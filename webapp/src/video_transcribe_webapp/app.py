from flask import Flask, render_template, request, jsonify
import os
import subprocess
import tempfile
import json
from pathlib import Path
from openai import OpenAI

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024 * 1024  # 4GB max file size

# Allowed video file extensions
ALLOWED_EXTENSIONS = {
    'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm', 'm4v', '3gp'
}

# Audio formats that don't need extraction
AUDIO_EXTENSIONS = {'wav', 'mp3', 'flac', 'ogg'}

def allowed_file(filename):
    if not '.' in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS or ext in AUDIO_EXTENSIONS

def extract_audio_if_needed(input_file):
    """
    Extract audio from video file if needed, return path to audio file.
    If input is already audio, return original path.
    """
    input_path = Path(input_file)
    
    if input_path.suffix.lower() in {'.wav', '.mp3', '.flac', '.ogg'}:
        return input_file
    
    # Check if ffmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        raise Exception("ffmpeg is required to extract audio from video files")
    
    # Create temporary audio file
    temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    temp_audio.close()
    
    # Extract audio using ffmpeg
    ffmpeg_cmd = [
        'ffmpeg', '-i', input_file, 
        '-vn',  # no video
        '-acodec', 'pcm_s16le',  # 16-bit PCM
        '-ar', '16000',  # 16kHz sample rate (whisper's preferred)
        '-ac', '1',  # mono
        '-y',  # overwrite output file
        temp_audio.name
    ]
    
    try:
        subprocess.run(ffmpeg_cmd, capture_output=True, check=True)
        return temp_audio.name
    except subprocess.CalledProcessError as e:
        os.unlink(temp_audio.name)  # cleanup temp file
        raise Exception(f"Error extracting audio: {e}")

def transcribe_audio_to_json(audio_file):
    """
    Transcribe audio file using whisper.cpp and return JSON with timestamps
    """
    # Get absolute path to whisper-cli
    script_dir = Path(__file__).parent.parent.parent.parent  # Go up to project root
    whisper_cli = script_dir / "whisper.cpp" / "build" / "bin" / "whisper-cli"
    
    if not whisper_cli.exists():
        raise Exception(f"whisper-cli not found at {whisper_cli}")
    
    # Set model path
    model_path = str(script_dir / "whisper.cpp" / "models" / "ggml-large-v3-turbo.bin")
    if not Path(model_path).exists():
        raise Exception(f"Model not found at {model_path}")
    
    # Create temp file for JSON output
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_json:
        temp_json_path = temp_json.name
    
    try:
        # Build command for JSON output
        cmd = [
            str(whisper_cli),
            '--output-json',
            '-m', model_path,
            '-of', temp_json_path.replace('.json', ''),  # whisper-cli adds .json
            audio_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Read the JSON output
        with open(temp_json_path, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)
        
        # Debug: print the structure to understand the format
        print("DEBUG: Transcript data structure:", json.dumps(transcript_data, indent=2)[:500])
        
        return transcript_data
    
    finally:
        # Cleanup temp file
        if os.path.exists(temp_json_path):
            os.unlink(temp_json_path)

def summarize_transcript_text(transcript_text, speaker_name):
    """
    Summarize transcript text using LM Studio with Phi-4 model
    """
    try:
        # Initialize OpenAI client for LM Studio
        client = OpenAI(
            base_url="http://localhost:1234/v1",
            api_key="lm-studio"  # LM Studio doesn't require a real API key
        )
        
        # Create prompt
        prompt = f"You are writing a summary of the given video transcript. The speaker is {speaker_name}. Keep it to around 150 words.\n\nTranscript:\n{transcript_text}"
        
        # Make request to LM Studio
        response = client.chat.completions.create(
            model="microsoft/phi-4",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        raise Exception(f"Error generating summary: {e}. Make sure LM Studio is running on port 1234 with the microsoft/phi-4 model loaded")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    speaker_name = request.form.get('speaker_name', 'Unknown Speaker')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only video and audio files are allowed.'}), 400
    
    # Save uploaded file temporarily
    temp_video = tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix)
    file.save(temp_video.name)
    temp_video.close()
    
    temp_audio = None
    
    try:
        # Extract audio if needed
        temp_audio = extract_audio_if_needed(temp_video.name)
        
        # Transcribe to JSON
        transcript_data = transcribe_audio_to_json(temp_audio)
        
        # Extract plain text for summarization - handle different JSON structures
        transcript_segments = transcript_data.get('transcription', [])
        if not transcript_segments:
            # Try alternative key names
            transcript_segments = transcript_data.get('segments', [])
            if not transcript_segments:
                transcript_segments = transcript_data.get('results', [])
        
        transcript_text = '\n'.join([segment.get('text', '') for segment in transcript_segments])
        
        # Generate summary
        summary = summarize_transcript_text(transcript_text, speaker_name)
        
        return jsonify({
            'success': True,
            'message': f'Video file "{file.filename}" processed successfully',
            'transcript': transcript_data,
            'summary': summary,
            'speaker_name': speaker_name
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        # Clean up temp files
        try:
            if os.path.exists(temp_video.name):
                os.unlink(temp_video.name)
            if temp_audio and temp_audio != temp_video.name and os.path.exists(temp_audio):
                os.unlink(temp_audio)
        except Exception:
            pass

if __name__ == '__main__':
    app.run(debug=True)