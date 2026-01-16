# Audio Post-Processing Pipeline

A simple script for post-processing podcast audio files by appending a standardized intro and normalizing loudness levels.

## Overview

This script automates the post-processing workflow for podcast episodes:

1. **Append Standard Intro**: Prepends a mastered 20-second intro file to the beginning of the podcast
2. **Loudness Normalization**: Adjusts the podcast audio loudness to match the intro's loudness level (-16 LUFS)
3. **Export**: Saves the final processed audio file

## Requirements

### Input Files

- **Standard Intro**: A 20-second `.wav` file that is already mastered to **-16 LUFS**
  - This file serves as the reference for loudness normalization
  - Should be a high-quality, mastered audio file

- **Podcast Audio**: A raw `.m4a` file containing the main podcast content
  - Typically 4+ minutes in length
  - Not yet mastered or normalized
  - Will be adjusted to match the intro's loudness level

### Output

- **Processed Podcast**: A single audio file containing:
  - The standard intro at the beginning
  - The normalized podcast audio following the intro
  - All audio matched to -16 LUFS loudness standard

## File Paths

**Important**: All input and output files are located **outside the repository**. The script uses absolute file paths to access these files.

You will need to provide:
- Path to the standard intro `.wav` file
- Path to the raw podcast `.m4a` file
- Path where the processed output file should be saved

## Usage

The script is designed to be run manually on a regular basis as you finish raw podcast files. It provides a simple command-line interface where you specify the file paths.

### Example Workflow

1. Finish recording and exporting your raw podcast as `.m4a`
2. Run the post-processing script with the file paths
3. The script will:
   - Load the intro and podcast files
   - Normalize the podcast to match the intro's loudness (-16 LUFS)
   - Concatenate intro + normalized podcast
   - Export the final file
4. Use the processed file for distribution

## Technical Details

### Loudness Standard

- **Target**: -16 LUFS (Loudness Units relative to Full Scale)
- **Reference**: The standard intro file is already at -16 LUFS
- **Method**: The podcast audio will be analyzed and adjusted to match this target loudness level

### Audio Processing Steps

1. **Load Files**: Read both the intro `.wav` and podcast `.m4a` files
2. **Loudness Analysis**: Measure the current loudness of the podcast audio
3. **Normalization**: Apply gain adjustment to bring podcast to -16 LUFS
4. **Concatenation**: Append the intro to the beginning of the normalized podcast
5. **Export**: Save the final processed audio file

## Dependencies

The script will use audio processing libraries capable of:
- Reading `.wav` and `.m4a` audio formats
- Measuring and adjusting loudness (LUFS)
- Concatenating audio files
- Exporting processed audio

## Future Enhancements

Potential improvements for future versions:
- Batch processing multiple podcast files
- Configurable loudness targets
- Additional audio processing options (fade in/out, compression, etc.)
- Progress indicators for long-running operations
