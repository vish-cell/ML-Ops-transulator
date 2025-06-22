document.addEventListener('DOMContentLoaded', function() {
    const audioFileInput = document.getElementById('audioFile');
    const uploadBtn = document.getElementById('uploadBtn');
    const recordBtn = document.getElementById('recordBtn');
    const stopBtn = document.getElementById('stopBtn');
    const recordedAudio = document.getElementById('recordedAudio');
    const languageResult = document.getElementById('languageResult');
    const confirmBtn = document.getElementById('confirmBtn');
    const rejectBtn = document.getElementById('rejectBtn');
    const transcriptionText = document.getElementById('transcriptionText');
    
    const uploadSection = document.getElementById('uploadSection');
    const languageSection = document.getElementById('languageSection');
    const transcriptionResult = document.getElementById('transcriptionResult');
    
    let mediaRecorder;
    let audioChunks = [];
    let currentAudioFileBlob = null; // Store the blob for consistent processing

    // --- Event Listeners ---
    // Handle file upload
    uploadBtn.addEventListener('click', function() {
        if (audioFileInput.files.length === 0) {
            alert('Please select an audio file first');
            return;
        }
        currentAudioFileBlob = audioFileInput.files[0];
        processAudioForLanguageDetection(currentAudioFileBlob);
    });
    
    // Handle recording
    recordBtn.addEventListener('click', startRecording);
    stopBtn.addEventListener('click', stopRecording);
    
    confirmBtn.addEventListener('click', () => {
        // Use the stored audio file blob for transcription
        if (currentAudioFileBlob) {
            transcribeAudio(currentAudioFileBlob, languageResult.textContent);
        } else {
            alert('No audio to transcribe. Please upload or record.');
            resetUI();
        }
    });
    
    rejectBtn.addEventListener('click', resetUI);

    // --- Recording Functions ---
    function startRecording() {
        audioChunks = [];
        recordBtn.disabled = true;
        stopBtn.disabled = false;
        recordedAudio.src = '';
        
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                mediaRecorder = new MediaRecorder(stream);
                mediaRecorder.start();
                
                mediaRecorder.ondataavailable = function(e) {
                    audioChunks.push(e.data);
                };
                
                mediaRecorder.onstop = function() {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    const audioUrl = URL.createObjectURL(audioBlob);
                    recordedAudio.src = audioUrl;
                    
                    currentAudioFileBlob = audioBlob; // Store the recorded audio blob
                    processAudioForLanguageDetection(currentAudioFileBlob);

                    // Stop microphone stream tracks
                    stream.getTracks().forEach(track => track.stop());
                };
            })
            .catch(err => {
                console.error('Error accessing microphone:', err);
                alert('Error accessing microphone. Please check permissions.');
                recordBtn.disabled = false;
                stopBtn.disabled = true;
            });
    }
    
    function stopRecording() {
        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stop();
            recordBtn.disabled = false;
            stopBtn.disabled = true;
        }
    }
    
    // --- Audio Processing Functions ---
    async function processAudioForLanguageDetection(audioBlob) {
        uploadSection.classList.add('hidden');
        languageSection.classList.remove('hidden');
        transcriptionResult.classList.add('hidden');
        languageResult.textContent = 'Detecting...';
        
        const formData = new FormData();
        formData.append('audio', audioBlob, 'audio.wav'); // Use 'audio.wav' as filename for consistency
        
        try {
            // Step 1: Detect language
            const langResponse = await fetch('/detect_language', {
                method: 'POST',
                body: formData
            });
            
            if (!langResponse.ok) {
                const errorData = await langResponse.json().catch(() => ({error: 'Unknown error'}));
                throw new Error(`Language detection failed: ${errorData.error || langResponse.statusText}`);
            }
            
            const langData = await langResponse.json();
            languageResult.textContent = langData.language_name || langData.language || 'Unknown Language';
            // We don't need to pass the filepath back to frontend, as we use the blob directly now.
            // Backend will handle temporary file management.
            
        } catch (error) {
            console.error('Error during language detection:', error);
            languageResult.textContent = 'Detection failed';
            alert('Error detecting language: ' + error.message);
            resetUI();
        }
    }
    
    async function transcribeAudio(audioBlob, detectedLanguage) {
        languageSection.classList.add('hidden');
        transcriptionResult.classList.remove('hidden');
        transcriptionText.textContent = 'Transcribing...';
        
        const formData = new FormData();
        formData.append('audio', audioBlob, 'audio.wav'); // Send audio blob again
        // Optionally send language as a separate field if backend needs it and can't re-detect
        formData.append('language', detectedLanguage); 
        
        try {
            const transcribeResponse = await fetch('/transcribe', {
                method: 'POST',
                body: formData // Send as FormData, not JSON.stringify
            });
            
            if (!transcribeResponse.ok) {
                const errorData = await transcribeResponse.json().catch(() => ({error: 'Unknown error'}));
                throw new Error(`Transcription failed: ${errorData.error || transcribeResponse.statusText}`);
            }
            
            const transcript = await transcribeResponse.json();
            transcriptionText.textContent = transcript.text;
        } catch (error) {
            console.error('Error during transcription:', error);
            transcriptionText.textContent = 'Error: ' + error.message;
        } finally {
            // Optionally, you might want a "Start New" button instead of immediate reset
            // For now, let's keep it simple and just show the result.
        }
    }

    function resetUI() {
        uploadSection.classList.remove('hidden');
        languageSection.classList.add('hidden');
        transcriptionResult.classList.add('hidden');
        audioFileInput.value = ''; // Clear file input
        recordedAudio.src = ''; // Clear recorded audio
        currentAudioFileBlob = null; // Clear stored blob
        languageResult.textContent = '';
        transcriptionText.textContent = '';
    }
});