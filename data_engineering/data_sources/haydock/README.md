# Haydock Bible Commentary Extraction

This directory contains the extraction script for the Haydock Catholic Bible Commentary (1859 Edition).

## Overview

The script extracts commentary from an EPUB file and converts it to clean Markdown format. The EPUB format is ideal because:

- **Structured Data**: EPUB is technically a ZIP file containing HTML
- **Complete**: Contains the entire commentary in a single file (~5MB)
- **No Rate Limits**: No need for web crawling or API calls

## Prerequisites

1. **Download the EPUB file**:
   - Source: Isidore E-Book Library or JohnBlood GitLab
   - File: `Haydock Catholic Bible Commentary.epub`

2. **Place in raw directory**:
   ```bash
   cp ~/Downloads/Haydock\ Catholic\ Bible\ Commentary.epub raw/
   ```

## Usage

```bash
python extract_commentary.py
```

## Output

The script generates Markdown files organized by book/chapter in `data_engineering/processed_data/haydock/` (intermediate), which are then copied to `data_final/haydock/` (final output).

## Customization

The script uses generic HTML parsing that works with most EPUB structures. However, if your specific EPUB has a different structure:

1. **Inspect the EPUB structure**:
   ```bash
   # Unzip the EPUB (it's just a ZIP file)
   unzip "Haydock Catholic Bible Commentary.epub" -d epub_contents/
   # Open HTML files in a browser and inspect the structure
   ```

2. **Adjust parsing logic** in `extract_commentary.py`:
   - Look for specific CSS classes: `soup.find_all('p', class_='commentary')`
   - Adjust selectors based on your EPUB's HTML structure
   - Update the `process_book_content()` function

## Requirements

- EPUB file in `raw/` directory
- `ebooklib` library
- `beautifulsoup4` library
- Python 3.10+

## Notes

- The script attempts to automatically detect book titles and structure
- Commentary notes are separated from verse text
- You may need to manually adjust parsing based on your specific EPUB version

