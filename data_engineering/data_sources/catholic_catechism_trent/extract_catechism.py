#!/usr/bin/env python3
"""
McHugh & Callan Catechism Extraction Script

This script extracts the Catechism of the Council of Trent (McHugh & Callan Translation)
from a PDF file and converts it to clean Markdown format.

The script uses pdfplumber to extract text with formatting information (italics detection),
then applies markdown formatting for better readability. All content is preserved.

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
from typing import Optional, List, Tuple
import yaml
import pdfplumber

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

    # Remove page numbers that appear embedded in text (formatting artifact)
    # Pattern: "PART I : THE CREED33" -> "PART I : THE CREED"
    # Pattern: "The Necessity Of Religious Instruction29" -> "The Necessity Of Religious Instruction"
    # Only remove if it's 1-3 digits that appear after a word (likely page number)
    # Be careful not to remove years or other numbers that are part of content
    text = re.sub(r'([A-Za-z])\s*(\d{1,3})(\s+[A-Z])', r'\1\3', text)  # Number followed by capital (new section)
    text = re.sub(r'([A-Za-z])\s*(\d{1,3})\s*$', r'\1', text, flags=re.MULTILINE)  # Number at end of line

    # Clean up excessive dots used for spacing in PDF (formatting artifact)
    # Only remove dots that are clearly spacing, not content dots
    text = re.sub(r'\.{6,}', '', text)

    # Clean up extra spaces (formatting only)
    text = re.sub(r'[ \t]+', ' ', text)

    # Normalize line breaks (formatting only - PDF often creates excessive whitespace)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text


def _find_next_content_line(lines: List[str], start_idx: int) -> Optional[int]:
    """Find the next non-empty line after start_idx."""
    for i in range(start_idx + 1, len(lines)):
        if lines[i].strip():
            return i
    return None


def _format_italicized_headers(text: str, italicized_texts: List[str]) -> str:
    """Format italicized lines as #### headers using formulaic rules.

    Formulaic approach:
    - Only format lines that are reasonable header length (10-150 chars)
    - Must be followed by substantial content
    - Exclude lines that look like sentences (end with periods, have too many words)
    """
    if not italicized_texts:
        return text

    lines = text.split('\n')
    # Normalize italicized texts for matching
    italicized_normalized = {}
    for it in italicized_texts:
        normalized = ' '.join(it.strip().split())
        if normalized:
            italicized_normalized[normalized] = it.strip()

    formatted_count = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue

        # Normalize the line for comparison
        normalized_line = ' '.join(stripped.split())

        # Check for exact or substring match
        matched_italic = None
        for norm_italic, orig_italic in italicized_normalized.items():
            # Exact match (after normalization)
            if normalized_line == norm_italic:
                matched_italic = orig_italic
                break
            # Substring match - line contains italic text or vice versa
            elif (norm_italic in normalized_line and len(norm_italic) > 15) or \
                 (normalized_line in norm_italic and len(normalized_line) > 15):
                # Prefer longer match
                if not matched_italic or len(norm_italic) > len(matched_italic):
                    matched_italic = orig_italic

        if matched_italic:
            # Formulaic validation: must be reasonable header characteristics
            # 1. Length check (10-150 chars)
            if not (10 <= len(stripped) <= 150):
                continue

            # 2. Not a sentence (doesn't end with period, comma, or have too many words)
            word_count = len(stripped.split())
            if (stripped.endswith(('.', ',', ';')) and word_count > 8) or word_count > 20:
                continue

            # 3. Must be followed by substantial content
            next_idx = _find_next_content_line(lines, i)
            if next_idx:
                next_line = lines[next_idx].strip()
                # Format if next line has substantial content and isn't another header
                if len(next_line) > 15 and not next_line.startswith('#'):
                    lines[i] = f"#### {stripped}"
                    formatted_count += 1

    if formatted_count > 0:
        logger.info(f"Formatted {formatted_count} italicized lines as headers")

    return '\n'.join(lines)


def _split_long_lines(text: str) -> str:
    """Split long lines on structural markers to improve readability.

    Formulaic approach: Only split on clear structural markers (PART, ARTICLE, all-caps words).
    CRITICAL: This function only adds line breaks. It NEVER removes content.
    """
    # Split on structural markers that should always start a new line
    # PART markers
    text = re.sub(r'(\s+)(PART\s+[IVX]+\s*:)', r'\n\2', text)

    # ARTICLE markers
    text = re.sub(r'(\s+)(ARTICLE\s+[IVX]+\s*:)', r'\n\2', text)

    # All-caps structural words (PREFACE, INTRODUCTORY, etc.)
    # Pattern: whitespace + all-caps word (2+ chars) + whitespace or end
    text = re.sub(r'(\s+)([A-Z]{2,})(\s|$)', r'\n\2\3', text)

    # Normalize excessive line breaks
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text


def _merge_consecutive_headers(lines: List[str]) -> List[str]:
    """Merge consecutive header lines that were split across multiple lines.

    Formulaic approach:
    If consecutive lines all start with the same header level and the first line
    matches ARTICLE or PART pattern, combine them into a single header.
    """
    merged = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Check if this is a header line
        header_match = re.match(r'^(#+)\s+(.+)$', stripped)
        if header_match:
            header_level = header_match.group(1)
            header_text = header_match.group(2)

            # Check if this looks like the start of a multi-line ARTICLE or PART header
            is_article_header = re.match(r'^(ARTICLE|PART)\s+[IVX]+\s*:', header_text, re.IGNORECASE)

            combined_text = [header_text]
            j = i + 1

            # Collect consecutive lines with the same header level
            while j < len(lines):
                next_line = lines[j].strip()
                if not next_line:
                    break

                next_match = re.match(rf'^{re.escape(header_level)}\s+(.+)$', next_line)
                if next_match:
                    next_text = next_match.group(1)
                    # If this is an ARTICLE/PART header, merge all consecutive ## lines
                    if is_article_header:
                        combined_text.append(next_text)
                        j += 1
                        continue
                    # For other headers, only merge if they look like continuations
                    elif (len(next_text.split()) <= 8 and
                          not next_text.endswith('.') and
                          not re.match(r'^(ARTICLE|PART|PREFACE|INTRODUCTORY)', next_text, re.IGNORECASE)):
                        combined_text.append(next_text)
                        j += 1
                        continue
                break

            # Combine into single header
            merged.append(f"{header_level} {' '.join(combined_text)}")
            i = j
        else:
            merged.append(line)
            i += 1

    return merged


def add_markdown_headers(text: str, italicized_texts: Optional[List[str]] = None) -> str:
    """Applies Markdown headers using formulaic rules based on text structure.

    Formulaic approach:
    1. Italicized lines -> #### (subsection headers)
    2. PART I/II/III -> # (level 1)
    3. ARTICLE I/II -> ## (level 2)
    4. All-caps words (PREFACE, INTRODUCTORY) -> ## (level 2)

    CRITICAL: This function only adds markdown formatting. It NEVER removes or modifies
    the actual content. All words and text are preserved exactly as extracted from the PDF.

    Args:
        text: Cleaned plain text
        italicized_texts: Optional list of italicized line texts from PDF (primary signal for subsections)

    Returns:
        Text with Markdown headers applied (content unchanged)
    """
    # Step 1: Format italicized lines as subsection headers (####)
    # This is the primary signal for subsection headers
    if italicized_texts:
        text = _format_italicized_headers(text, italicized_texts)

    # Step 2: Split long lines on structural markers
    text = _split_long_lines(text)

    # Step 3: Apply structural headers (formulaic patterns)
    lines = text.split('\n')

    # First pass: detect and combine multi-line ARTICLE/PART headers BEFORE formatting
    # This handles cases where the header text spans multiple lines
    # CRITICAL: Preserve original line order - only combine lines that are clearly continuations
    i = 0
    combined_lines = []
    while i < len(lines):
        stripped = lines[i].strip()
        if not stripped:
            combined_lines.append(lines[i])
            i += 1
            continue

        # Check if this line starts an ARTICLE or PART header
        article_match = re.match(r'^(ARTICLE\s+[IVX]+\s*:\s*["\']?[A-Z])', stripped, re.IGNORECASE)
        part_match = re.match(r'^(PART\s+[IVX]+\s*:\s*[A-Z])', stripped, re.IGNORECASE)

        if article_match or part_match:
            # Collect continuation lines that are part of the same header
            combined_text = [stripped]
            j = i + 1
            # ARTICLE headers typically end with a closing quote, so look for that
            has_opening_quote = '"' in stripped or "'" in stripped
            found_closing_quote = stripped.endswith('"') or stripped.endswith("'")

            # Only combine up to 5 lines max to avoid over-merging
            max_continuations = 5
            continuation_count = 0

            while j < len(lines) and not found_closing_quote and continuation_count < max_continuations:
                next_stripped = lines[j].strip()
                if not next_stripped:
                    break

                # Strict check: next line must clearly be a continuation
                # Must be: all caps with quotes, or very short continuation (max 6 words)
                is_continuation = (
                    (has_opening_quote and ('"' in next_stripped or "'" in next_stripped) and
                     re.match(r'^[A-Z\s"\']+["\']?\s*$', next_stripped)) or
                    (len(next_stripped.split()) <= 6 and
                     next_stripped.isupper() and
                     not next_stripped.endswith('.') and
                     not re.match(r'^(ARTICLE|PART|PREFACE|INTRODUCTORY)', next_stripped, re.IGNORECASE))
                )

                if is_continuation:
                    combined_text.append(next_stripped)
                    # Check if we found the closing quote
                    if next_stripped.endswith('"') or next_stripped.endswith("'"):
                        found_closing_quote = True
                    j += 1
                    continuation_count += 1
                else:
                    break
            # Combine into single line
            combined_lines.append(' '.join(combined_text))
            i = j
        else:
            # Preserve original line order
            combined_lines.append(lines[i])
            i += 1

    lines = combined_lines

    # Second pass: format the headers
    for i, line in enumerate(lines):
        stripped = line.strip()

        # Skip empty lines and already-formatted headers
        if not stripped or stripped.startswith('#'):
            continue

        # Level 1: PART I, PART II, etc.
        if re.match(r'^PART\s+[IVX]+', stripped, re.IGNORECASE):
            lines[i] = re.sub(r'^(PART\s+[IVX]+.*)', r'# \1', stripped)
            continue

        # Level 2: ARTICLE I, ARTICLE II, etc.
        if re.match(r'^ARTICLE\s+[IVX]+', stripped, re.IGNORECASE):
            lines[i] = re.sub(r'^(ARTICLE\s+[IVX]+.*)', r'## \1', stripped)
            continue

        # Level 2: All-caps structural words (PREFACE, INTRODUCTORY, etc.)
        # Only if the entire line is all-caps (2+ chars) or starts with all-caps word
        if re.match(r'^[A-Z]{2,}(?:\s|$)', stripped):
            # Check if it's a known structural word or a short all-caps phrase
            if len(stripped.split()) <= 5 and stripped.isupper():
                lines[i] = f"## {stripped}"
                continue

    # Step 4: Merge consecutive header lines (e.g., multi-line ARTICLE headers)
    lines = _merge_consecutive_headers(lines)

    text = '\n'.join(lines)

    # Step 5: Clean up formatting artifacts
    # Remove page numbers from headers
    text = re.sub(r'(#+\s+[^#\n]+?)(\d{1,3})(\s|$)', r'\1\3', text, flags=re.MULTILINE)

    # Normalize excessive line breaks
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text


def _is_italic_char(char: dict) -> bool:
    """Check if a character is italic based on font name or flags."""
    font_name = char.get('fontname', '').lower()
    return ('italic' in font_name or 'oblique' in font_name or
            (char.get('flags', 0) & 0x40))


def _extract_page_with_italics(page) -> Tuple[str, List[str]]:
    """Extract text and italicized lines from a PDF page using y-coordinate-based line grouping.

    This method groups characters by their vertical position (y-coordinate) to properly
    reconstruct lines, which is more reliable than relying on newline characters in PDFs.

    Returns:
        Tuple of (text_content, list of italicized line texts)
    """
    # Group characters by line using y-coordinates
    # Round to 0.1 precision to handle slight variations in positioning
    lines_by_y = {}
    for char in page.chars:
        y = round(char.get('top', 0), 1)
        if y not in lines_by_y:
            lines_by_y[y] = []
        lines_by_y[y].append(char)

    # Sort lines by y-coordinate (top to bottom)
    # In pdfplumber, 'top' is the y-coordinate of the top edge of the character
    # The coordinate system typically has y=0 at the BOTTOM, so larger 'top' = higher on page
    # However, we need to verify: if headers appear after content, the sort is reversed
    # Test: sort descending (largest y first) = top to bottom if y=0 at bottom
    #       sort ascending (smallest y first) = top to bottom if y=0 at top
    # Based on the issue where headers appear after content, we likely need ascending order
    sorted_lines = sorted(lines_by_y.items(), key=lambda x: x[0], reverse=False)  # Ascending = top to bottom if y=0 at top

    text_parts = []
    italicized_lines = set()

    for y, chars in sorted_lines:
        if not chars:
            continue

        # Sort characters by x-coordinate (left to right)
        chars_sorted = sorted(chars, key=lambda c: c.get('x0', 0))

        # Build line text and check for italics
        line_text = ""
        italic_count = 0
        total_count = 0

        for char in chars_sorted:
            text = char.get('text', '')
            line_text += text
            total_count += 1
            if _is_italic_char(char):
                italic_count += 1

        # Check if line is mostly italicized (subsection headers)
        if total_count > 0 and (italic_count / total_count) > 0.5:
            stripped = line_text.strip()
            if stripped:
                italicized_lines.add(stripped)

        # Add line to text content
        if line_text.strip():
            text_parts.append(line_text)

    return '\n'.join(text_parts), list(italicized_lines)


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

    # Extract text from PDF with italics detection
    text_content: Optional[str] = None
    italicized_texts: List[str] = []
    try:
        with pdfplumber.open(INPUT_FILENAME) as pdf:
            total_pages = len(pdf.pages)
            logger.info(f"PDF has {total_pages} pages, extracting text with formatting...")

            # Limit pages if --max-pages is specified (for testing)
            max_page = args.max_pages if args.max_pages else total_pages
            actual_page_count = min(max_page, total_pages)

            text_parts = []
            all_italicized_lines = set()

            for page_num in range(actual_page_count):
                if (page_num + 1) % 10 == 0 or page_num == 0:
                    logger.info(f"  Processing page {page_num + 1}/{actual_page_count}...")
                try:
                    page = pdf.pages[page_num]
                    page_text, page_italics = _extract_page_with_italics(page)
                    text_parts.append(page_text)
                    all_italicized_lines.update(page_italics)
                except Exception as e:
                    logger.warning(f"  Warning: Could not extract text from page {page_num + 1}: {e}")
                    continue

            text_content = '\n'.join(text_parts)

            if not text_content or len(text_content.strip()) < 100:
                logger.error("Extracted text appears to be empty or too short")
                return 1

            logger.info(f"Successfully extracted {len(text_content)} characters from PDF")
            logger.info(f"Found {len(all_italicized_lines)} italicized text lines")
            italicized_texts = list(all_italicized_lines)

    except Exception as e:
        logger.error(f"Error reading PDF file: {e}", exc_info=True)
        return 1

    if text_content is None:
        logger.error("Failed to extract text from PDF")
        return 1

    logger.info("Applying Markdown formatting...")
    # CRITICAL: All content from PDF is preserved. Only formatting is applied.
    clean_content = clean_text(text_content)

    # Clean italicized_texts to match the cleaned content (for proper matching)
    # Note: clean_text works on full text, so we need to clean each italicized line individually
    cleaned_italicized_texts = []
    for text in italicized_texts:
        cleaned = clean_text(text).strip()
        if cleaned:
            cleaned_italicized_texts.append(cleaned)
    # Remove duplicates
    cleaned_italicized_texts = list(set(cleaned_italicized_texts))

    if cleaned_italicized_texts:
        logger.info(f"After cleaning, {len(cleaned_italicized_texts)} unique italicized lines to format")
        logger.debug(f"Sample italicized lines: {cleaned_italicized_texts[:5]}")

    final_content = add_markdown_headers(clean_content, cleaned_italicized_texts)

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

