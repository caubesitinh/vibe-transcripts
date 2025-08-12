# Video/Audio Transcription App

A small video transcription app that was built on a recording for Microsoft
with Claude.

## Prerequisites

1. **Python 3.8+** with `uv` package manager installed
2. **FFmpeg** for audio extraction from video files:
   ```bash
   brew install ffmpeg  # macOS
   # or apt install ffmpeg  # Ubuntu/Debian
   ```
3. **LM Studio** running locally on port 1234 with microsoft/phi-4 model (for summarization)

## Setup

1. **Build whisper.cpp and download the model**:
   ```bash
   make build-whisper
   ```

2. **Start the development server** (web interface):
   ```bash
   make dev
   ```

3. **Check server logs** if needed:
   ```bash
   make tail-log
   ```

## License

This project uses whisper.cpp (MIT License) for transcription capabilities.

It's entirely AI generated and thus most likely in the public domain.  If
for whatever reason that is not the legal interpretation you can consider
it to be MIT licensed.
