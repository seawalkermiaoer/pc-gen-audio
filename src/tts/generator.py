#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import shutil
import sys
import logging
from openai import OpenAI
from src.config.constants import (
    OPENAI_BASE_URL, OPENAI_API_KEY, OPENAI_MODEL, OPENAI_VOICE,
    TMP_DIR, RES_DIR
)
from src.audio.utils import get_audio_duration

logger = logging.getLogger(__name__)

def step1_generate_audio(input_file, base_name):
    """
    Step 1: Generate WAV files for each English sentence and create step1.json

    - Read input_file (English-Chinese sentence pairs)
    - Generate audio using OpenAI TTS
    - Calculate duration of each audio file
    - Save to res/{base_name}.step1.json
    """
    logger.info("="*70)
    logger.info("STEP 1: Generating Audio from Text")
    logger.info("="*70)

    # Create directories
    os.makedirs(TMP_DIR, exist_ok=True)
    os.makedirs(RES_DIR, exist_ok=True)

    logger.info(f"Created directory: {TMP_DIR}")
    logger.info(f"Created directory: {RES_DIR}")

    # Initialize OpenAI client
    client = OpenAI(
        base_url=OPENAI_BASE_URL,
        api_key=OPENAI_API_KEY
    )
    logger.info(f"OpenAI client initialized: {OPENAI_BASE_URL} ({OPENAI_MODEL})")

    # Read input JSON file
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)

    logger.info(f"Reading input file: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        sentences = json.load(f)

    logger.info(f"Loaded {len(sentences)} sentences")
    logger.info("")

    # Generate WAV files for each English sentence
    durations = []
    for i, sentence_data in enumerate(sentences):
        english_text = sentence_data['english']
        chinese_text = sentence_data['chinese']
        wav_filename = os.path.join(TMP_DIR, f"sentence_{i}.wav")

        logger.info(f"[{i+1}/{len(sentences)}] Generating audio for: {english_text[:50]}...")

        # Generate audio using OpenAI
        with client.audio.speech.with_streaming_response.create(
            model=OPENAI_MODEL,
            voice=OPENAI_VOICE,
            input=english_text
        ) as response:
            response.stream_to_file(wav_filename)

        # Get duration
        duration = get_audio_duration(wav_filename)
        durations.append(duration)

        logger.info(f"  Saved: {wav_filename} (Duration: {duration:.3f}s)")
        logger.info(f"  Chinese: {chinese_text}")
        logger.info("")

    # Create step1.json
    result = []
    for i, sentence_data in enumerate(sentences):
        result.append({
            "english": sentence_data['english'],
            "chinese": sentence_data['chinese'],
            "duration": durations[i]
        })

    step1_json = os.path.join(RES_DIR, f'{base_name}.step1.json')
    with open(step1_json, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    logger.info(f"Step 1 completed. Result saved to: {step1_json}")
    logger.info("")
    return step1_json
