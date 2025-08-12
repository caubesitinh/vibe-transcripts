#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

import subprocess
import sys
import os
import tempfile
from pathlib import Path

def extract_audio_if_needed(input_file):
    """
    Extract audio from video file if needed, return path to audio file.
    If input is already audio, return original path.
    """
    input_path = Path(input_file)
    supported_audio_formats = {'.wav', '.mp3', '.flac', '.ogg'}
    
    if input_path.suffix.lower() in supported_audio_formats:
        return input_file
    
    # Check if ffmpeg is available
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: ffmpeg is required to extract audio from video files")
        print("Please install ffmpeg: brew install ffmpeg")
        sys.exit(1)
    
    # Create temporary audio file
    temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    temp_audio.close()
    
    print(f"Extracting audio from {input_file} to temporary file...")
    
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
        print(f"Audio extracted successfully")
        return temp_audio.name
    except subprocess.CalledProcessError as e:
        os.unlink(temp_audio.name)  # cleanup temp file
        print(f"Error extracting audio: {e}")
        if e.stderr:
            print("FFmpeg error:", e.stderr.decode())
        sys.exit(1)

def transcribe_video(input_file, output_format="txt", model_path=None):
    """
    Transcribe video/audio file using whisper.cpp
    
    Args:
        input_file: Path to input audio/video file
        output_format: Output format (txt, srt, vtt, json)
        model_path: Path to whisper model (optional, defaults to large-v3-turbo)
    """
    
    # Get absolute path to whisper-cli
    script_dir = Path(__file__).parent
    whisper_cli = script_dir / "whisper.cpp" / "build" / "bin" / "whisper-cli"
    
    if not whisper_cli.exists():
        print(f"Error: whisper-cli not found at {whisper_cli}")
        print("Please ensure whisper.cpp is compiled in the whisper.cpp directory")
        sys.exit(1)
    
    # Set default model to large-v3-turbo if not specified
    if not model_path:
        model_path = str(script_dir / "whisper.cpp" / "models" / "ggml-large-v3-turbo.bin")
        if not Path(model_path).exists():
            print(f"Error: Default model not found at {model_path}")
            print("Please download the model using: cd whisper.cpp && bash ./models/download-ggml-model.sh large-v3-turbo")
            sys.exit(1)
    
    # Extract audio if needed
    audio_file = extract_audio_if_needed(input_file)
    temp_file_created = audio_file != input_file
    
    try:
        # Build command
        cmd = [str(whisper_cli)]
        
        # Add output format flag
        format_flags = {
            "txt": "--output-txt",
            "srt": "--output-srt", 
            "vtt": "--output-vtt",
            "json": "--output-json"
        }
        
        if output_format in format_flags:
            cmd.append(format_flags[output_format])
        else:
            print(f"Warning: Unknown format '{output_format}', defaulting to txt")
            cmd.append("--output-txt")
        
        # Add model path
        cmd.extend(["-m", model_path])
        
        # Set output file path next to original input file with same name but .txt extension
        input_path = Path(input_file)
        output_file_path = input_path.parent / input_path.stem
        cmd.extend(["-of", str(output_file_path)])
        
        # Add audio file
        cmd.append(audio_file)
        
        print(f"Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print("Transcription completed successfully!")
            if result.stdout:
                print("Output:", result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error running whisper-cli: {e}")
            if e.stderr:
                print("Error details:", e.stderr)
            return False
    finally:
        # Always clean up temp file if we created one
        if temp_file_created and os.path.exists(audio_file):
            try:
                os.unlink(audio_file)
            except Exception:
                pass

def main():
    if len(sys.argv) < 2:
        print("Usage: uv run transcribe.py <input_file> [output_format] [model_path]")
        print("  input_file: Path to audio/video file")
        print("  output_format: txt, srt, vtt, or json (default: txt)")
        print("  model_path: Path to whisper model file (optional)")
        print("")
        print("Examples:")
        print("  uv run transcribe.py audio.wav")
        print("  uv run transcribe.py video.mp4 srt")
        print("  uv run transcribe.py audio.mp3 json /path/to/model.bin")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_format = sys.argv[2] if len(sys.argv) > 2 else "txt"
    model_path = sys.argv[3] if len(sys.argv) > 3 else None
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    
    transcribe_video(input_file, output_format, model_path)

if __name__ == "__main__":
    main()