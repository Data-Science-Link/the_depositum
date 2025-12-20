# Roman Catechism Extraction

This directory contains the extraction script for the Catechism of the Council of Trent (McHugh & Callan Translation, 1923).

## Overview

The script extracts the catechism from a PDF file and converts it to clean Markdown format with comprehensive header detection and formatting.

- **Translation Accuracy**: SaintsBooks.net provides the correct McHugh & Callan translation (not the older Donovan translation)
- **Source**: The PDF file is available directly from SaintsBooks.net
- **Formatting**: Uses `pdfplumber` for advanced text extraction with italic detection
- **Content Preservation**: **CRITICAL** - The script NEVER removes content from the PDF, only adjusts formatting for better readability

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
# Full extraction (all 346 pages)
python extract_catechism.py

# Test extraction (first 5 pages)
python extract_catechism.py --max-pages 5
```

## Output

The script generates a single Markdown file: `Catholic_Catechism_Trent_McHugh_Callan.md` directly in `data_final/catholic_catechism_trent/` (final output location).

The file includes:
- YAML frontmatter with metadata
- `# PART` headers for main parts (PART I, PART II, PART III, PART IV)
- `## ARTICLE` headers for articles (ARTICLE I, ARTICLE II, etc.)
- `##` headers for major sections (PREFACE, INTRODUCTORY, THE SACRAMENT OF..., etc.)
- `###` headers for major subsections (Meaning Of This Article, Importance Of This Article, etc.)
- `####` headers for italicized subsection titles (Different Abodes Called Hell, Two Judgments, etc.)
- Clean text with proper formatting
- All content preserved exactly as in the PDF

## Header Detection

The script uses multiple methods to detect and format headers:

### Automatic Detection Methods:
1. **Font Analysis**: Detects italicized text using `pdfplumber` character-level font analysis
2. **Pattern Matching**: Regex patterns for structural elements (PART, ARTICLE, etc.)
3. **Known Sections**: Pattern-based fallback for common italicized section titles

### Header Hierarchy:
- `# PART I : THE CREED` - Top-level parts
- `## ARTICLE I : "I BELIEVE IN GOD..."` - Articles under parts
- `## PREFACE`, `## INTRODUCTORY` - Major sections
- `## THE SACRAMENT OF BAPTISM` - Sacrament sections
- `### Meaning Of This Article` - Major subsections
- `#### Different Abodes Called Hell` - Italicized subsection titles
- `#### Two Judgments` - Other italicized section titles

### Content Preservation:
**CRITICAL RULE**: The script NEVER removes words or content from the PDF. All text content is preserved exactly as extracted. Only formatting artifacts (null bytes, excessive whitespace, page number references) are removed.

## Requirements

- PDF file in this directory (`data_engineering/data_sources/catholic_catechism_trent/`)
- `pdfplumber` library (for PDF text extraction with formatting detection)
- Python 3.10+
- Dependencies installed via `uv pip install -e ..` from project root

## Technical Details

### Extraction Process:
1. **Text Extraction**: Uses `pdfplumber` to extract text with character-level formatting information
2. **Italic Detection**: Analyzes font names and flags to identify italicized text (for section titles)
3. **Text Cleaning**: Removes formatting artifacts (page numbers, excessive whitespace, null bytes)
4. **Line Splitting**: Splits long lines that contain multiple section headers
5. **Header Formatting**: Applies markdown headers based on structure and formatting

### Key Functions:
- `clean_text()`: Removes formatting artifacts while preserving all content
- `add_markdown_headers()`: Detects and formats headers with proper hierarchy
- `_extract_page_with_italics()`: Extracts text and detects italicized lines per page
- `_format_known_italic_sections()`: Pattern-based fallback for italicized section titles

## Notes

- **Content Preservation**: All substantive content from the PDF is preserved. Only formatting artifacts are removed.
- **Page Numbers**: Automatically removed during extraction (they appear as formatting artifacts)
- **Italic Detection**: May not detect all italicized sections; pattern-based fallback handles common cases
- **Header Detection**: The script is designed to be conservative - it may miss some headers but will not incorrectly format content
- **Logging**: All operations are logged to `data_engineering/logs/catechism_extraction.log`

