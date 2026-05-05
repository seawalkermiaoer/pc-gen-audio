#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse
from datetime import datetime

# Local imports
from src.config.constants import DEFAULT_INPUT_FILE, RES_DIR, LOG_FILE
from src.common.logger import setup_logger
from src.tts.generator import step1_generate_audio
from src.audio.processor import step2_merge_audio
from src.common.gemini import get_gemini_service
from src.config.constants import DEFAULT_INPUT_FILE, RES_DIR, LOG_FILE, TMP_DIR
import json

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

    # Setup logger
    logger = setup_logger(BASE_NAME)

    start_time = datetime.now()

    logger.info("="*70)
    logger.info("AUDIO GENERATION PIPELINE (Modularized)")
    logger.info("="*70)
    logger.info(f"Input: {INPUT_FILE}")
    logger.info(f"Output: {BASE_NAME}.wav, {BASE_NAME}.step2.json, {BASE_NAME}.md")
    logger.info("="*70)
    logger.info("")

    try:
        # Pre-processing: Convert Markdown to JSON using Gemini if needed
        if INPUT_FILE.lower().endswith('.md'):
            logger.info(f"Detecting Markdown input. Calling Gemini for preprocessing...")
            gemini = get_gemini_service()
            
            with open(INPUT_FILE, 'r', encoding='utf-8') as f:
                article_text = f.read()
            
            processed_data = gemini.convert_article_to_json(article_text)
            if not processed_data:
                logger.error("Gemini preprocessing failed.")
                sys.exit(1)
            
            # Save to temporary JSON file
            temp_json_path = os.path.join(TMP_DIR, f"{BASE_NAME}_processed.json")
            if not os.path.exists(TMP_DIR):
                os.makedirs(TMP_DIR)
                
            with open(temp_json_path, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Gemini preprocessing completed. Saved to {temp_json_path}")
            INPUT_FILE = temp_json_path

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
