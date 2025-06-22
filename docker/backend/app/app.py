from flask import Flask, request, jsonify
import whisper
import torch
import os
from datetime import datetime
import logging

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/tmp'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

model = None

try:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Loading Whisper model on {device}")
    model = whisper.load_model("base", device=device)
    logger.info("Model loaded successfully")
except Exception as e:
    logger.error(f"Failed to load model: {e}")
    raise

@app.route('/detect', methods=['POST'])
def detect():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file'}), 400
    
    try:
        audio_file = request.files['audio']
        filename = f"audio_{datetime.now().timestamp()}.wav"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        audio_file.save(filepath)
        
        audio = whisper.load_audio(filepath)
        audio = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(audio).to(model.device)
        
        _, probs = model.detect_language(mel)
        language = max(probs, key=probs.get)
        logger.info(f"Detected language: {language}")
        
        return jsonify({
            'status': 'success',
            'language': language,
            'filepath': filepath
        })
    except Exception as e:
        logger.error(f"Detection error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided for transcription'}), 400
    
    try:
        audio_file = request.files['audio']
        language = request.form.get('language')
        
        if not language:
            return jsonify({'error': 'Language not provided for transcription'}), 400

        filename = f"transcribe_audio_{datetime.now().timestamp()}.wav"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        audio_file.save(filepath)
        
        logger.info(f"Transcribing {filepath} in {language}")
        result = model.transcribe(filepath, language=language)
        os.remove(filepath)
        
        return jsonify({
            'status': 'success',
            'text': result['text']
        })
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)