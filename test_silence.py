#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import os

def get_audio_duration(file_path):
    """Get duration of an audio file in seconds using ffprobe"""
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1', file_path],
        capture_output=True, text=True, check=True
    )
    return float(result.stdout.strip())

def create_silence_file(duration, output_path):
    """Create a silence audio file with specified duration"""
    print(f"Creating silence file: {output_path} ({duration}s)")
    subprocess.run([
        'ffmpeg', '-y', '-f', 'lavfi', '-i', 'anullsrc=channel_layout=mono:sample_rate=22050',
        '-t', str(duration), '-c:a', 'pcm_s16le', output_path
    ], check=True, capture_output=True)
    print(f"Created silence file: {output_path}")

# Test the silence duration
if __name__ == "__main__":
    # Create tmp directory if it doesn't exist
    tmp_dir = "tmp"
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
    
    # Create a 700ms silence file in tmp directory
    silence_file = os.path.join(tmp_dir, "test_silence_700ms.wav")
    GAP_DURATION_SEC = 0.7  # 700ms
    
    create_silence_file(GAP_DURATION_SEC, silence_file)
    
    # Check the actual duration
    duration = get_audio_duration(silence_file)
    print(f"Actual duration: {duration:.3f}s ({duration*1000:.0f}ms)")
    
    # List files in tmp directory
    print(f"\nFiles in {tmp_dir} directory:")
    for file in os.listdir(tmp_dir):
        print(f"  {file}")
    
    # Don't clean up - keep files for user review
    print(f"\nFiles kept in {tmp_dir} directory for review")