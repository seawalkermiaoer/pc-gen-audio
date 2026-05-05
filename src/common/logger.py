#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
from src.config.constants import LOG_FILE

def setup_logger(base_name):
    """
    Setup logging configuration.
    
    - base_name: The base name for the log file (e.g., 'x1')
    Returns the configured logger instance.
    """
    base_log_name = os.path.splitext(os.path.basename(LOG_FILE))[0]
    dynamic_log_file = f"{base_log_name}_{base_name}.log"

    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(dynamic_log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)
