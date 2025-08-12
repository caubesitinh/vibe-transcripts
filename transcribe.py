#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///

import subprocess
import sys
import os
from pathlib import Path

def transcribe_video(input_file, output_format="txt", model_path=None):
    """
    Transcribe video/audio file using whisper.cpp
    
    Args:
        input_file: Path to input audio/video file
        output_format: Output format (txt, srt, vtt, json)
        model_path: Path to whisper model (optional)
    """
    
    # Get absolute path to whisper-cli
    script_dir = Path(__file__).parent
    whisper_cli = script_dir / "whisper.cpp" / "build" / "bin" / "whisper-cli"
    
    if not whisper_cli.exists():
        print(f"Error: whisper-cli not found at {whisper_cli}")
        print("Please ensure whisper.cpp is compiled in the whisper.cpp directory")
        sys.exit(1)
    
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
    
    # Add model path if specified
    if model_path:
        cmd.extend(["-m", model_path])
    
    # Add input file
    cmd.append(input_file)
    
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