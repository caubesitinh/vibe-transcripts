#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = ["openai"]
# ///

import sys
import os
from openai import OpenAI

def summarize_transcript(transcript_file, speaker_name):
    """
    Summarize a transcript using LM Studio with Phi-4 model
    
    Args:
        transcript_file: Path to the transcript file
        speaker_name: Name of the speaker
    """
    
    # Read transcript
    if not os.path.exists(transcript_file):
        print(f"Error: Transcript file '{transcript_file}' not found")
        sys.exit(1)
    
    try:
        with open(transcript_file, 'r', encoding='utf-8') as f:
            transcript = f.read().strip()
    except Exception as e:
        print(f"Error reading transcript file: {e}")
        sys.exit(1)
    
    if not transcript:
        print("Error: Transcript file is empty")
        sys.exit(1)
    
    # Initialize OpenAI client for LM Studio
    client = OpenAI(
        base_url="http://localhost:1234/v1",
        api_key="lm-studio"  # LM Studio doesn't require a real API key
    )
    
    # Create prompt
    prompt = f"You are writing a summary of the given video transcript. The speaker is {speaker_name}. Keep it to around 150 words.\n\nTranscript:\n{transcript}"
    
    try:
        # Make request to LM Studio
        response = client.chat.completions.create(
            model="microsoft/phi-4",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            temperature=0.7
        )
        
        summary = response.choices[0].message.content.strip()
        print(summary)
        
    except Exception as e:
        print(f"Error generating summary: {e}")
        print("Make sure LM Studio is running on port 1234 with the microsoft/phi-4 model loaded")
        sys.exit(1)

def main():
    if len(sys.argv) != 3:
        print("Usage: uv run summarize.py <transcript_file> <speaker_name>")
        print("  transcript_file: Path to the transcript file (.txt)")
        print("  speaker_name: Name of the speaker")
        print("")
        print("Example:")
        print("  uv run summarize.py transcript.txt 'John Doe'")
        sys.exit(1)
    
    transcript_file = sys.argv[1]
    speaker_name = sys.argv[2]
    
    summarize_transcript(transcript_file, speaker_name)

if __name__ == "__main__":
    main()