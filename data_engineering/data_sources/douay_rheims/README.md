# Douay-Rheims Bible Extraction

This directory contains the extraction script for the Douay-Rheims Bible (1899 American Edition).

## Overview

The script downloads the Bible directly from `bible-api.com`, which sources its text from `ebible.org`, a standard for public domain Bible data. This ensures:

- **Data Integrity**: Official API source
- **Canon Accuracy**: Automatically fetches all 73 books for Catholic translation
- **Clean Formatting**: Outputs standard Markdown ready for NotebookLM

## Usage

```bash
python extract_bible.py
```

## Output

The script generates 73 Markdown files (one per book) in `data_engineering/processed_data/douay_rheims/` (intermediate), which are then copied to `data_final/douay_rheims/` (final output).

Each file contains:
- Frontmatter with title and tags
- Book title as H1 header
- Chapters as H2 headers
- Verses formatted as `**verse_number** verse_text`

## Configuration

The script uses settings from `data_engineering/config/pipeline_config.yaml`:
- API endpoint: `https://bible-api.com/data/dra`
- Translation ID: `dra` (Douay-Rheims 1899 American Edition)
- Rate limiting: 0.5 second delay between requests

## Requirements

- Internet connection
- `requests` library
- Python 3.10+

## Notes

- The API is rate-limited, so the script includes delays between requests
- All 73 books are automatically detected and downloaded
- Files are saved with safe filenames (spaces replaced with underscores)

