#!/usr/bin/env python3
"""
McHugh & Callan Catechism Extraction Script

This script extracts the Catechism of the Council of Trent (McHugh & Callan Translation)
from a PDF file and converts it to clean Markdown format.

The script uses the pypdf library to extract text from PDF,
then applies regex patterns to detect headers and insert Markdown syntax.

CRITICAL RULE: This script NEVER removes words or content from the PDF. All text content
is preserved exactly as extracted. Only formatting artifacts (null bytes, excessive whitespace,
page number references) are removed. The copyright notice and all substantive content are preserved.

Prerequisites:
    - Download the PDF file from SaintsBooks.net
    - Place it in this directory

Usage:
    python extract_catechism.py
"""

import sys
import re
import argparse
import logging
from pathlib import Path
from typing import Optional
import yaml
from pypdf import PdfReader

# Set up logging to both console and file
LOG_DIR = Path(__file__).parent.parent.parent.parent / "data_engineering" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "catechism_extraction.log"

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.handlers.clear()  # Prevent duplicate handlers if script is imported

# Create formatter (shared between handlers)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# File handler
file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Load configuration
CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "pipeline_config.yaml"
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent  # Go up to project root
try:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    # Resolve paths relative to project root
    INPUT_FILENAME = PROJECT_ROOT / config['paths']['raw_data']['catechism']
    OUTPUT_DIR = PROJECT_ROOT / config['paths']['final_output']['catechism']
    OUTPUT_FILENAME = config['output']['naming']['catechism']
except (FileNotFoundError, yaml.YAMLError, KeyError) as e:
    logger.warning(f"Could not load config, using defaults: {e}")
    INPUT_FILENAME = Path(__file__).parent / "The Roman Catechism.pdf"
    OUTPUT_DIR = Path(__file__).parent.parent.parent.parent / "data_final" / "catholic_catechism_trent"
    OUTPUT_FILENAME = "Catholic_Catechism_Trent_McHugh_Callan.md"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILEPATH = OUTPUT_DIR / OUTPUT_FILENAME


def clean_text(text: str) -> str:
    """Cleans up the raw text extracted from PDF.

    CRITICAL: This function only removes formatting artifacts (null bytes, excessive whitespace, etc.).
    It NEVER removes actual content or words from the PDF. All text content is preserved.

    Args:
        text: Raw text from PDF extraction

    Returns:
        Cleaned text string with all content preserved
    """
    # Remove common PDF artifacts (not content)
    text = text.replace('\x00', '')
    text = text.replace('\r', '')

    # Remove page number references (formatting only - lines with only dots and numbers at the end)
    # Pattern: "Text.............................................................................25"
    # This removes the dots and numbers, but preserves the text before them
    text = re.sub(r'\.{3,}\s*\d+\s*$', '', text, flags=re.MULTILINE)

    # Remove standalone page numbers (formatting only - lines with only numbers)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)

    # Clean up excessive dots used for spacing in PDF (formatting artifact)
    # Only remove dots that are clearly spacing, not content dots
    text = re.sub(r'\.{6,}', '', text)

    # Clean up extra spaces (formatting only)
    text = re.sub(r'[ \t]+', ' ', text)

    # Normalize line breaks (formatting only - PDF often creates excessive whitespace)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text


def add_markdown_headers(text: str) -> str:
    """Identifies major structural headers and applies Markdown syntax.

    CRITICAL: This function only adds markdown formatting. It NEVER removes or modifies
    the actual content. All words and text are preserved exactly as extracted from the PDF.

    Args:
        text: Cleaned plain text

    Returns:
        Text with Markdown headers applied (content unchanged)
    """
    # 1. Main Parts (e.g., "PART I") -> # Header 1
    text = re.sub(r'^PART ([IVX]+)', r'# PART \1', text, flags=re.MULTILINE)

    # 2. Articles (e.g., "ARTICLE I") -> ## Header 2
    # Handle split headers across lines (common in PDF extraction)
    text = re.sub(r'^ARTICLE ([IVX]+)\s*:\s*"([^"]+)"\s*\n\s*([^"]+)"',
                  r'## ARTICLE \1 : "\2 \3"', text, flags=re.MULTILINE)
    text = re.sub(r'^ARTICLE ([IVX]+)\s*:\s*"([^"]+)"', r'## ARTICLE \1 : "\2"', text, flags=re.MULTILINE)
    text = re.sub(r'^ARTICLE ([IVX]+)', r'## ARTICLE \1', text, flags=re.MULTILINE)

    # 3. Major section titles (only the most important structural elements)
    # These are major subsections within articles that deserve ### headers
    # Be conservative - only catch clear section titles, not every capitalized phrase
    major_section_patterns = [
        r'^(Meaning Of This Article)',
        r'^(Importance Of This Article)',
        r'^(Advantages Of [A-Z][^\.]{15,})',  # Only longer phrases
        r'^(Necessity Of [A-Z][^\.]{15,})',
        r'^(Definition Of [A-Z][^\.]{15,})',
        r'^(First Part [Oo]f This Article)',
        r'^(Second Part [Oo]f This Article)',
        r'^(Third Part [Oo]f This Article)',
    ]
    for pattern in major_section_patterns:
        text = re.sub(pattern, r'### \1', text, flags=re.MULTILINE)

    # 4. Special sections
    text = re.sub(r'^(QUESTION [IVX0-9]+)', r'### \1', text, flags=re.MULTILINE)
    text = re.sub(r'^(THE END OF THE CATECHISM)', r'## \1', text, flags=re.MULTILINE)

    return text


def main() -> int:
    """Main extraction function.

    Returns:
        Exit code: 0 for success, 1 for failure
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Extract Catechism of the Council of Trent from PDF')
    parser.add_argument('--max-pages', type=int, default=None,
                        help='Maximum number of pages to extract (for testing)')
    args = parser.parse_args()

    logger.info("Starting Catechism extraction...")
    logger.info(f"Output directory: {OUTPUT_DIR}")
    logger.info(f"📝 Logging to: {LOG_FILE}")
    if args.max_pages:
        logger.info(f"⚠️  TEST MODE: Limiting extraction to first {args.max_pages} pages")

    # Check if PDF file exists
    if not INPUT_FILENAME.exists():
        logger.error(f"Error: Could not find '{INPUT_FILENAME}'")
        logger.info("Please download the PDF file from SaintsBooks.net and place it in this directory")
        logger.info("URL: https://www.saintsbooks.net/books/The%20Roman%20Catechism.pdf")
        return 1

    logger.info(f"Reading PDF: {INPUT_FILENAME}...")

    # Extract text from PDF
    text_content: Optional[str] = None
    try:
        reader = PdfReader(INPUT_FILENAME)
        total_pages = len(reader.pages)
        logger.info(f"PDF has {total_pages} pages, extracting text...")

        # Limit pages if --max-pages is specified (for testing)
        pages_to_process = reader.pages[:args.max_pages] if args.max_pages else reader.pages
        actual_page_count = len(pages_to_process)

        text_parts = []
        for page_num, page in enumerate(pages_to_process, start=1):
            if page_num % 10 == 0 or page_num == 1:
                logger.info(f"  Processing page {page_num}/{actual_page_count}...")
            try:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            except Exception as e:
                logger.warning(f"  Warning: Could not extract text from page {page_num}: {e}")
                continue

        text_content = '\n'.join(text_parts)

        if not text_content or len(text_content.strip()) < 100:
            logger.error("Extracted text appears to be empty or too short")
            return 1

        logger.info(f"Successfully extracted {len(text_content)} characters from PDF")
    except Exception as e:
        logger.error(f"Error reading PDF file: {e}", exc_info=True)
        return 1

    if text_content is None:
        logger.error("Failed to extract text from PDF")
        return 1

    logger.info("Applying Markdown formatting...")
    # CRITICAL: All content from PDF is preserved. Only formatting is applied.
    clean_content = clean_text(text_content)
    final_content = add_markdown_headers(clean_content)

    # Write output file with frontmatter
    try:
        with open(OUTPUT_FILEPATH, 'w', encoding='utf-8') as f:
            # Frontmatter
            f.write("---\n")
            f.write("title: Catechism of the Council of Trent (McHugh & Callan Translation)\n")
            f.write("tags: catechism, council-of-trent, mchugh-callan, magisterium\n")
            f.write("---\n\n")

            # Content
            f.write(final_content)

        file_size_kb = OUTPUT_FILEPATH.stat().st_size / 1024
        logger.info(f"✅ Success! Converted text saved to: {OUTPUT_FILEPATH}")
        logger.info(f"File size: {file_size_kb:.2f} KB")
        return 0
    except (IOError, OSError) as e:
        logger.error(f"Error writing output file: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

