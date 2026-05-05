#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

# OpenAI TTS Configuration
OPENAI_BASE_URL = "http://127.0.0.1:8880/v1"
OPENAI_API_KEY = "not-needed"
OPENAI_MODEL = "kokoro"
OPENAI_VOICE = "af_sky+af_bella"

# Gemini AI Configuration
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

# Audio Processing Configuration
INITIAL_SILENCE_SEC = 0.3  # 300ms
GAP_DURATION_SEC = 0.7  # 700ms
GAP_BUFFER_SEC = 0.3  # ±300ms for gap timing
DISPLAY_BUFFER_SEC = 0.2  # 200ms for display

# File Paths
DEFAULT_INPUT_FILE = "x1.json"
TMP_DIR = 'tmp'
RES_DIR = 'res'
LOG_FILE = "app.log"
