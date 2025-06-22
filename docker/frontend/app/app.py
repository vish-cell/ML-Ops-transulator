from flask import Flask, render_template, request, jsonify
import requests
import os
import logging

app = Flask(
    __name__,
    template_folder='website',
    static_folder='website',
    static_url_path='/website'
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BACKEND_URL = os.environ.get('BACKEND_URL', 'http://whisper:8000/')

@app.route('/app')
def index():
    return render_template('index.html')

@app.route('/detect_language', methods=['POST'])
def detect_language():
    if 'audio' not in request.files:
        logger.error("Detect Language: No audio file in request.")
        return jsonify({'error': 'No audio file'}), 400
    
    audio_file = request.files['audio']
    logger.info(f"Detect Language: Received audio file {audio_file.filename}")
    try:
        response = requests.post(
            f'{BACKEND_URL}/detect',
            files={'audio': (audio_file.filename, audio_file.stream, audio_file.content_type)}
        )
        response.raise_for_status()
        logger.info(f"Detect Language: Backend response {response.status_code}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Detect Language: Backend communication error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Detect Language: Unexpected error in frontend proxy: {str(e)}")
        return jsonify({'error': f"Language detection failed in frontend proxy: {str(e)}"}), 500

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'audio' not in request.files:
        logger.error("Transcribe: No audio file in request.")
        return jsonify({'error': 'No audio file provided for transcription'}), 400
    
    try:
        audio_file_storage = request.files['audio']
        language = request.form.get('language')
        
        if not language:
            logger.error("Transcribe: Language not provided in form data.")
            return jsonify({'error': 'Language not provided for transcription'}), 400

        logger.info(f"Transcribe: Received audio file {audio_file_storage.filename} for language {language}")

        files_to_send = {'audio': (audio_file_storage.filename, audio_file_storage.stream, audio_file_storage.content_type)}
        data_to_send = {'language': language} if language else {}

        response = requests.post(
            f'{BACKEND_URL}/transcribe',
            files=files_to_send,
            data=data_to_send
        )
        
        response.raise_for_status()
        logger.info(f"Transcribe: Backend response {response.status_code}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Transcribe: Backend communication error during transcription: {str(e)}")
        return jsonify({'error': f"Backend communication error during transcription: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Transcribe: Unexpected error in frontend proxy: {str(e)}")
        return jsonify({'error': f"Transcription failed in frontend proxy: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)