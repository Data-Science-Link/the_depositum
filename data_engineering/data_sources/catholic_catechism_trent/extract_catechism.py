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


def _extract_original_toc_from_raw(text: str) -> Tuple[str, str]:
    """Extract and preserve the original PDF table of contents from raw text.

    The original TOC is identified by finding the earliest and latest lines with 5+
    consecutive dots (.....) which indicate page number references. All lines between
    these boundaries (inclusive) are treated as TOC content, even if some lines don't
    have dots (e.g., when dots appear on the next line).
    This must be done BEFORE clean_text() removes the dots.

    Args:
        text: Raw text from PDF extraction (before cleaning)

    Returns:
        Tuple of (text_without_toc, original_toc_text)
    """
    lines = text.split('\n')

    # Pattern to match lines with 5+ consecutive dots (TOC format)
    # Example: "Advantages of Terminating our Prayer with this Word................................................................346"
    dot_pattern = re.compile(r'\.{5,}')

    # Find the earliest line with dots (TOC start)
    toc_start = -1
    for i, line in enumerate(lines):
        if dot_pattern.search(line):
            toc_start = i
            break

    # Find the latest line with dots (TOC end)
    toc_end = -1
    for i in range(len(lines) - 1, -1, -1):
        if dot_pattern.search(lines[i]):
            toc_end = i
            break

    # Extract TOC section if both boundaries found
    if toc_start >= 0 and toc_end >= toc_start:
        toc_lines = lines[toc_start:toc_end + 1]  # Inclusive range
        original_toc = '\n'.join(toc_lines)

        # Remove TOC from main text
        text_without_toc_lines = lines[:toc_start] + lines[toc_end + 1:]
        text_without_toc = '\n'.join(text_without_toc_lines)

        logger.info(f"Extracted original PDF table of contents (lines {toc_start}-{toc_end}, {len(toc_lines)} lines total)")
        return text_without_toc, original_toc

    # If no TOC boundaries found, return original text
    logger.warning("Could not detect original PDF table of contents (no lines with 5+ consecutive dots)")
    return text, ""


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


def _get_section_context(lines: List[str], current_idx: int) -> Tuple[str, int]:
    """Determine the current section context by looking backwards for structural headers.

    Returns: (context_type, header_level) where:
    - context_type: 'intro', 'part', 'article', 'level2_section', or 'none'
    - header_level: The level of the most recent structural header found
    """
    # Look backwards for the most recent structural header
    for i in range(current_idx - 1, -1, -1):
        line = lines[i].strip()
        if not line:
            continue

        # Check if it's a formatted header
        if line.startswith('#'):
            header_level = len(line) - len(line.lstrip('#'))
            header_text = line.lstrip('#').strip()

            # Check for INTRODUCTORY (Level 1)
            if re.match(r'^INTRODUCTORY', header_text, re.IGNORECASE):
                return ('intro', header_level)
            # Check for PART (Level 1)
            if re.match(r'^PART\s+[IVX]+', header_text, re.IGNORECASE):
                return ('part', header_level)
            # Check for ARTICLE (Level 2)
            if re.match(r'^ARTICLE\s+[IVX]+', header_text, re.IGNORECASE):
                return ('article', header_level)
            # Check for Level 2 sections like "THE SACRAMENTS", "THE SACRAMENT OF..."
            if header_level == 2:
                if re.match(r'^THE\s+SACRAMENT', header_text, re.IGNORECASE):
                    return ('level2_section', header_level)
        # Also check unformatted structural markers
        elif re.match(r'^INTRODUCTORY', line, re.IGNORECASE):
            return ('intro', 1)
        elif re.match(r'^PART\s+[IVX]+', line, re.IGNORECASE):
            return ('part', 1)
        elif re.match(r'^ARTICLE\s+[IVX]+', line, re.IGNORECASE):
            return ('article', 2)
        elif re.match(r'^THE\s+SACRAMENT', line, re.IGNORECASE):
            return ('level2_section', 2)

    return ('none', 0)


def _format_italicized_headers(text: str, italicized_texts: List[str]) -> str:
    """Format italicized lines as headers using hierarchy-aware rules.

    Formulaic approach:
    - Determine header level based on section context:
      - Under INTRODUCTORY or PART → `##` (Level 2)
      - Under ARTICLE or Level 2 section → `###` (Level 3)
      - Default/unknown → `####` (Level 4)
    - Only format lines that are reasonable header length (5-150 chars)
    - Must be followed by substantial content
    - Exclude lines that look like sentences
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
    level_counts = {'##': 0, '###': 0, '####': 0}

    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue

        # Normalize the line for comparison
        normalized_line = ' '.join(stripped.split())
        normalized_line_no_punct = normalized_line.rstrip('.,:;!?')

        # Check for exact or substring match
        matched_italic = None
        for norm_italic, orig_italic in italicized_normalized.items():
            norm_italic_no_punct = norm_italic.rstrip('.,:;!?')

            # Exact match
            if normalized_line == norm_italic or normalized_line_no_punct == norm_italic_no_punct:
                matched_italic = orig_italic
                break
            # Substring match
            min_length = 5 if len(normalized_line) <= 15 else 15
            if (norm_italic in normalized_line and len(norm_italic) >= min_length) or \
               (normalized_line in norm_italic and len(normalized_line) >= min_length) or \
               (norm_italic_no_punct in normalized_line_no_punct and len(norm_italic_no_punct) >= min_length) or \
               (normalized_line_no_punct in norm_italic_no_punct and len(normalized_line_no_punct) >= min_length):
                if not matched_italic or len(norm_italic) > len(matched_italic):
                    matched_italic = orig_italic

        if matched_italic:
            # Validation: reasonable header characteristics
            if not (5 <= len(stripped) <= 150):
                continue

            word_count = len(stripped.split())
            if (stripped.endswith(('.', ',', ';')) and word_count > 8) or word_count > 20:
                continue

            # Determine header level based on context
            context_type, parent_level = _get_section_context(lines, i)

            # Hierarchy rules:
            # - Under INTRODUCTORY or PART (Level 1) → Level 2
            # - Under ARTICLE or Level 2 section (Level 2) → Level 3
            # - Under Level 3 section → Level 4
            # - Unknown → Level 4 (default)
            if context_type in ('intro', 'part'):
                header_level = '##'  # Level 2 (under Level 1)
            elif context_type in ('article', 'level2_section'):
                header_level = '###'  # Level 3 (under Level 2)
            elif parent_level == 3:
                header_level = '####'  # Level 4 (under Level 3)
            else:
                header_level = '####'  # Level 4 (default/deeper subsections)

            # Check if followed by substantial content
            is_short_header = 5 <= len(stripped) <= 15
            next_idx = _find_next_content_line(lines, i)
            if next_idx:
                next_line = lines[next_idx].strip()
                min_next_length = 10 if is_short_header else 15
                if len(next_line) > min_next_length and not next_line.startswith('#'):
                    lines[i] = f"{header_level} {stripped}"
                    formatted_count += 1
                    level_counts[header_level] += 1
            elif is_short_header:
                lines[i] = f"{header_level} {stripped}"
                formatted_count += 1
                level_counts[header_level] += 1

    if formatted_count > 0:
        logger.info(f"Formatted {formatted_count} italicized lines as headers: "
                   f"{level_counts['##']} Level 2, {level_counts['###']} Level 3, {level_counts['####']} Level 4")

    return '\n'.join(lines)


def _split_merged_headers(text: str) -> str:
    """Split merged headers that appear on a single line.

    PDF extraction sometimes merges multiple headers into one line.
    This function identifies and splits them based on common patterns.

    CRITICAL: This function only adds line breaks. It NEVER removes content.

    Args:
        text: Text that may contain merged headers

    Returns:
        Text with merged headers split into separate lines
    """
    lines = text.split('\n')
    result_lines = []

    for line in lines:
        stripped = line.strip()

        # Skip empty lines
        if not stripped:
            result_lines.append(line)
            continue

        # Pattern 1: Multiple all-caps section titles merged (before formatting)
        # Example: "PREFACE ORIGIN OF THE ROMAN CATECHISM AUTHORITY AND EXCELLENCE..."
        if not stripped.startswith('#') and re.match(r'^[A-Z\s]+$', stripped) and len(stripped.split()) > 8:
            # Try to split on known section boundaries
            # Look for patterns like "ORIGIN OF", "AUTHORITY AND", "EXCELLENCE OF"
            words = stripped.split()
            sections = []
            current_section = []

            # Known section starter patterns
            section_markers = ['ORIGIN', 'AUTHORITY', 'EXCELLENCE', 'CATECHISM', 'NECESSITY',
                             'NATURE', 'ENDS', 'MEANING', 'IMPORTANCE', 'ADVANTAGES']

            i = 0
            while i < len(words):
                word = words[i]
                current_section.append(word)

                # Check if next word might start a new section
                if i + 1 < len(words):
                    next_word = words[i + 1]
                    # If current word is a section marker and we have a reasonable section length
                    if word in section_markers and len(current_section) >= 3:
                        # Check if this looks like end of section
                        if next_word in ['OF', 'AND', 'THE'] and len(current_section) >= 4:
                            sections.append(' '.join(current_section))
                            current_section = []

                i += 1

            # Add remaining
            if current_section:
                sections.append(' '.join(current_section))

            # Only split if we found 2-4 reasonable sections
            if 2 <= len(sections) <= 4 and all(3 <= len(s.split()) <= 12 for s in sections):
                result_lines.extend([f"## {section}" for section in sections])
                continue

        # Pattern 2: Multiple title-case subsection headers merged
        # Example: "Meaning Of This Article Importance Of This Article"
        if not stripped.startswith('#') and len(stripped.split()) > 8:
            words = stripped.split()
            phrases = []
            current_phrase = []

            for i, word in enumerate(words):
                # Title case word (capital first letter)
                is_capital = word and word[0].isupper()

                if is_capital:
                    # Check if this might start a new phrase
                    if current_phrase:
                        # Common phrase endings that suggest completion
                        last_word = current_phrase[-1].upper()
                        if last_word in ['ARTICLE', 'COMMANDMENT', 'SACRAMENT', 'THIS', 'THAT', 'THESE', 'THOSE']:
                            if len(current_phrase) >= 2:
                                phrases.append(' '.join(current_phrase))
                                current_phrase = [word]
                            else:
                                current_phrase.append(word)
                        else:
                            current_phrase.append(word)
                    else:
                        current_phrase.append(word)
                else:
                    if current_phrase:
                        current_phrase.append(word)

            if current_phrase and len(current_phrase) >= 2:
                phrases.append(' '.join(current_phrase))

            # Only split if we found 2-4 reasonable phrases
            if 2 <= len(phrases) <= 4 and all(2 <= len(p.split()) <= 8 for p in phrases):
                result_lines.extend([f"#### {phrase}" for phrase in phrases])
                continue

        result_lines.append(line)

    return '\n'.join(result_lines)


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


def _generate_table_of_contents(text: str) -> str:
    """Generate a table of contents from markdown headers.

    Extracts all headers (## and above) and creates a TOC with proper indentation.
    Includes copyright/introduction and preface sections.

    Args:
        text: Markdown text with headers

    Returns:
        Table of contents as markdown list
    """
    lines = text.split('\n')
    toc_items = []

    # Skip the TOC header itself and the original TOC comment block
    skip_until_content = True
    in_original_toc_comment = False

    for line in lines:
        stripped = line.strip()

        # Skip until we're past the TOC section and original TOC comment
        if skip_until_content:
            if stripped == "## Table of Contents":
                continue
            if stripped.startswith("<!--"):
                in_original_toc_comment = True
                continue
            if in_original_toc_comment:
                if stripped.startswith("-->"):
                    in_original_toc_comment = False
                continue
            # Start including headers once we're past the TOC sections
            if stripped.startswith("##") and not in_original_toc_comment:
                skip_until_content = False

        # Extract headers (now including all sections)
        header_match = re.match(r'^(#+)\s+(.+)$', stripped)
        if header_match:
            level = len(header_match.group(1))
            title = header_match.group(2).strip()

            # Only include ## and ### headers in TOC (skip ####)
            if level <= 3:
                # Create anchor-friendly link
                anchor = re.sub(r'[^\w\s-]', '', title).strip()
                anchor = re.sub(r'[-\s]+', '-', anchor).lower()

                indent = '  ' * (level - 1)
                toc_items.append(f"{indent}- [{title}](#{anchor})")

    if not toc_items:
        return ""

    return "## Table of Contents\n\n" + "\n".join(toc_items) + "\n"


def _format_copyright_section(text: str) -> str:
    """Format the copyright notice and introduction section with a header and regular text.

    Finds the section from "The Catechism of the Council of Trent or (The Catechism for Parish Priests)"
    to "The translation and preface by John A. McHugh, O.P. and Charles J. Callan, O.P. (circa 1923)"
    and formats it with a header and regular text (removing blockquotes and header markers).

    Args:
        text: Text that may contain copyright notice

    Returns:
        Text with copyright section formatted with header and regular text
    """
    lines = text.split('\n')
    copyright_start = -1
    copyright_end = -1

    # Find the start: "The Catechism of the Council of Trent" or similar
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Look for the title line
        if 'THE CATECHISM OF THE COUNCIL OF TRENT' in stripped.upper() or \
           (stripped.upper().startswith('THE CATECHISM') and 'TRENT' in stripped.upper()):
            copyright_start = i
            break

    # Find the end: "The translation and preface by John A. McHugh, O.P. and Charles J. Callan, O.P. (circa 1923)"
    if copyright_start >= 0:
        for i in range(copyright_start, len(lines)):
            stripped = lines[i].strip()
            # Look for the translation line
            if 'JOHN A. MCHUGH' in stripped.upper() and 'CHARLES J. CALLAN' in stripped.upper() and \
               ('CIRCA 1923' in stripped.upper() or '1923' in stripped):
                copyright_end = i + 1  # Include this line
                break

    # If we found both boundaries, format the section
    if copyright_start >= 0 and copyright_end > copyright_start:
        result_lines = []

        # Add lines before copyright section
        result_lines.extend(lines[:copyright_start])

        # Add header
        result_lines.append('## Copyright and Introduction to the Document')
        result_lines.append('')

        # Process copyright section lines: remove blockquotes, headers, and format as regular text
        for i in range(copyright_start, copyright_end):
            line = lines[i]
            stripped = line.strip()

            # Skip empty lines (we'll add them back if needed)
            if not stripped:
                result_lines.append('')
                continue

            # Remove blockquote markers
            if stripped.startswith('>'):
                stripped = stripped[1:].strip()

            # Remove header markers (####)
            if stripped.startswith('####'):
                stripped = stripped[4:].strip()
            elif stripped.startswith('###'):
                stripped = stripped[3:].strip()
            elif stripped.startswith('##'):
                stripped = stripped[2:].strip()
            elif stripped.startswith('#'):
                stripped = stripped[1:].strip()

            # Add the cleaned line
            result_lines.append(stripped)

        # Add lines after copyright section
        result_lines.extend(lines[copyright_end:])

        return '\n'.join(result_lines)

    # If we couldn't find the section, return original text
    return text


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

    # Step 1.5: Split merged headers (multiple headers on one line)
    text = _split_merged_headers(text)

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

        # Level 1: INTRODUCTORY (should be Level 1, not Level 2)
        if re.match(r'^INTRODUCTORY(?:\s|$)', stripped, re.IGNORECASE):
            lines[i] = f"# {stripped}"
            continue

        # Level 2: All-caps structural words (PREFACE, etc.) - but not INTRODUCTORY (handled above)
        # Only if the entire line is all-caps (2+ chars) or starts with all-caps word
        if re.match(r'^[A-Z]{2,}(?:\s|$)', stripped):
            # Check if it's a known structural word or a short all-caps phrase
            # Skip INTRODUCTORY as it's already handled above
            if stripped.upper() != 'INTRODUCTORY' and len(stripped.split()) <= 5 and stripped.isupper():
                lines[i] = f"## {stripped}"
                continue

        # First, check if line contains multiple potential headers merged together
        # (e.g., "Circumstances of the Judgment: The Judge")
        if ':' in stripped and len(stripped.split(':')) == 2:
            parts = stripped.split(':', 1)
            first_part = parts[0].strip() + ':'
            second_part = parts[1].strip()
            # Check if second part looks like a separate header (short, title case)
            if second_part and 3 <= len(second_part) <= 20:
                second_words = second_part.split()
                if len(second_words) <= 4 and all(w[0].isupper() for w in second_words if w):
                    # Check if first part also looks like a header
                    first_words = first_part.rstrip(':').strip().split()
                    lowercase_words = {'of', 'the', 'and', 'or', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'with', 'by'}
                    significant_first = [w for w in first_words if w.lower() not in lowercase_words]
                    if significant_first and all(w[0].isupper() for w in significant_first if w) and 2 <= len(first_words) <= 8:
                        # Split into two separate headers
                        lines[i] = f"#### {first_part}"
                        # Insert the second header on the next line
                        lines.insert(i + 1, f"#### {second_part}")
                        continue

        # Pattern-based detection for common header patterns that might not be detected as italicized
        # Title-case phrases ending with colon (e.g., "Circumstances of the Judgment:")
        # Pattern: Starts with capital, ends with colon, has reasonable length
        if stripped.endswith(':') and len(stripped) >= 10 and len(stripped) <= 80:
            words = stripped.rstrip(':').strip().split()
            # Common lowercase words that are acceptable in title case
            lowercase_words = {'of', 'the', 'and', 'or', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'with', 'by'}
            # Check if it looks like a header (2-8 words)
            if 2 <= len(words) <= 8:
                # Check if first word and significant words are capitalized
                # Allow lowercase words like "of", "the", etc.
                significant_words = [w for w in words if w.lower() not in lowercase_words]
                if significant_words and all(w[0].isupper() for w in significant_words if w):
                    # Check if next line has content (it's a header)
                    next_idx = _find_next_content_line(lines, i)
                    if next_idx:
                        next_line = lines[next_idx].strip()
                        # Format if next line has substantial content (not just another short header)
                        # If next line is a short header (like "The Judge"), format this one too
                        # but keep them separate
                        if (len(next_line) > 10 and not next_line.startswith('#')) or \
                           (next_line.startswith('####') and 5 <= len(next_line.replace('####', '').strip()) <= 15):
                            # Format this line, but don't merge with next
                            lines[i] = f"#### {stripped.rstrip()}"
                            continue

    # Step 4: Merge consecutive header lines (e.g., multi-line ARTICLE headers)
    lines = _merge_consecutive_headers(lines)

    text = '\n'.join(lines)

    # Step 5: Clean up formatting artifacts
    # Remove page numbers from headers
    text = re.sub(r'(#+\s+[^#\n]+?)(\d{1,3})(\s|$)', r'\1\3', text, flags=re.MULTILINE)

    # Step 6: Post-process to split remaining merged headers in formatted text
    lines = text.split('\n')
    result_lines = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Check for merged ## headers (multiple section titles)
        if stripped.startswith('##') and not stripped.startswith('###'):
            header_text = stripped[2:].strip()

            # Pattern: Multiple all-caps section titles merged
            # Example: "PREFACE ORIGIN OF THE ROMAN CATECHISM AUTHORITY AND EXCELLENCE..."
            if len(header_text.split()) > 10 and header_text.isupper():
                # Split on specific known patterns
                # Pattern 1: "PREFACE" followed by "ORIGIN OF THE ROMAN CATECHISM"
                if 'PREFACE' in header_text and 'ORIGIN' in header_text:
                    # Try to split at "ORIGIN"
                    idx = header_text.find('ORIGIN')
                    if idx > 0:
                        part1 = header_text[:idx].strip()
                        part2 = header_text[idx:].strip()
                        # Further split part2 if it contains "AUTHORITY"
                        if 'AUTHORITY' in part2:
                            idx2 = part2.find('AUTHORITY')
                            if idx2 > 0:
                                part2a = part2[:idx2].strip()
                                part2b = part2[idx2:].strip()
                                # Check if part2b contains "EXCELLENCE"
                                if 'EXCELLENCE' in part2b:
                                    idx3 = part2b.find('EXCELLENCE')
                                    if idx3 > 0:
                                        part2b1 = part2b[:idx3].strip()
                                        part2b2 = part2b[idx3:].strip()
                                        # Split into: PREFACE, ORIGIN..., AUTHORITY..., EXCELLENCE...
                                        parts = [part1, part2a, part2b1, part2b2]
                                        if all(3 <= len(p.split()) <= 15 for p in parts):
                                            result_lines.extend([f"## {p}" for p in parts])
                                            continue
                                else:
                                    parts = [part1, part2a, part2b]
                                    if all(3 <= len(p.split()) <= 15 for p in parts):
                                        result_lines.extend([f"## {p}" for p in parts])
                                        continue
                            else:
                                parts = [part1, part2]
                                if all(3 <= len(p.split()) <= 20 for p in parts):
                                    result_lines.extend([f"## {p}" for p in parts])
                                    continue

        # Check for merged #### headers (multiple subsection titles)
        if stripped.startswith('####'):
            header_text = stripped[4:].strip()

            # Pattern 1: Title-case phrase ending with colon followed by short title-case phrase
            # Example: "Circumstances of the Judgment: The Judge"
            if ':' in header_text and len(header_text.split(':')) == 2:
                parts = header_text.split(':', 1)
                first_part = parts[0].strip() + ':'
                second_part = parts[1].strip()
                # Check if second part looks like a separate header (short, title case, 2-4 words)
                if second_part and 3 <= len(second_part) <= 20:
                    second_words = second_part.split()
                    if 1 <= len(second_words) <= 4 and all(w[0].isupper() for w in second_words if w):
                        # Check if first part also looks like a header (title case, reasonable length)
                        first_words = first_part.rstrip(':').strip().split()
                        lowercase_words = {'of', 'the', 'and', 'or', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'with', 'by'}
                        significant_first = [w for w in first_words if w.lower() not in lowercase_words]
                        if significant_first and all(w[0].isupper() for w in significant_first if w) and 2 <= len(first_words) <= 8:
                            # Split into two separate headers
                            result_lines.append(f"#### {first_part}")
                            result_lines.append(f"#### {second_part}")
                            continue

            # Pattern 2: Multiple title-case phrases merged
            # Example: "Meaning Of This Article Importance Of This Article"
            if len(header_text.split()) > 10:
                # Look for repeated patterns like "Of This Article", "Of The", etc.
                words = header_text.split()
                phrases = []
                current_phrase = []

                # Common phrase endings that indicate completion
                phrase_endings = ['Article', 'Commandment', 'Sacrament', 'This', 'That', 'These', 'Those']

                i_word = 0
                while i_word < len(words):
                    word = words[i_word]
                    current_phrase.append(word)

                    # Check if this word might end a phrase
                    if word in phrase_endings and len(current_phrase) >= 3:
                        # Check if next word starts with capital (new phrase)
                        if i_word + 1 < len(words) and words[i_word + 1][0].isupper():
                            phrases.append(' '.join(current_phrase))
                            current_phrase = []

                    i_word += 1

                if current_phrase and len(current_phrase) >= 2:
                    phrases.append(' '.join(current_phrase))

                # Only split if we found 2-4 reasonable phrases
                if 2 <= len(phrases) <= 4 and all(2 <= len(p.split()) <= 10 for p in phrases):
                    result_lines.extend([f"#### {phrase}" for phrase in phrases])
                    continue

        result_lines.append(line)

    text = '\n'.join(result_lines)

    # Step 7: Improve spacing - ensure blank lines around headers
    lines = text.split('\n')
    result_lines = []

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Add blank line before headers (except at start of file)
        if stripped.startswith('#') and i > 0:
            prev_line = result_lines[-1] if result_lines else ''
            if prev_line.strip() and not prev_line.strip().startswith('>'):
                result_lines.append('')

        result_lines.append(line)

        # Add blank line after headers if next line is not empty and not a header
        if stripped.startswith('#') and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line and not next_line.startswith('#') and not next_line.startswith('>'):
                result_lines.append('')

    text = '\n'.join(result_lines)

    # Normalize excessive line breaks (max 2 consecutive)
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

    # Extract original PDF table of contents BEFORE cleaning (dots will be removed by clean_text)
    logger.info("Extracting original PDF table of contents...")
    text_without_toc, original_toc = _extract_original_toc_from_raw(text_content)

    # Clean the text (excluding the original TOC which we'll preserve as-is)
    clean_content = clean_text(text_without_toc)

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

    # Format copyright section
    final_content = _format_copyright_section(final_content)

    # Generate table of contents
    logger.info("Generating table of contents...")
    toc = _generate_table_of_contents(final_content)

    # Write output file with frontmatter
    try:
        with open(OUTPUT_FILEPATH, 'w', encoding='utf-8') as f:
            # Enhanced frontmatter
            f.write("---\n")
            f.write("title: Catechism of the Council of Trent (McHugh & Callan Translation)\n")
            f.write("subtitle: The Roman Catechism / Catechism of Pius V\n")
            f.write("authors:\n")
            f.write("  - name: John A. McHugh, O.P.\n")
            f.write("  - name: Charles J. Callan, O.P.\n")
            f.write("translation_date: 1923\n")
            f.write("source: SaintsBooks.net\n")
            f.write("tags:\n")
            f.write("  - catechism\n")
            f.write("  - council-of-trent\n")
            f.write("  - mchugh-callan\n")
            f.write("  - magisterium\n")
            f.write("  - roman-catechism\n")
            f.write("language: en\n")
            f.write("format: markdown\n")
            f.write("---\n\n")

            # Table of contents (dynamically generated from detected headers)
            if toc:
                f.write(toc)
                f.write("\n")

            # Original PDF table of contents (preserved as-is, commented out)
            # NOTE: The table of contents above is the correct, dynamically generated one.
            # The section below is the original PDF table of contents preserved for reference only.
            if original_toc:
                f.write("<!--\n")
                f.write("ORIGINAL PDF TABLE OF CONTENTS (PRESERVED FOR REFERENCE)\n")
                f.write("========================================================\n")
                f.write("NOTE: The table of contents above is the correct, dynamically generated one.\n")
                f.write("This section below is the original PDF table of contents preserved as-is.\n")
                f.write("========================================================\n\n")
                # Write the original TOC exactly as extracted (no cleaning, no formatting)
                f.write(original_toc)
                f.write("\n-->\n\n")

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

