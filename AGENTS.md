# Agent Guidelines for Audio Generation Codebase

## Project Overview
This is an audio generation pipeline that converts English-Chinese sentence pairs into synchronized audio files with precise timestamps. The system generates speech using a local OpenAI TTS service, processes audio with ffmpeg, and produces timestamped MP3/WAV files along with JSON metadata.

## Environment Setup

### Prerequisites
- Python 3.9+ (located at `/usr/bin/python3`)
- ffmpeg and ffprobe (required for audio processing)
- Local OpenAI-compatible TTS service running on `http://localhost:8880/v1`

### Directory Structure
- `main.py` - Main pipeline script
- `test_silence.py` - Test utility for silence generation
- `x1.json` - Example input (English-Chinese sentence pairs)
- `res/` - Output directory for results
- `tmp/` - Temporary directory for intermediate files
- `node_modules/` - Node.js dependencies (unused in Python code)

## Build & Run Commands

### Main Pipeline
```bash
# Run full pipeline with default input
python3 main.py

# Run with custom input file
python3 main.py custom.json

# Run with custom base name for output files
python3 main.py input.json --base output_name
```

### Testing
```bash
# Test silence generation utility
python3 test_silence.py

# Check audio duration (requires ffprobe)
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 file.wav
```

### Cleanup
```bash
# Remove temporary files
rm -rf tmp/

# Remove results
rm -rf res/
```

## Code Style Guidelines

### Python Version & Imports
- Use Python 3.9+
- Always include shebang: `#!/usr/bin/env python3`
- File encoding: `# -*- coding: utf-8 -*-`
- Import order (follows main.py):
  1. Standard library imports
  2. Third-party imports
  3. Local imports

### Naming Conventions
- **Variables**: `snake_case` (e.g., `initial_silence_sec`, `gap_duration_sec`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `OPENAI_BASE_URL`, `GAP_DURATION_SEC`)
- **Functions**: `snake_case` (e.g., `get_audio_duration`, `normalize_audio`)
- **Classes**: `CamelCase` (not currently used in codebase)
- **Files**: `snake_case` (e.g., `test_silence.py`, `main.py`)

### Formatting
- Indentation: 4 spaces (no tabs)
- Line length: Maximum 80 characters (current code uses ~70 for headers)
- String formatting: Use f-strings for logging (e.g., `logger.info(f"Loaded {len(sentences)} sentences")`)
- Use descriptive logging messages with structured format

### Error Handling
- Use `try-except` blocks for critical operations
- Log all errors with appropriate severity levels
- Exit with `sys.exit(1)` on fatal errors
- Always check file existence before operations
- Validate external command execution (ffmpeg, ffprobe)

### Logging Standards
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
```

- Use `logger.info()` for normal operations
- Use `logger.error()` for failures
- Use `logger.debug()` for detailed troubleshooting
- Always include contextual information in log messages

### File Operations
- Always use `os.path.exists()` before accessing files
- Handle paths with `os.path.join()` for cross-platform compatibility
- Use `os.makedirs()` with existence check for directory creation
- Always specify `encoding='utf-8'` for text files

### Audio Processing
- Input format: JSON array with `{"english": "...", "chinese": "..."}` objects
- Audio format: PCM 16-bit, 22050 Hz, mono
- Silence files: Generated via ffmpeg's `anullsrc`
- Normalization: Always normalize to standard format before concatenation

### Function Documentation
```python
def function_name(param1, param2):
    """
    Brief description of function purpose.
    
    - Detailed explanation of what it does
    - Parameters description
    - Return value description
    
    Returns:
        Description of return value
    """
```

### External Command Execution
```python
def run_external_command(cmd_args):
    """Execute external command with error handling."""
    result = subprocess.run(
        cmd_args,
        capture_output=True, 
        text=True, 
        check=True
    )
    return result
```

### Configuration Management
- Keep configuration constants at top of file
- Use command-line arguments for runtime configuration
- Document all configurable parameters
- Validate input before processing

## Development Workflow

### Adding New Features
1. Understand existing pipeline structure (Step 1 → Step 2)
2. Follow existing naming and logging conventions
3. Test with `test_silence.py` for audio utilities
4. Run full pipeline to verify integration

### Testing Changes
1. Create test input JSON with sample sentences
2. Run `python3 main.py test.json --base test_output`
3. Verify outputs in `res/` directory:
   - `test_output.wav` - Raw audio
   - `test_output.mp3` - Compressed audio
   - `test_output.step2.json` - Timestamps
   - `test_output.md` - Markdown timeline

### Debugging
1. Check `app.log` for detailed execution log
2. Verify ffmpeg/ffprobe availability
3. Ensure local TTS service is running on port 8880
4. Check file permissions for tmp/ and res/ directories

## Performance Considerations
- Audio files are stored temporarily in `tmp/` during processing
- Clean up `tmp/` directory periodically
- Monitor disk space for large audio batches
- Consider batch size limits based on available memory

## Security Notes
- API key is hardcoded as "not-needed" for local TTS service
- Input files are trusted (no sanitization performed)
- File paths are validated before processing
- No network operations beyond localhost:8880

## Maintenance Tasks
- Monitor `app.log` file size (rotates based on base name)
- Clean `tmp/` directory after successful runs
- Backup important result files from `res/` directory
- Update Python dependencies if needed

## Common Issues & Solutions
- **FFmpeg not found**: Install via `brew install ffmpeg` (macOS)
- **Permission denied**: Ensure write access to current directory
- **TTS service unavailable**: Start local TTS service on port 8880
- **JSON parsing error**: Validate input JSON format with `python3 -m json.tool`

## References
- See `main.py` for complete implementation reference
- See `x1.json` for input format example
- See `res/x1.step2.json` for output format example