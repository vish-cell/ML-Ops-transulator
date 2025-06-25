# docker/backend/app/app.py

from flask import Flask, request, jsonify
import whisper
import torch
import os
from datetime import datetime
import logging
import time # Import time for metrics calculations

# Import Prometheus client libraries
from prometheus_client import generate_latest, Counter, Gauge, Histogram, make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware # Used to add the /metrics endpoint

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

model = None

# --- Prometheus Metrics Definitions for Backend ---
# Counter: Increments every time a request is made to an endpoint
# Labels allow you to slice and dice the metric data (e.g., requests by endpoint or status code)
REQUEST_COUNT = Counter(
    'whisper_backend_requests_total',
    'Total number of requests to the backend.',
    ['endpoint', 'http_status_code']
)
# Histogram: Measures request durations and categorizes them into configurable buckets
# Provides insights into latency distribution (e.g., how many requests took <0.5s, <1s, etc.)
REQUEST_LATENCY = Histogram(
    'whisper_backend_request_latency_seconds',
    'Request latency for backend endpoints.',
    ['endpoint']
)
# Gauge: Represents a single numerical value that can go up or down
# Useful for current states, like resource usage or a boolean status (0/1)
WHISPER_MODEL_LOAD_STATUS = Gauge(
    'whisper_model_load_status',
    'Status of Whisper model loading (1=success, 0=failure)'
)
# Histogram: Measures the size of uploaded audio files.
# Helps understand the distribution of input data sizes.
AUDIO_FILE_SIZE_BYTES = Histogram(
    'whisper_backend_audio_file_size_bytes',
    'Size of uploaded audio files in bytes.',
    buckets=[1024, 5120, 10240, 51200, 102400, 512000, 1048576, 5242880, 10485760, float('inf')] # Example buckets: 1KB, 5KB, 10KB, 50KB, 100KB, 500KB, 1MB, 5MB, 10MB, +Inf
)
# --- End Prometheus Metrics Definitions ---

# Use an environment variable to determine model size, fallback to "small" if not set
# This allows for easy configuration via Kubernetes Deployment YAML
WHISPER_MODEL_SIZE = os.environ.get("WHISPER_MODEL_SIZE", "base")

try:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Loading Whisper model '{WHISPER_MODEL_SIZE}' on {device}")
    model = whisper.load_model(WHISPER_MODEL_SIZE, device=device)
    logger.info("Model loaded successfully")
    WHISPER_MODEL_LOAD_STATUS.set(1) # Set gauge to 1 on successful model load
except Exception as e:
    logger.error(f"Failed to load model: {e}")
    WHISPER_MODEL_LOAD_STATUS.set(0) # Set gauge to 0 on model load failure
    raise # Re-raise the exception to indicate a critical startup failure

@app.route('/health', methods=['GET'])
def health():
    """
    Simple health check endpoint for Kubernetes liveness/readiness probes.
    Returns 200 OK if the application is running.
    """
    return jsonify({'status': 'healthy'}), 200

@app.route('/detect', methods=['POST'])
def detect():
    start_time = time.time()
    endpoint_label = '/detect'
    http_status_code = 500 # Default status code in case of an unhandled error

    try:
        if 'audio' not in request.files:
            http_status_code = 400
            return jsonify({'error': 'No audio file'}), 400
        
        audio_file = request.files['audio']
        filename = f"audio_{datetime.now().timestamp()}.wav"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        audio_file.save(filepath)
        
        # Record the size of the uploaded audio file
        AUDIO_FILE_SIZE_BYTES.observe(os.path.getsize(filepath))
        
        audio = whisper.load_audio(filepath)
        audio = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(audio).to(model.device)
        
        _, probs = model.detect_language(mel)
        language = max(probs, key=probs.get)
        logger.info(f"Detected language: {language}")
        
        os.remove(filepath) # Clean up the temporary file
        
        http_status_code = 200 # Set status to 200 on success
        return jsonify({
            'status': 'success',
            'language': language
            # Removed 'filepath': filepath as it's a temporary internal detail
        })
    except Exception as e:
        logger.error(f"Detection error: {e}", exc_info=True) # Log full traceback
        return jsonify({'error': str(e)}), http_status_code # Returns the default 500 or specific error
    finally:
        # Ensure metrics are always recorded, even if an error occurs
        REQUEST_COUNT.labels(endpoint=endpoint_label, http_status_code=http_status_code).inc()
        REQUEST_LATENCY.labels(endpoint=endpoint_label).observe(time.time() - start_time)

@app.route('/transcribe', methods=['POST'])
def transcribe():
    start_time = time.time()
    endpoint_label = '/transcribe'
    http_status_code = 500 # Default status code in case of an unhandled error

    try:
        if 'audio' not in request.files:
            http_status_code = 400
            return jsonify({'error': 'No audio file provided for transcription'}), 400
        
        audio_file = request.files['audio']
        language = request.form.get('language')
        
        if not language:
            http_status_code = 400
            return jsonify({'error': 'Language not provided for transcription'}), 400

        filename = f"transcribe_audio_{datetime.now().timestamp()}.wav"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        audio_file.save(filepath)
        
        # Record the size of the uploaded audio file
        AUDIO_FILE_SIZE_BYTES.observe(os.path.getsize(filepath))

        logger.info(f"Transcribing {filepath} in {language}")
        result = model.transcribe(filepath, language=language)
        os.remove(filepath) # Clean up the temporary file
        
        http_status_code = 200 # Set status to 200 on success
        return jsonify({
            'status': 'success',
            'text': result['text']
        })
    except Exception as e:
        logger.error(f"Transcription error: {e}", exc_info=True) # Log full traceback
        return jsonify({'error': str(e)}), http_status_code # Returns the default 500 or specific error
    finally:
        # Ensure metrics are always recorded, even if an error occurs
        REQUEST_COUNT.labels(endpoint=endpoint_label, http_status_code=http_status_code).inc()
        REQUEST_LATENCY.labels(endpoint=endpoint_label).observe(time.time() - start_time)

# Add a /metrics endpoint that Prometheus can scrape
# This will expose your defined metrics (counters, gauges, histograms)
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app()
})

if __name__ == '__main__':
    # When run directly, this uses Flask's development server.
    # In a production Kubernetes environment, you would typically use a WSGI server
    # like Gunicorn to run the Flask application.
    app.run(host='0.0.0.0', port=8000)