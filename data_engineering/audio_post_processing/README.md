# Audio Post-Processing Pipeline

A simple script for post-processing podcast audio files by appending a standardized intro and normalizing loudness levels.

## Overview

This script automates the post-processing workflow for podcast episodes:

1. **Append Standard Intro**: Prepends a mastered 20-second intro file to the beginning of the podcast
2. **Loudness Normalization**: Normalizes both intro and podcast audio to -16 LUFS (intro normalized if outside ±0.5 LUFS tolerance)
3. **Export**: Saves the final processed audio file as MP3 (default) or specified format

## Requirements

### Input Files

- **Standard Intro**: A 20-second `.wav` file (ideally mastered to **-16 LUFS**)
  - If the intro is outside ±0.5 LUFS of -16, it will be automatically normalized
  - Should be a high-quality, mastered audio file

- **Podcast Audio**: A raw `.m4a` file containing the main podcast content
  - Typically 4+ minutes in length
  - Not yet mastered or normalized
  - Will be adjusted to match the intro's loudness level

### Output

- **Processed Podcast**: A single MP3 file (default) containing:
  - The normalized intro at the beginning
  - The normalized podcast audio following the intro
  - All audio matched to -16 LUFS loudness standard
  - Exported at 256kbps VBR (Variable Bitrate) for high quality

## File Paths

**Important**: All input and output files are located **outside the repository**. The script uses absolute file paths to access these files.

You will need to provide:
- Path to the standard intro `.wav` file
- Path to the raw podcast `.m4a` file
- Path where the processed output file should be saved (optional - defaults to "Mastered {podcast_name}.mp3" in the same directory)

## Installation

### Prerequisites

1. **ffmpeg** must be installed on your system (required for MP3/M4A support)
   - macOS: `brew install ffmpeg`
   - Linux: `sudo apt-get install ffmpeg` or `sudo yum install ffmpeg`
   - Windows: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

2. **Install Python dependencies**:
   ```bash
   uv sync
   ```

## Usage

The script is designed to be run manually on a regular basis as you finish raw podcast files. It provides a simple command-line interface where you specify the file paths.

### Basic Usage

```bash
# With explicit output path (MP3 format)
uv run python data_engineering/audio_post_processing/process_podcast.py \
    --intro /path/to/intro.wav \
    --podcast /path/to/podcast.m4a \
    --output /path/to/output.mp3

# Without --output (auto-generates "Mastered {podcast_name}.mp3" in same directory)
uv run python data_engineering/audio_post_processing/process_podcast.py \
    --intro /path/to/intro.wav \
    --podcast /path/to/podcast.m4a
```

### Command-Line Arguments

- `--intro`: Path to the intro `.wav` file (required)
- `--podcast`: Path to the raw podcast `.m4a` file (required)
- `--output`: Path where the processed output file should be saved (optional, defaults to "Mastered {podcast_name}.mp3")
- `--target-lufs`: Target loudness in LUFS (optional, default: -16.0)

### Example Workflow

1. Finish recording and exporting your raw podcast as `.m4a`
2. Run the post-processing script:
   ```bash
   # Option 1: Let script auto-generate output filename
   uv run python data_engineering/audio_post_processing/process_podcast.py \
       --intro ~/Audio/intro.wav \
       --podcast ~/Audio/episode_01.m4a
   # Creates: ~/Audio/Mastered episode_01.mp3

   # Option 2: Specify custom output path
   uv run python data_engineering/audio_post_processing/process_podcast.py \
       --intro ~/Audio/intro.wav \
       --podcast ~/Audio/episode_01.m4a \
       --output ~/Audio/episode_01_processed.mp3
   ```
3. The script will:
   - Load the intro and podcast files
   - Measure the current loudness of both files
   - Normalize intro if outside ±0.5 LUFS of target
   - Normalize podcast to -16 LUFS
   - Concatenate normalized intro + normalized podcast
   - Export as MP3 at 256kbps VBR (high quality)
4. Use the processed file for distribution

## Technical Details

### Loudness Standard

- **Target**: -16 LUFS (Loudness Units relative to Full Scale)
- **Tolerance**: ±0.5 LUFS (intro normalized if outside this range)
- **Method**: Both intro and podcast are analyzed and normalized to -16 LUFS
  - Intro is normalized if it's outside the tolerance range
  - Podcast is always normalized to match the target

### Audio Processing Steps

1. **Load Files**: Read both the intro `.wav` and podcast `.m4a` files
2. **Loudness Analysis**: Measure the current loudness of both intro and podcast
3. **Normalization**:
   - Normalize intro if outside ±0.5 LUFS of -16 LUFS
   - Normalize podcast to -16 LUFS
4. **Concatenation**: Append the normalized intro to the beginning of the normalized podcast
5. **Export**: Save the final processed audio file as MP3 (256kbps VBR) or specified format

## Dependencies

### Python Libraries

The script uses the following Python libraries (installed via `uv sync`):
- **pydub**: Audio manipulation, format conversion, and concatenation
- **pyloudnorm**: LUFS measurement and loudness normalization
- **numpy**: Required by pyloudnorm for audio processing

### System Dependencies

- **ffmpeg**: Required by pydub for MP3/M4A format support
  - Must be installed separately on your system
  - See Installation section above for setup instructions

### Export Format

- **Default Format**: MP3 (256kbps VBR - Variable Bitrate)
  - MP3 is the most compatible format for podcasting
  - VBR provides better quality at similar file sizes
  - High bitrate preserves audio quality during re-encoding
- **Supported Formats**: MP3, M4A (AAC), WAV
  - Format is determined by output file extension
  - If no extension provided, defaults to `.mp3`

## Future Enhancements

Potential improvements for future versions:
- Batch processing multiple podcast files
- Configurable loudness targets
- Additional audio processing options (fade in/out, compression, etc.)
- Progress indicators for long-running operations
