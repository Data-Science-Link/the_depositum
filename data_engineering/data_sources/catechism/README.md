# Roman Catechism Extraction

This directory contains the extraction script for the Catechism of the Council of Trent (McHugh & Callan Translation, 1923).

## Overview

The script extracts the catechism from an RTF (Rich Text Format) file and converts it to clean Markdown. RTF is used because:

- **Translation Accuracy**: SaintsBooks.net provides the correct McHugh & Callan translation (not the older Donovan translation)
- **Better Structure**: RTF preserves text hierarchy better than PDF scans
- **Easier Parsing**: More structured than raw text files

## Prerequisites

1. **Download the RTF file**:
   - Source: SaintsBooks.net
   - File: `Catechism of the Council of Trent.rtf`
   - **Important**: Ensure it's the McHugh & Callan translation (1923), not the Donovan translation (1829)

2. **Place in raw directory**:
   ```bash
   cp ~/Downloads/Catechism\ of\ the\ Council\ of\ Trent.rtf raw/
   ```

## Usage

```bash
python extract_catechism.py
```

## Output

The script generates a single Markdown file: `Catechism_McHugh_Callan.md` in `data_engineering/processed_data/catechism/` (intermediate), which is then copied to `data_final/catechism/` (final output).

The file includes:
- `# PART` headers for main parts
- `## ARTICLE` headers for articles
- `### QUESTION` headers for questions/sections
- Clean text with proper formatting

## Header Detection

The script uses regex patterns to detect headers:
- `PART I`, `PART II`, etc. → `# PART I`
- `ARTICLE I`, `ARTICLE II`, etc. → `## ARTICLE I`
- `QUESTION I`, `QUESTION II`, etc. → `### QUESTION I`

If your RTF has different header patterns, adjust the regex in `add_markdown_headers()`.

## Requirements

- RTF file in `raw/` directory
- `striprtf` library
- Python 3.10+

## Post-Processing

After extraction, you may need to manually:
- Check the Table of Contents for correct Roman numerals
- Move footnotes (they may appear inline in RTF)
- Verify header formatting matches your expectations

## Notes

- The script tries UTF-8 encoding first, then falls back to latin-1
- RTF conversions can leave artifacts; manual cleanup may be needed
- Footnotes often need manual adjustment after extraction

