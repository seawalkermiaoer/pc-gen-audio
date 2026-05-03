#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import shutil
import subprocess
import sys
import logging
import argparse
from math import ceil, floor
from datetime import datetime
from openai import OpenAI

# =============================================================================
# Configuration (Defaults)
# =============================================================================

# OpenAI TTS Configuration
OPENAI_BASE_URL = "http://localhost:8880/v1"
OPENAI_API_KEY = "not-needed"
OPENAI_MODEL = "kokoro"
OPENAI_VOICE = "af_sky+af_bella"

# Audio Processing Configuration
INITIAL_SILENCE_SEC = 0.3  # 300ms
GAP_DURATION_SEC = 0.7  # 700ms
GAP_BUFFER_SEC = 0.3  # ±300ms for gap timing
DISPLAY_BUFFER_SEC = 0.2  # 200ms for display

# File Paths (will be set via command line args)
DEFAULT_INPUT_FILE = "x1.json"
TMP_DIR = 'tmp'
RES_DIR = 'res'
LOG_FILE = "app.log"

# =============================================================================
# Logging Setup
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =============================================================================
# Utility Functions
# =============================================================================

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

# =============================================================================
# Step 1: Generate Audio from Text
# =============================================================================

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
    if os.path.exists(TMP_DIR):
        shutil.rmtree(TMP_DIR)
    os.makedirs(TMP_DIR)

    if not os.path.exists(RES_DIR):
        os.makedirs(RES_DIR)

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

# =============================================================================
# Step 2: Merge Audio and Generate Timestamps
# =============================================================================

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

# =============================================================================
# Main Workflow
# =============================================================================

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Audio Generation Pipeline - Generate audio from text with timestamps',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                          # Use default input (x1.json)
  python main.py input.json              # Use custom input file
  python main.py --input data.json       # Using --input flag
  python main.py data.txt --base audio1  # Custom base name

Input file format:
  JSON array with English-Chinese sentence pairs:
  [
    {"english": "Hello", "chinese": "你好"},
    {"english": "World", "chinese": "世界"}
  ]
        """
    )

    parser.add_argument(
        'input',
        nargs='?',  # Positional argument (optional)
        default=DEFAULT_INPUT_FILE,
        help=f'Input JSON file with sentences (default: {DEFAULT_INPUT_FILE})'
    )

    parser.add_argument(
        '--input',
        dest='input_alt',
        help='Alternative way to specify input file'
    )

    parser.add_argument(
        '--base',
        dest='base_name',
        help='Base name for output files (default: derived from input filename)'
    )

    args = parser.parse_args()

    # Handle alternative input flag
    if args.input_alt:
        args.input = args.input_alt

    # Validate input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    # Set base name if not provided
    if not args.base_name:
        args.base_name = os.path.splitext(os.path.basename(args.input))[0]

    return args

def main():
    """Main workflow: Run complete audio generation pipeline"""
    # Parse command line arguments
    args = parse_arguments()
    INPUT_FILE = args.input
    BASE_NAME = args.base_name

    # Update log file name to include base name
    global LOG_FILE
    base_log_name = os.path.splitext(os.path.basename(LOG_FILE))[0]
    LOG_FILE = f"{base_log_name}_{BASE_NAME}.log"

    start_time = datetime.now()

    logger.info("="*70)
    logger.info("AUDIO GENERATION PIPELINE")
    logger.info("="*70)
    logger.info(f"Input: {INPUT_FILE}")
    logger.info(f"Output: {BASE_NAME}.wav, {BASE_NAME}.step2.json, {BASE_NAME}.md")
    logger.info(f"Log: {LOG_FILE}")
    logger.info("="*70)
    logger.info("")

    try:
        # Step 1: Generate audio
        step1_generate_audio(INPUT_FILE, BASE_NAME)

        # Step 2: Merge and timestamp
        step2_merge_audio(BASE_NAME)

        # Success summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info("="*70)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY!")
        logger.info("="*70)
        logger.info(f"Total processing time: {duration:.2f}s")
        logger.info("")
        logger.info("Output files:")
        logger.info(f"  - {RES_DIR}/{BASE_NAME}.wav (merged audio, WAV format)")
        logger.info(f"  - {RES_DIR}/{BASE_NAME}.mp3 (merged audio, MP3 format, 128kbps)")
        logger.info(f"  - {RES_DIR}/{BASE_NAME}.step2.json (timestamps)")
        logger.info(f"  - {RES_DIR}/{BASE_NAME}.md (markdown timeline)")
        logger.info(f"  - {LOG_FILE} (execution log)")
        logger.info("="*70)

    except Exception as e:
        logger.error("="*70)
        logger.error("PIPELINE FAILED!")
        logger.error("="*70)
        logger.error(f"Error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    main()
