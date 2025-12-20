# Roman Catechism Extraction

This directory contains the extraction script for the Catechism of the Council of Trent (McHugh & Callan Translation, 1923).

## Overview

The script extracts the catechism from a PDF file and converts it to clean Markdown format.

- **Translation Accuracy**: SaintsBooks.net provides the correct McHugh & Callan translation (not the older Donovan translation)
- **Source**: The PDF file is available directly from SaintsBooks.net

## Prerequisites

1. **Download the PDF file**:
   - **Source**: [SaintsBooks.net](https://www.saintsbooks.net/books/The%20Roman%20Catechism.pdf)
   - **Direct URL**: https://www.saintsbooks.net/books/The%20Roman%20Catechism.pdf
   - **File**: `The Roman Catechism.pdf`
   - **Important**: This is the McHugh & Callan translation (1923), not the older Donovan translation (1829)

2. **Place in this directory**:
   ```bash
   cp ~/Downloads/The\ Roman\ Catechism.pdf data_engineering/data_sources/catholic_catechism_trent/
   ```

   Or if you're already in this directory:
   ```bash
   cp ~/Downloads/The\ Roman\ Catechism.pdf .
   ```

## Usage

```bash
python extract_catechism.py
```

## Output

The script generates a single Markdown file: `Catholic_Catechism_Trent_McHugh_Callan.md` directly in `data_final/catholic_catechism_trent/` (final output location).

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

If your PDF has different header patterns, adjust the regex in `add_markdown_headers()`.

## Requirements

- PDF file in this directory (`data_engineering/data_sources/catholic_catechism_trent/`)
- `pypdf` library (for PDF text extraction)
- Python 3.10+

## Post-Processing

After extraction, you may need to manually:
- Check the Table of Contents for correct Roman numerals
- Move footnotes (they may appear inline in RTF)
- Verify header formatting matches your expectations

## Notes

- PDF text extraction may have formatting artifacts; manual cleanup may be needed
- Footnotes often need manual adjustment after extraction
- Page numbers and headers/footers are automatically removed during extraction

