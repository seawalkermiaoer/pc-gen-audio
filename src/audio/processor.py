#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import subprocess
import sys
import logging
from src.config.constants import (
    INITIAL_SILENCE_SEC, GAP_DURATION_SEC, GAP_BUFFER_SEC, DISPLAY_BUFFER_SEC,
    TMP_DIR, RES_DIR
)
from src.audio.utils import (
    sec_to_hhmmss_ms, create_silence_file, normalize_audio
)

logger = logging.getLogger(__name__)

def step2_merge_audio(base_name):
    """
    Step 2: Calculate precise timestamps and merge audio files

    - Read res/{base_name}.step1.json
    - Add 300ms initial silence and 700ms gaps between sentences
    - Normalize and merge all audio files
    - Convert to MP3 format
    - Generate res/{base_name}.step2.json and res/{base_name}.md
    """
    logger.info("="*70)
    logger.info("STEP 2: Merging Audio and Generating Timestamps")
    logger.info("="*70)

    # Input from Step 1
    step1_json = os.path.join(RES_DIR, f'{base_name}.step1.json')
    if not os.path.exists(step1_json):
        logger.error(f"{step1_json} not found. Please run step 1 first.")
        sys.exit(1)

    # Load step1.json
    logger.info(f"Loading {step1_json}")
    with open(step1_json, 'r', encoding='utf-8') as f:
        sentences = json.load(f)

    logger.info(f"Loaded {len(sentences)} sentences")
    logger.info("Configuration:")
    logger.info(f"  - Initial silence: {INITIAL_SILENCE_SEC*1000:.0f}ms")
    logger.info(f"  - Gap between sentences: {GAP_DURATION_SEC*1000:.0f}ms (±{GAP_BUFFER_SEC*1000:.0f}ms)")
    logger.info(f"  - Display buffer: ±{DISPLAY_BUFFER_SEC*1000:.0f}ms")
    logger.info(f"  - Timestamp format: HH:MM:SS.mmm (millisecond precision)")
    logger.info("")

    # Calculate timeline
    t = INITIAL_SILENCE_SEC
    timeline = []
    normalized_files = []

    logger.info("Processing sentences...")
    logger.info("-"*70)
    for i, sentence in enumerate(sentences):
        english = sentence['english']
        chinese = sentence['chinese']
        duration = sentence['duration']

        # Calculate actual timing
        start_actual = t
        end_actual = t + duration

        # Calculate display timing (with 200ms buffer)
        out_start_ms = start_actual - DISPLAY_BUFFER_SEC
        out_end_ms = end_actual + DISPLAY_BUFFER_SEC
        out_start_hhmmss_ms = sec_to_hhmmss_ms(out_start_ms)
        out_end_hhmmss_ms = sec_to_hhmmss_ms(out_end_ms)

        # Add to timeline
        timeline.append({
            "index": i,
            "english": english,
            "chinese": chinese,
            "duration": duration,
            "start_ts": start_actual,
            "end_ts": end_actual,
            "out_start_ms": out_start_ms,
            "out_end_ms": out_end_ms,
            "out_start_hhmmss_ms": out_start_hhmmss_ms,
            "out_end_hhmmss_ms": out_end_hhmmss_ms
        })

        logger.info(f"[Sentence {i+1}/{len(sentences)}]")
        logger.info(f"  English: {english}")
        logger.info(f"  Chinese: {chinese}")
        logger.info(f"  Duration: {duration:.3f}s")
        logger.info(f"  Actual timing: {start_actual:.3f}s - {end_actual:.3f}s")
        logger.info(f"  Output display: {out_start_hhmmss_ms} ~ {out_end_hhmmss_ms} (with {DISPLAY_BUFFER_SEC*1000:.0f}ms buffer)")
        logger.info("")

        # Normalize sentence audio
        sentence_file = os.path.join(TMP_DIR, f"sentence_{i}.wav")
        if not os.path.exists(sentence_file):
            logger.error(f"File not found: {sentence_file}")
            sys.exit(1)

        normalized_file = os.path.join(TMP_DIR, f"sentence_{i}_norm.wav")
        normalize_audio(sentence_file, normalized_file)
        normalized_files.append(normalized_file)

        # Create gap after sentence (except last)
        if i < len(sentences) - 1:
            gap_file = os.path.join(TMP_DIR, f"silence_{i}.wav")
            create_silence_file(GAP_DURATION_SEC, gap_file)
            t = end_actual + GAP_DURATION_SEC
        else:
            t = end_actual

    # Create concat list
    logger.info("-"*70)
    logger.info("Creating concatenation list...")
    concat_list = []

    # Add initial silence
    initial_silence_file = os.path.join(TMP_DIR, "initial_silence.wav")
    if not os.path.exists(initial_silence_file):
        create_silence_file(INITIAL_SILENCE_SEC, initial_silence_file)
    normalized_initial = os.path.join(TMP_DIR, "initial_silence_norm.wav")
    normalize_audio(initial_silence_file, normalized_initial)
    concat_list.append(normalized_initial)
    logger.info(f"Added initial silence: {normalized_initial} ({INITIAL_SILENCE_SEC*1000:.0f}ms)")

    # Add sentences and gaps
    for i, norm_file in enumerate(normalized_files):
        concat_list.append(norm_file)
        logger.info(f"Added sentence {i+1}: {norm_file}")

        if i < len(sentences) - 1:
            gap_file = os.path.join(TMP_DIR, f"silence_{i}.wav")
            normalized_gap = os.path.join(TMP_DIR, f"silence_{i}_norm.wav")
            normalize_audio(gap_file, normalized_gap)
            concat_list.append(normalized_gap)
            logger.info(f"Added gap {i+1}: {normalized_gap} ({GAP_DURATION_SEC*1000:.0f}ms)")

    # Write concat list
    concat_file = os.path.join(TMP_DIR, "concat_list.txt")
    with open(concat_file, 'w', encoding='utf-8') as f:
        for file_path in concat_list:
            abs_path = os.path.abspath(file_path).replace('\\', '/')
            f.write(f"file '{abs_path}'\n")

    logger.info(f"Concat list written: {concat_file}")
    logger.info(f"Total files to concatenate: {len(concat_list)}")
    logger.info("")

    # Merge audio files to WAV
    output_wav = os.path.join(RES_DIR, f"{base_name}.wav")
    output_mp3 = os.path.join(RES_DIR, f"{base_name}.mp3")
    logger.info("-"*70)
    logger.info(f"Merging audio files to: {output_wav}")

    result = subprocess.run([
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
        '-i', concat_file, '-acodec', 'pcm_s16le', '-ar', '22050', '-ac', '1',
        output_wav
    ], capture_output=True, text=True)

    if result.returncode != 0:
        logger.error("FFmpeg merge failed!")
        logger.error(result.stderr)
        sys.exit(1)

    logger.info("Audio merged successfully!")
    logger.info("")

    # Convert WAV to MP3
    logger.info("-"*70)
    logger.info(f"Converting to MP3: {output_mp3}")

    result = subprocess.run([
        'ffmpeg', '-y', '-i', output_wav,
        '-codec:a', 'libmp3lame', '-b:a', '128k',
        output_mp3
    ], capture_output=True, text=True)

    if result.returncode != 0:
        logger.error("FFmpeg MP3 conversion failed!")
        logger.error(result.stderr)
        sys.exit(1)

    logger.info("MP3 conversion successful!")
    logger.info("")

    # Save step2.json
    step2_json = os.path.join(RES_DIR, f'{base_name}.step2.json')
    logger.info("-"*70)
    logger.info(f"Saving timestamp JSON: {step2_json}")

    with open(step2_json, 'w', encoding='utf-8') as f:
        output_timeline = []
        for item in timeline:
            output_timeline.append({
                "english": item["english"],
                "chinese": item["chinese"],
                "duration": item["duration"],
                "start_ts": item["start_ts"],
                "end_ts": item["end_ts"]
            })
        json.dump(output_timeline, f, ensure_ascii=False, indent=2)

    logger.info("Timestamp JSON saved successfully")

    # Generate markdown output
    output_md = os.path.join(RES_DIR, f"{base_name}.md")
    logger.info(f"Generating markdown output: {output_md}")

    with open(output_md, 'w', encoding='utf-8') as f:
        f.write("```audio-player\n")
        f.write(f"[[{base_name}.mp3]]\n")

        for item in timeline:
            first_word = item['english'].split()[0] if item['english'].split() else ''
            f.write(f"{item['out_start_hhmmss_ms']} → {item['out_end_hhmmss_ms']} --- {first_word}\n")

        f.write("```\n")

    logger.info("Markdown output generated successfully")
    logger.info("")

    logger.info("="*70)
    logger.info("Step 2 completed successfully!")
    logger.info(f"  - Audio files: {output_wav}, {output_mp3}")
    logger.info(f"  - Timestamp JSON: {step2_json}")
    logger.info(f"  - Markdown output: {output_md}")
    logger.info("="*70)
    logger.info("")
