# docker/frontend/app/app.py

from flask import Flask, render_template, request, jsonify
import requests
import os
import logging
import time # Required for latency metrics

# Import Prometheus client libraries
from prometheus_client import generate_latest, Counter, Histogram, make_wsgi_app
from werkzeug.middleware.dispatcher import DispatcherMiddleware # Used to add the /metrics endpoint

app = Flask(
    __name__,
    template_folder='website',
    static_folder='website',
    static_url_path='/website'
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Prometheus Metrics Definitions for Frontend ---
# Counter: Total requests to frontend endpoints
FRONTEND_REQUEST_COUNT = Counter(
    'whisper_frontend_requests_total',
    'Total number of requests to the frontend.',
    ['endpoint', 'http_status_code']
)
# Histogram: Latency of requests to frontend endpoints
FRONTEND_REQUEST_LATENCY = Histogram(
    'whisper_frontend_request_latency_seconds',
    'Request latency for frontend endpoints.',
    ['endpoint']
)
# Counter: Total API calls made by frontend to backend
BACKEND_API_CALL_COUNT = Counter(
    'whisper_frontend_backend_api_calls_total',
    'Total number of API calls made by frontend to backend.',
    ['backend_endpoint', 'http_status_code']
)
# Histogram: Latency of API calls made by frontend to backend
BACKEND_API_CALL_LATENCY = Histogram(
    'whisper_frontend_backend_api_call_latency_seconds',
    'Latency of backend API calls from frontend.',
    ['backend_endpoint']
)
# --- End Prometheus Metrics Definitions ---


# Get backend URL from environment variable, fallback for local development
# IMPORTANT: In Kubernetes, this should be the service name: 'http://whisper-backend-service:8000/'
BACKEND_URL = os.environ.get('BACKEND_URL', 'http://whisper-backend-service:8000/')
logger.info(f"Frontend configured to use backend at: {BACKEND_URL}")


@app.route('/app')
def index():
    start_time = time.time()
    endpoint_label = '/' # Even if route is /app, typically root is considered for index
    http_status_code = 200
    try:
        response = render_template('index.html')
        return response
    except Exception as e:
        logger.error(f"Error serving index page: {e}", exc_info=True)
        http_status_code = 500
        return jsonify({'error': 'Failed to load frontend'}), 500
    finally:
        FRONTEND_REQUEST_COUNT.labels(endpoint=endpoint_label, http_status_code=http_status_code).inc()
        FRONTEND_REQUEST_LATENCY.labels(endpoint=endpoint_label).observe(time.time() - start_time)

@app.route('/detect_language', methods=['POST'])
def detect_language():
    start_time_total = time.time()
    frontend_endpoint_label = '/detect_language'
    http_status_code_frontend = 500 # Default for frontend's response

    try:
        if 'audio' not in request.files:
            logger.error("Detect Language: No audio file in request.")
            http_status_code_frontend = 400
            return jsonify({'error': 'No audio file'}), 400

        audio_file = request.files['audio']
        logger.info(f"Detect Language: Received audio file {audio_file.filename}")

        backend_api_label = '/detect' # Label for backend endpoint being called
        start_time_backend_call = time.time()
        http_status_code_backend = 500 # Default for backend's response

        response = requests.post(
            f'{BACKEND_URL}/detect',
            files={'audio': (audio_file.filename, audio_file.stream, audio_file.content_type)}
        )
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        http_status_code_backend = response.status_code
        http_status_code_frontend = response.status_code # Frontend's status matches backend's success/failure
        result = response.json()
        logger.info(f"Detect Language: Backend response {response.status_code}")
        return jsonify(result)
    except requests.exceptions.RequestException as e:
        logger.error(f"Detect Language: Backend communication error: {str(e)}", exc_info=True)
        http_status_code_frontend = 500 # Always 500 for frontend if backend call fails
        return jsonify({'error': f"Backend communication error: {e}"}), 500
    except Exception as e:
        logger.error(f"Detect Language: Unexpected error in frontend proxy: {str(e)}", exc_info=True)
        http_status_code_frontend = 500
        return jsonify({'error': f"Language detection failed in frontend proxy: {str(e)}"}), 500
    finally:
        # Record metrics for backend API call (from frontend perspective)
        BACKEND_API_CALL_COUNT.labels(backend_endpoint=backend_api_label, http_status_code=http_status_code_backend).inc()
        BACKEND_API_CALL_LATENCY.labels(backend_endpoint=backend_api_label).observe(time.time() - start_time_backend_call)
        # Record metrics for the overall frontend request
        FRONTEND_REQUEST_COUNT.labels(endpoint=frontend_endpoint_label, http_status_code=http_status_code_frontend).inc()
        FRONTEND_REQUEST_LATENCY.labels(endpoint=frontend_endpoint_label).observe(time.time() - start_time_total)


@app.route('/transcribe', methods=['POST'])
def transcribe():
    start_time_total = time.time()
    frontend_endpoint_label = '/transcribe'
    http_status_code_frontend = 500 # Default for frontend's response

    try:
        if 'audio' not in request.files:
            logger.error("Transcribe: No audio file in request.")
            http_status_code_frontend = 400
            return jsonify({'error': 'No audio file provided for transcription'}), 400

        audio_file_storage = request.files['audio']
        language = request.form.get('language')

        if not language:
            logger.error("Transcribe: Language not provided in form data.")
            http_status_code_frontend = 400
            return jsonify({'error': 'Language not provided for transcription'}), 400

        logger.info(f"Transcribe: Received audio file {audio_file_storage.filename} for language {language}")

        files_to_send = {'audio': (audio_file_storage.filename, audio_file_storage.stream, audio_file_storage.content_type)}
        data_to_send = {'language': language} if language else {}

        backend_api_label = '/transcribe'
        start_time_backend_call = time.time()
        http_status_code_backend = 500

        response = requests.post(
            f'{BACKEND_URL}/transcribe',
            files=files_to_send,
            data=data_to_send
        )

        response.raise_for_status()
        http_status_code_backend = response.status_code
        http_status_code_frontend = response.status_code
        result = response.json()
        logger.info(f"Transcribe: Backend response {response.status_code}")
        return jsonify(result)
    except requests.exceptions.RequestException as e:
        logger.error(f"Transcribe: Backend communication error during transcription: {str(e)}", exc_info=True)
        http_status_code_frontend = 500
        return jsonify({'error': f"Backend communication error during transcription: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Transcribe: Unexpected error in frontend proxy: {str(e)}", exc_info=True)
        http_status_code_frontend = 500
        return jsonify({'error': f"Transcription failed in frontend proxy: {str(e)}"}), 500
    finally:
        # Record metrics for backend API call (from frontend perspective)
        BACKEND_API_CALL_COUNT.labels(backend_endpoint=backend_api_label, http_status_code=http_status_code_backend).inc()
        BACKEND_API_CALL_LATENCY.labels(backend_endpoint=backend_api_label).observe(time.time() - start_time_backend_call)
        # Record metrics for the overall frontend request
        FRONTEND_REQUEST_COUNT.labels(endpoint=frontend_endpoint_label, http_status_code=http_status_code_frontend).inc()
        FRONTEND_REQUEST_LATENCY.labels(endpoint=frontend_endpoint_label).observe(time.time() - start_time_total)


# Add a /metrics endpoint that Prometheus can scrape
# This will expose your defined metrics (counters, gauges, histograms)
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app()
})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)