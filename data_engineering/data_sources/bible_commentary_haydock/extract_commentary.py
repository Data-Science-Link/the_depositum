#!/usr/bin/env python3
"""
Haydock Catholic Bible Commentary Extraction Script

This script extracts the Haydock Catholic Bible Commentary (1859 Edition) from
an EPUB file and converts it to clean, well-structured Markdown format following
best practices for documentation and AI tool compatibility.

The script properly parses the EPUB's HTML structure:
- Identifies book and chapter boundaries
- Extracts verse-by-verse commentary
- Preserves Latin phrases and Hebrew transliterations
- Organizes content hierarchically
- Outputs directly to data_final/bible_commentary_haydock/

Prerequisites:
    - Download the EPUB file from Isidore E-Book Library
    - Place it in the data_sources/bible_commentary_haydock/ directory

Usage:
    python extract_commentary.py
"""

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
import yaml
import sys

# Add parent directory to path to import shared canonical_books module
canonical_books_path = Path(__file__).parent.parent
sys.path.insert(0, str(canonical_books_path))
from canonical_books import CATHOLIC_BIBLE_CANON, get_canonical_info

# Set up logging to both console and file
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "commentary_extraction.log"

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
try:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    INPUT_EPUB = Path(config['paths']['raw_data']['haydock'])
    OUTPUT_DIR = Path(config['paths']['final_output']['haydock'])
except Exception as e:
    logger.warning(f"Could not load config, using defaults: {e}")
    INPUT_EPUB = Path(__file__).parent / "Haydock Catholic Bible Comment - Haydock, George Leo_3948.epub"
    OUTPUT_DIR = Path(__file__).parent.parent.parent.parent / "data_final" / "bible_commentary_haydock"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def clean_text(text: str) -> str:
    """Cleans up extra whitespace and formatting artifacts.

    Args:
        text: Raw text string

    Returns:
        Cleaned text string with normalized whitespace
    """
    if not text:
        return ""
    # Normalize whitespace (multiple spaces/tabs/newlines to single space)
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove null bytes and other control characters (except newlines in markdown)
    text = text.replace('\x00', '')
    # Remove zero-width spaces
    text = text.replace('\u200b', '')
    text = text.replace('\u200c', '')
    text = text.replace('\u200d', '')
    return text


def extract_verse_number(text: str) -> Optional[int]:
    """Extracts verse number from text like 'Ver. 1.' or 'Ver. 12.'.

    Args:
        text: Text containing verse number

    Returns:
        Verse number as integer, or None if not found
    """
    match = re.search(r'Ver\.\s*(\d+)', text, re.IGNORECASE)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


def parse_chapter_header(text: str) -> Optional[Tuple[str, int]]:
    """Parses chapter header like 'GENESIS 19' into book name and chapter number.

    Args:
        text: Chapter header text

    Returns:
        Tuple of (book_name, chapter_number) or None if parsing fails
    """
    # Pattern: BOOK_NAME followed by optional whitespace and chapter number
    match = re.match(r'^([A-Z][A-Z\s]+?)\s+(\d+)$', text.strip())
    if match:
        book_name = match.group(1).strip()
        try:
            chapter_num = int(match.group(2))
            return (book_name, chapter_num)
        except ValueError:
            return None
    return None


def convert_html_to_markdown(element) -> str:
    """Converts HTML element to Markdown, preserving structure.

    This function handles:
    - Bold text (<strong>) -> **text**
    - Italic text (<em>) -> *text*
    - Paragraphs -> newlines
    - Preserves Latin phrases and Hebrew transliterations

    Args:
        element: BeautifulSoup element

    Returns:
        Markdown-formatted string
    """
    if element is None:
        return ""

    # Handle string content directly
    if isinstance(element, str):
        return clean_text(element)

    # Handle different tag types
    tag_name = element.name.lower() if hasattr(element, 'name') else None

    if tag_name == 'strong':
        text = ''.join(convert_html_to_markdown(child) for child in element.children)
        return f"**{clean_text(text)}**"
    elif tag_name == 'em':
        text = ''.join(convert_html_to_markdown(child) for child in element.children)
        return f"*{clean_text(text)}*"
    elif tag_name == 'p':
        text = ''.join(convert_html_to_markdown(child) for child in element.children)
        return clean_text(text)
    elif tag_name == 'span':
        # Preserve span content (often used for Hebrew transliterations)
        text = ''.join(convert_html_to_markdown(child) for child in element.children)
        return clean_text(text)
    else:
        # For other elements, extract text recursively
        text = ''.join(convert_html_to_markdown(child) for child in element.children)
        return clean_text(text)


def process_epub_content(book: epub.EpubBook) -> Dict[str, Dict[int, List[Dict[str, str]]]]:
    """Processes all HTML content from the EPUB file.

    Organizes commentary by book, then by chapter, then by verse.

    Args:
        book: EpubBook object from ebooklib

    Returns:
        Nested dictionary: {book_name: {chapter_num: [verse_commentaries]}}
        Each verse_commentary is a dict with 'verse' and 'commentary' keys
    """
    commentary_data = defaultdict(lambda: defaultdict(list))

    logger.info("Processing EPUB HTML content...")

    for item in book.get_items():
        if item.get_type() != ebooklib.ITEM_DOCUMENT:
            continue

        html_content = item.get_content()
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find all resource text divs
        resource_divs = soup.find_all('div', class_='resourcetext')

        for div in resource_divs:
            current_book = None
            current_chapter = None

            # Process all paragraphs in this div
            paragraphs = div.find_all('p')

            for p in paragraphs:
                p_class = p.get('class', [])
                if not p_class:
                    continue

                p_class_str = ' '.join(p_class)
                text_content = clean_text(p.get_text())

                if not text_content:
                    continue

                # Check if this is a chapter header (lang-en17)
                if 'lang-en17' in p_class_str:
                    parsed = parse_chapter_header(text_content)
                    if parsed:
                        current_book, current_chapter = parsed
                        logger.debug(f"Found chapter: {current_book} {current_chapter}")
                    continue

                # Check if this is verse commentary (lang-en16 or lang-en7)
                if 'lang-en16' in p_class_str or 'lang-en7' in p_class_str:
                    if not current_book or not current_chapter:
                        # Skip if we don't have book/chapter context
                        continue

                    # Extract verse number
                    verse_num = extract_verse_number(text_content)

                    if verse_num is None:
                        # If no verse number found, try to extract from strong tags
                        strong_tags = p.find_all('strong', class_='calibre2')
                        for strong in strong_tags:
                            verse_num = extract_verse_number(strong.get_text())
                            if verse_num:
                                break

                    # Convert HTML to markdown
                    commentary_md = convert_html_to_markdown(p)

                    # Remove the verse number prefix from commentary text
                    # (we'll format it properly in markdown)
                    commentary_clean = re.sub(r'^Ver\.\s*\d+\.\s*', '', commentary_md, flags=re.IGNORECASE).strip()

                    if commentary_clean:
                        commentary_data[current_book][current_chapter].append({
                            'verse': verse_num if verse_num else 0,
                            'commentary': commentary_clean
                        })

    return dict(commentary_data)


def generate_markdown_file(book_name: str, chapters: Dict[int, List[Dict[str, str]]], output_dir: Path) -> bool:
    """Generates a Markdown file for a single book of commentary.

    Follows markdown best practices:
    - YAML frontmatter with metadata
    - Hierarchical headers (# for book, ## for chapters)
    - Table of contents
    - Clean verse formatting
    - Consistent spacing
    - Filename matches Bible extraction pattern: Bible_Book_{position:02d}_{book_name}_Commentary.md

    Args:
        book_name: Name of the Bible book as it appears in the EPUB
        chapters: Dictionary mapping chapter numbers to lists of verse commentaries
        output_dir: Directory to save the Markdown file

    Returns:
        True if successful, False otherwise
    """
    if not book_name or not chapters:
        logger.warning(f"Invalid data for book: {book_name}")
        return False

    # Get canonical information using shared module
    canonical_info = get_canonical_info(book_name=book_name)
    if not canonical_info:
        logger.warning(f"Could not find canonical position for book: {book_name}")
        # Fallback: use position 99 and original name
        canonical_position = 99
        canonical_name = book_name
        section = ""
        book_id = None
    else:
        canonical_position = canonical_info['canonical_position']
        canonical_name = canonical_info['canonical_name']
        section = canonical_info.get('section', '')
        book_id = canonical_info.get('id')

    # Determine testament
    testament = "Old Testament" if canonical_position <= 46 else "New Testament"

    # Create safe filename matching Bible extraction pattern
    # Format: Bible_Book_01_Genesis_Commentary.md
    safe_book_name = "".join(c for c in canonical_name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_book_name = safe_book_name.replace(' ', '_')
    filename = f"Bible_Book_{canonical_position:02d}_{safe_book_name}_Commentary.md"
    filepath = output_dir / filename

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            # YAML frontmatter following best practices (matching Bible extraction pattern)
            f.write("---\n")
            f.write(f"title: {canonical_name} Commentary\n")
            f.write(f"book: {canonical_name}\n")
            f.write(f"canonical_position: {canonical_position}\n")
            f.write(f"testament: {testament}\n")
            if section:
                f.write(f"section: {section}\n")
            if book_id:
                f.write(f"book_id: {book_id}\n")
            f.write(f"commentary: Haydock Catholic Bible Commentary\n")
            f.write(f"edition: 1859 Edition\n")
            f.write(f"author: George Leo Haydock\n")
            f.write(f"total_chapters: {len(chapters)}\n")
            f.write("tags:\n")
            f.write("  - commentary\n")
            f.write("  - haydock\n")
            f.write("  - catholic\n")
            f.write("  - bible-commentary\n")
            f.write(f"  - {testament.lower().replace(' ', '-')}\n")
            if section:
                section_tag = section.lower().replace(' ', '-')
                f.write(f"  - {section_tag}\n")
            f.write("language: en\n")
            f.write("format: markdown\n")
            f.write("---\n\n")

            # Book title (H1) - matching Bible format
            f.write(f"# {canonical_name} Commentary\n\n")

            # Table of Contents - matching Bible format exactly
            f.write("## Table of Contents\n\n")
            for chapter_num in sorted(chapters.keys()):
                # Use lowercase, hyphenated format for anchors (matching Bible files)
                f.write(f"- [Chapter {chapter_num}](#chapter-{chapter_num})\n")
            f.write("\n---\n\n")

            # Process each chapter - matching Bible format exactly
            for chapter_num in sorted(chapters.keys()):
                verse_commentaries = chapters[chapter_num]

                # Chapter header (H2) - matching Bible format
                f.write(f"## Chapter {chapter_num}\n\n")

                # Process verses
                # Sort by verse number, but handle cases where verse number might be 0 or None
                sorted_verses = sorted(verse_commentaries, key=lambda x: x['verse'] if x['verse'] else 9999)

                for verse_data in sorted_verses:
                    verse_num = verse_data['verse']
                    commentary = verse_data['commentary']

                    if verse_num and verse_num > 0:
                        # Format: **verse_num** commentary text  (matching Bible format with two spaces at end)
                        f.write(f"**{verse_num}** {commentary}  \n")
                    else:
                        # If no verse number, just write the commentary (with two spaces for line break)
                        f.write(f"{commentary}  \n")

                # Horizontal rule between chapters (matching Bible format)
                f.write("\n---\n\n")

        logger.info(f"Generated: {filename} ({len(chapters)} chapters)")
        return True

    except Exception as e:
        logger.error(f"Error generating markdown for {book_name}: {e}", exc_info=True)
        return False


def main() -> int:
    """Main extraction function.

    Returns:
        Exit code: 0 for success, 1 for failure
    """
    logger.info("Starting Haydock Commentary extraction...")

    # Check if EPUB file exists
    if not INPUT_EPUB.exists():
        logger.error(f"Error: Could not find EPUB file at '{INPUT_EPUB}'")
        logger.info("Please download the EPUB file and place it in the data_sources/bible_commentary_haydock/ directory")
        logger.info(f"Expected filename: {INPUT_EPUB.name}")
        return 1

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {OUTPUT_DIR}")

    # Read EPUB file
    logger.info(f"Reading EPUB file: {INPUT_EPUB}")
    try:
        book = epub.read_epub(str(INPUT_EPUB))
    except Exception as e:
        logger.error(f"Error reading EPUB file: {e}", exc_info=True)
        return 1

    # Process content
    try:
        commentary_data = process_epub_content(book)
    except Exception as e:
        logger.error(f"Error processing EPUB content: {e}", exc_info=True)
        return 1

    if not commentary_data:
        logger.error("No commentary data extracted from EPUB")
        return 1

    logger.info(f"Extracted commentary for {len(commentary_data)} books")

    # Generate markdown files
    success_count = 0
    total_count = len(commentary_data)

    for book_name, chapters in commentary_data.items():
        if generate_markdown_file(book_name, chapters, OUTPUT_DIR):
            success_count += 1
        else:
            logger.warning(f"Failed to generate markdown for {book_name}")

    logger.info(f"✅ Success! Generated {success_count}/{total_count} commentary files")
    logger.info(f"Files saved in: {OUTPUT_DIR}")

    if success_count == 0:
        logger.error("No files were generated successfully")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
