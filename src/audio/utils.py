#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import logging

logger = logging.getLogger(__name__)

def get_audio_duration(file_path):
    """Get duration of an audio file in seconds using ffprobe"""
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1', file_path],
        capture_output=True, text=True, check=True
    )
    return float(result.stdout.strip())

def sec_to_hhmmss_ms(s):
    """Convert seconds to HH:MM:SS.mmm format with millisecond precision"""
    s = int(s * 1000)  # Convert to milliseconds
    ms = s % 1000
    s //= 1000
    sec = s % 60
    s //= 60
    min = s % 60
    s //= 60
    hour = s
    return f"{hour:02d}:{min:02d}:{sec:02d}.{ms:03d}"

def create_silence_file(duration, output_path):
    """Create a silence audio file with specified duration"""
    logger.info(f"Creating silence file: {output_path} ({duration}s)")
    subprocess.run([
        'ffmpeg', '-y', '-f', 'lavfi', '-i', 'anullsrc=channel_layout=mono:sample_rate=22050',
        '-t', str(duration), '-c:a', 'pcm_s16le', output_path
    ], check=True, capture_output=True)
    logger.info(f"Created silence file: {output_path}")

def normalize_audio(input_path, output_path):
    """Normalize audio to standard format (PCM 16-bit, 22050 Hz, mono)"""
    logger.debug(f"Normalizing audio: {input_path} -> {output_path}")
    subprocess.run([
        'ffmpeg', '-y', '-i', input_path,
        '-acodec', 'pcm_s16le', '-ar', '22050', '-ac', '1',
        output_path
    ], check=True, capture_output=True)
