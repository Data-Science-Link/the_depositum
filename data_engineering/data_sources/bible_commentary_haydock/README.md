# Haydock Bible Commentary Extraction

This directory contains the extraction script for the Haydock Catholic Bible Commentary (1859 Edition).

## Overview

The script extracts commentary from an EPUB file and converts it to clean Markdown format. The EPUB format is ideal because:

- **Structured Data**: EPUB is technically a ZIP file containing HTML
- **Complete**: Contains the entire commentary in a single file (~5MB)
- **No Rate Limits**: No need for web crawling or API calls

## Prerequisites

**⚠️ IMPORTANT: The source EPUB file is NOT included in this repository to keep the repo size small. You must download it separately before running the extraction script.**

1. **Download the EPUB file**:
   - **Direct Download URL**: [Haydock Catholic Bible Commentary - Haydock, George Leo.epub](https://isidore.co/CalibreLibrary/Haydock,%20George%20Leo/Haydock%20Catholic%20Bible%20Commentary%20(3948)/Haydock%20Catholic%20Bible%20Commentary%20-%20Haydock,%20George%20Leo.epub)
   - **Source Directory**: [Isidore E-Book Library](https://isidore.co/CalibreLibrary/Haydock,%20George%20Leo/Haydock%20Catholic%20Bible%20Commentary%20(3948)/)
   - **File Size**: ~4.6MB
   - **File Name**: `Haydock Catholic Bible Commentary - Haydock, George Leo.epub`
   - **Note**: The ZIP file from Isidore did not work, but the direct EPUB download works correctly.

2. **Place the EPUB file in this directory**:
   ```bash
   # From the project root
   cp ~/Downloads/Haydock\ Catholic\ Bible\ Commentary\ -\ Haydock,\ George\ Leo.epub data_engineering/data_sources/bible_commentary_haydock/

   # Or if you're already in this directory
   cp ~/Downloads/Haydock\ Catholic\ Bible\ Commentary\ -\ Haydock,\ George\ Leo.epub .
   ```

   **Note**: The script will look for the EPUB file in this directory. The file is automatically ignored by git (see `.gitignore`) to keep the repository size small.

## Usage

```bash
python extract_commentary.py
```

## Output

The script generates Markdown files organized by book/chapter in `data_engineering/processed_data/bible_commentary_haydock/` (intermediate), which are then copied to `data_final/bible_commentary_haydock/` (final output).

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

