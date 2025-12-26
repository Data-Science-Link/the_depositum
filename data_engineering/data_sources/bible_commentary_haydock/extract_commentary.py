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
import argparse

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


def process_epub_content(book: epub.EpubBook) -> Tuple[Dict[str, Dict[int, List[Dict[str, str]]]], Dict[str, str]]:
    """Processes all HTML content from the EPUB file.

    Organizes commentary by book, then by chapter, then by verse.
    Also captures book introductions.

    EXODUS INTRODUCTION STRUCTURE (discovered through EPUB examination):
    The EPUB structure for Exodus (and likely other books) follows this pattern:
    - DIV N: Book name detection
      * lang-en13: "EXODUS" (book name)
      * lang-en14: "THE BOOK OF EXODUS" (full book title)
    - DIV N+1: Introduction section
      * lang-en15: "INTRODUCTION" (header paragraph)
      * lang-en7: Introduction text ("The second Book of Moses is called Exodus...")
        Note: lang-en7 is also used for verse commentary, so we distinguish by checking
        for verse numbers ("Ver.") - introduction text doesn't have verse numbers.
    - DIV N+2: Chapter 1 and verse commentary
      * lang-en17: "EXODUS 1" (chapter header)
      * lang-en7/lang-en16: Verse commentary starting with "Ver. 1.", "Ver. 2.", etc.

    KEY FIX: When detecting a new book name, we MUST reset current_chapter to None.
    Otherwise, if we're processing Exodus after Genesis, current_chapter might still be
    50 (from Genesis chapter 50), and the introduction collection logic that checks
    "if not current_chapter" will fail, causing the introduction to be skipped.

    Args:
        book: EpubBook object from ebooklib

    Returns:
        Tuple of:
        - Nested dictionary: {book_name: {chapter_num: [verse_commentaries]}}
          Each verse_commentary is a dict with 'verse' and 'commentary' keys
        - Dictionary: {book_name: introduction_text}
          Introduction text for each book
    """
    commentary_data = defaultdict(lambda: defaultdict(list))
    book_introductions = {}  # Store introductions per book

    logger.info("Processing EPUB HTML content...")

    total_items = 0
    total_divs = 0
    div_count = 0
    chapters_found = 0
    verses_found = 0

    # State variables that persist across ALL divs and items (for continuity)
    # These are initialized ONCE before processing any items
    current_book = None
    current_chapter = None
    in_introduction = False
    current_introduction = []  # Collect introduction paragraphs
    pending_introduction = []  # Collect introduction paragraphs before book name is detected
    last_seen_book_hint = None  # Track last book name hint (from lang-en11 in TOC)

    for item in book.get_items():
        if item.get_type() != ebooklib.ITEM_DOCUMENT:
            continue

        total_items += 1

        html_content = item.get_content()
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find all resource text divs
        resource_divs = soup.find_all('div', class_='resourcetext')
        total_divs += len(resource_divs)

        for div in resource_divs:
            div_count += 1

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

                # Skip title page and metadata content (lang-en through lang-en9)
                # These contain: title, author, publisher, publication date
                # Check for exact class matches (not substrings - lang-en17 contains lang-en1 and lang-en7!)
                # BUT: lang-en7 is also used for verse commentary, so we must NOT skip it here!
                # Only skip lang-en0 through lang-en6, lang-en8, lang-en9
                skip_classes = [f'lang-en{i}' for i in range(7)] + ['lang-en8', 'lang-en9']
                if any(cls in p_class for cls in skip_classes):
                    continue

                # Skip table of contents (lang-en10, lang-en11)
                # These contain: list of Bible book names
                # But save lang-en11 as a hint for the next book we might encounter
                if 'lang-en10' in p_class_str:
                    continue
                if 'lang-en11' in p_class_str:
                    # This is a book name in the TOC - save as hint for pending introduction
                    last_seen_book_hint = text_content.strip()
                    continue

                # Detect book name (lang-en13 or lang-en14)
                # lang-en13: "GENESIS"
                # lang-en14: "THE BOOK OF GENESIS"
                if 'lang-en13' in p_class_str or 'lang-en14' in p_class_str:
                    # Try to extract book name from text
                    # lang-en13 is usually just the book name, lang-en14 is "THE BOOK OF {NAME}"
                    if 'lang-en13' in p_class_str:
                        book_name = text_content.strip()
                    else:
                        # Extract from "THE BOOK OF GENESIS" -> "GENESIS"
                        book_name = text_content.replace("THE BOOK OF", "").strip()

                    if book_name:
                        # If we have pending introduction and this book matches the hint, assign it
                        if pending_introduction and last_seen_book_hint and book_name.upper() == last_seen_book_hint.upper():
                            current_introduction = pending_introduction
                            pending_introduction = []
                            in_introduction = True
                            logger.info(f"Assigned {len(current_introduction)} pending introduction paragraphs to {book_name}")
                        # If we were collecting introduction for a previous book, save it now
                        if in_introduction and current_book and current_book != book_name and current_introduction:
                            intro_text = '\n\n'.join(current_introduction)
                            if intro_text.strip():
                                book_introductions[current_book] = intro_text.strip()
                                logger.info(f"Captured introduction for {current_book} ({len(current_introduction)} paragraphs)")
                        # Don't reset introduction state if we're switching to a new book - introduction may come after
                        # Only reset if we're definitely starting a new book section
                        prev_book = current_book
                        current_book = book_name
                        # If this is a new book, reset chapter number
                        # EXODUS FIX: Must reset current_chapter to None when switching books, otherwise introduction
                        # text won't be collected. The introduction collection logic checks "if not current_chapter",
                        # so if current_chapter still has a value from the previous book (e.g., 50 from Genesis),
                        # the introduction text will be skipped.
                        if prev_book != book_name:
                            current_chapter = None  # Reset chapter when starting a new book
                            logger.info(f"Detected book name: {book_name} (previous: {prev_book})")
                            # Keep in_introduction and current_introduction if they exist, in case intro comes after
                        else:
                            # Same book, reset introduction state
                            in_introduction = False
                            current_introduction = []
                    continue

                # Detect introduction header (lang-en15)
                # EXODUS INTRODUCTION STRUCTURE (discovered through EPUB examination):
                # - DIV 8: Book name (lang-en13: "EXODUS", lang-en14: "THE BOOK OF EXODUS")
                # - DIV 9: Introduction header (lang-en15: "INTRODUCTION") followed by
                #          introduction text (lang-en7: "The second Book of Moses is called Exodus...")
                # - DIV 10: Chapter 1 header (lang-en17: "EXODUS 1") followed by verse commentary
                # The introduction text uses lang-en7 (same class as verse commentary), so we distinguish
                # by checking for verse numbers ("Ver.") - introduction text doesn't have verse numbers.
                if 'lang-en15' in p_class_str:
                    if current_book:
                        in_introduction = True
                        # Don't reset current_introduction - it might already have the first paragraph
                        if not current_introduction:
                            current_introduction = []
                        logger.info(f"Found INTRODUCTION header for {current_book}")
                    elif last_seen_book_hint:
                        # We have a book hint but book name not yet detected - start collecting for that book
                        in_introduction = True
                        current_introduction = []
                        logger.info(f"Found INTRODUCTION header but no current_book set, using hint: {last_seen_book_hint}")
                    else:
                        logger.warning(f"Found INTRODUCTION header but no current_book set and no hint available")
                    continue

                # Skip other metadata classes (lang-en8, lang-en9, lang-en12)
                # lang-en8: "THE OLD TESTAMENT OF THE HOLY CATHOLIC BIBLE"
                # lang-en9: "The books of the Old Testament:"
                # lang-en12: Commentator abbreviations explanation
                if any(f'lang-en{i}' in p_class_str for i in [8, 9, 12]):
                    continue

                # Check if this is a chapter header (lang-en17)
                if 'lang-en17' in p_class_str:
                    parsed = parse_chapter_header(text_content)
                    if parsed:
                        book_name, chapter_num = parsed

                        # If we were collecting introduction but didn't have a book name yet, assign it now
                        if in_introduction and current_introduction and not current_book:
                            # Check if the hint matches this book
                            if last_seen_book_hint and book_name.upper() == last_seen_book_hint.upper():
                                current_book = book_name
                                logger.info(f"Assigned book name {book_name} from chapter header, had {len(current_introduction)} intro paragraphs")
                            # Or if we have pending introduction that matches
                            elif pending_introduction and last_seen_book_hint and book_name.upper() == last_seen_book_hint.upper():
                                current_introduction = pending_introduction
                                pending_introduction = []
                                current_book = book_name
                                logger.info(f"Assigned {len(current_introduction)} pending introduction paragraphs to {book_name} from chapter header")

                        # Special case: if this is chapter 1 and we just found the INTRODUCTION header
                        # but haven't collected any paragraphs yet, keep collecting (introduction may come after)
                        if chapter_num == 1 and in_introduction and not current_introduction:
                            # Don't save yet, keep collecting introduction after chapter 1 header
                            logger.info(f"Chapter 1 found for {book_name} but introduction not yet collected, will continue collecting")
                        # If we were collecting introduction, save it now (before changing book/chapter)
                        elif in_introduction and current_introduction:
                            intro_text = '\n\n'.join(current_introduction)
                            if intro_text.strip():
                                # Use book_name from chapter header, or current_book as fallback
                                intro_book = book_name if book_name else current_book
                                if intro_book:
                                    book_introductions[intro_book] = intro_text.strip()
                                    logger.info(f"Captured introduction for {intro_book} ({len(current_introduction)} paragraphs)")

                        # Update current book and chapter
                        prev_book = current_book
                        current_book = book_name
                        current_chapter = chapter_num

                        # Don't reset in_introduction if we're still collecting for chapter 1
                        # The introduction paragraphs may come in the same div as the INTRODUCTION header,
                        # which is processed before this chapter header, but we need to keep collecting
                        if chapter_num == 1 and in_introduction:
                            # Keep introduction mode active to collect any remaining intro paragraphs
                            # They will be saved when we encounter the first verse or next chapter
                            logger.info(f"Chapter 1 found for {book_name}, keeping introduction mode active")
                        else:
                            in_introduction = False
                            current_introduction = []
                        chapters_found += 1
                        logger.info(f"✓ Parsed chapter: {current_book} {current_chapter}")
                    else:
                        # Log when we find lang-en17 but can't parse it
                        logger.warning(f"✗ Found lang-en17 but couldn't parse: '{text_content}' (len={len(text_content)}, repr={repr(text_content[:50])})")
                    continue

                # Check if this is verse commentary (lang-en16 or lang-en7)
                # Note: lang-en7 is used for both intro text AND verse commentary
                # We distinguish by checking for verse numbers
                # BUT: if we're in introduction mode and don't have a chapter yet, prioritize introduction collection
                if 'lang-en16' in p_class_str or 'lang-en7' in p_class_str:
                    # If we're in introduction mode and no chapter, check if this looks like introduction first
                    # Introduction text typically doesn't start with "Ver." and is longer
                    raw_text = p.get_text()
                    is_likely_intro = (in_introduction and not current_chapter and
                                     len(raw_text) > 100 and
                                     not raw_text.strip().startswith('Ver.') and
                                     'Ver.' not in raw_text[:50])

                    # Extract verse number from raw text first (before clean_text normalizes it)
                    verse_num = extract_verse_number(raw_text)
                    # Fallback to cleaned text if not found
                    if verse_num is None:
                        verse_num = extract_verse_number(text_content)

                    # If not found in text, try extracting from strong tags (calibre2 class contains "Ver. X.")
                    # The HTML structure is: <strong class="calibre2">Ver.</strong> <strong class="calibre2">1</strong><strong class="calibre2">.</strong>
                    if verse_num is None:
                        strong_tags = p.find_all('strong', class_='calibre2')
                        # Look for pattern: "Ver." followed by a number
                        for i, strong in enumerate(strong_tags):
                            strong_text = strong.get_text().strip()
                            # Check if this strong tag contains "Ver."
                            if 'Ver.' in strong_text or 'ver.' in strong_text.lower():
                                # Look for number in the next strong tag(s)
                                if i + 1 < len(strong_tags):
                                    next_strong = strong_tags[i + 1]
                                    num_text = next_strong.get_text().strip()
                                    try:
                                        verse_num = int(num_text)
                                        break
                                    except ValueError:
                                        pass
                        # Also try extracting from all strong tags combined
                        if verse_num is None and strong_tags:
                            all_strong_text = ' '.join([s.get_text() for s in strong_tags])
                            verse_num = extract_verse_number(all_strong_text)

                    # Convert HTML to markdown
                    commentary_md = convert_html_to_markdown(p)

                    # PRIORITY: If we're in introduction mode and no verse number, this is likely introduction text
                    # EXODUS CASE: After lang-en15 "INTRODUCTION" header is detected, the next paragraph in the same div
                    # is lang-en7 with the introduction text. This paragraph has:
                    # - class: lang-en7 (same as verse commentary, so we need to distinguish)
                    # - no verse number (verse_num = None after extraction)
                    # - long text (>50 chars) without "Ver." at the start
                    # - current_chapter = None (chapter 1 hasn't been detected yet, OR we just reset it for a new book)
                    # The key case: in_introduction=True, current_chapter=None, verse_num=None → collect as intro
                    # IMPORTANT: We must reset current_chapter=None when detecting a new book name, otherwise
                    # the introduction text won't be collected (it was still 50 from Genesis when processing Exodus intro)
                    if in_introduction and verse_num is None:
                        raw_text_for_check = p.get_text()

                        # If we have no chapter yet, definitely collect as introduction (most common case)
                        # This handles: book name → INTRODUCTION header → intro text (lang-en7) → chapter 1
                        # For Exodus: DIV 8 (book name) → DIV 9 (INTRODUCTION header + lang-en7 intro) → DIV 10 (chapter 1)
                        if not current_chapter:
                            # Check if this looks like introduction (long text, no "Ver." at start)
                            # Exodus intro text: "The second Book of Moses is called Exodus from the Greek word..."
                            looks_like_intro = (len(raw_text_for_check) > 50 and
                                              not raw_text_for_check.strip().startswith('Ver.') and
                                              'Ver.' not in raw_text_for_check[:30])
                            if looks_like_intro:
                                commentary_clean = commentary_md.strip()
                                if commentary_clean:
                                    current_introduction.append(commentary_clean)
                                    book_context = current_book if current_book else (last_seen_book_hint if last_seen_book_hint else "unknown")
                                    logger.info(f"Added introduction paragraph for {book_context} (before chapter): {commentary_clean[:50]}...")
                                continue
                        # If we're in chapter 1 and haven't collected intro yet, also collect
                        # This handles edge cases where introduction text comes after chapter 1 header
                        elif current_chapter == 1 and not current_introduction:
                            looks_like_intro = (len(raw_text_for_check) > 50 and
                                              not raw_text_for_check.strip().startswith('Ver.') and
                                              'Ver.' not in raw_text_for_check[:30])
                            if looks_like_intro:
                                commentary_clean = commentary_md.strip()
                                if commentary_clean:
                                    current_introduction.append(commentary_clean)
                                    logger.info(f"Added introduction paragraph for {current_book} (chapter 1, first): {commentary_clean[:50]}...")
                                continue
                        # Also handle if we're in chapter 1 and already have some intro paragraphs
                        # (in case intro text comes in multiple paragraphs after chapter header)
                        elif current_chapter == 1 and current_introduction:
                            looks_like_intro = (len(raw_text_for_check) > 50 and
                                              not raw_text_for_check.strip().startswith('Ver.') and
                                              'Ver.' not in raw_text_for_check[:30])
                            if looks_like_intro:
                                commentary_clean = commentary_md.strip()
                                if commentary_clean:
                                    current_introduction.append(commentary_clean)
                                    logger.info(f"Added introduction paragraph for {current_book} (chapter 1, continuing): {commentary_clean[:50]}...")
                                continue

                    # PRIORITY: If we have book/chapter context, it's verse commentary (even if verse_num extraction failed)
                    # BUT: if we're still collecting introduction (chapter 1, in_introduction mode), check if this is intro first
                    # This must come BEFORE introduction checks to avoid misclassifying verse 1 as introduction
                    # However, if we're in chapter 1 and introduction mode but haven't collected intro yet, prioritize intro
                    if current_book and current_chapter and not (current_chapter == 1 and in_introduction and not current_introduction):
                        # If verse number extraction failed, try one more time with raw HTML
                        if verse_num is None:
                            raw_text = p.get_text()
                            verse_num = extract_verse_number(raw_text)
                            # If still None but it looks like verse commentary (has "Ver." pattern), use 0 as fallback
                            if verse_num is None and ('Ver.' in raw_text or 'ver.' in raw_text.lower()):
                                verse_num = 0

                        # Process as verse commentary if we have a verse number (including 0 as fallback)
                        if verse_num is not None:
                            # If we're in chapter 1 and have introduction collected but not saved, save it now
                            if current_chapter == 1 and in_introduction and current_introduction:
                                intro_text = '\n\n'.join(current_introduction)
                                if intro_text.strip():
                                    book_introductions[current_book] = intro_text.strip()
                                    logger.info(f"Captured introduction for {current_book} when processing first verse ({len(current_introduction)} paragraphs)")
                                in_introduction = False
                                current_introduction = []

                            # Remove the verse number prefix from commentary text
                            commentary_clean = commentary_md
                            # Remove all variations of "Ver. X." in markdown format
                            commentary_clean = re.sub(r'^\*\*Ver\.\*\*\s*\*\*\d+\*\*\s*\*\*\.\*\*\s*', '', commentary_clean, flags=re.IGNORECASE)
                            commentary_clean = re.sub(r'^\*\*Ver\.\*\*\s*\*\*\d+\*\*\.\s*', '', commentary_clean, flags=re.IGNORECASE)
                            commentary_clean = re.sub(r'^\*\*Ver\.\*\*\s*\d+\.\s*', '', commentary_clean, flags=re.IGNORECASE)
                            commentary_clean = re.sub(r'^\*\*Ver\.\*\*\s*\*\*\d+\*\*\s+', '', commentary_clean, flags=re.IGNORECASE)
                            commentary_clean = re.sub(r'^Ver\.\s*\d+\.\s*', '', commentary_clean, flags=re.IGNORECASE)
                            commentary_clean = re.sub(r'^\*\*Ver\.\s*\d+\.\s*\*\*\s*', '', commentary_clean, flags=re.IGNORECASE)
                            commentary_clean = commentary_clean.strip()

                            if commentary_clean:
                                commentary_data[current_book][current_chapter].append({
                                    'verse': verse_num,
                                    'commentary': commentary_clean
                                })
                                verses_found += 1
                        continue

                    # If we're in introduction mode and no verse number, collect as introduction
                    # This handles remaining cases where introduction text appears
                    if in_introduction and verse_num is None:
                        commentary_clean = commentary_md.strip()
                        is_likely_intro = (commentary_clean and
                                         len(commentary_clean) > 50 and
                                         not commentary_clean.strip().startswith('Ver.') and
                                         'Ver.' not in commentary_clean[:30])
                        # Also allow if we're in chapter 1 and no verses have been processed yet
                        if current_book and current_chapter == 1 and not commentary_data.get(current_book, {}).get(1):
                            is_likely_intro = True
                        if is_likely_intro:
                            current_introduction.append(commentary_clean)
                            book_context = current_book if current_book else (last_seen_book_hint if last_seen_book_hint else "unknown")
                            logger.info(f"Added introduction paragraph for {book_context} (chapter {current_chapter if current_chapter else 'none'}): {commentary_clean[:50]}...")
                        continue

                    # Also check: if we have book but no chapter yet, and no verse number, it might be intro
                    # This handles the first introduction paragraph that appears before "INTRODUCTION" header
                    if verse_num is None and current_book and not current_chapter:
                        commentary_clean = commentary_md.strip()
                        looks_like_intro = (commentary_clean and
                                          len(commentary_clean) > 50 and
                                          not commentary_clean.strip().startswith('Ver.') and
                                          'Ver.' not in commentary_clean[:30])
                        if looks_like_intro:
                            if not in_introduction:
                                in_introduction = True
                                current_introduction = [commentary_clean]
                                logger.info(f"Started collecting introduction for {current_book} (first paragraph)")
                            else:
                                current_introduction.append(commentary_clean)
                                logger.info(f"Added introduction paragraph for {current_book}")
                        continue

                    # If we don't have a book name yet but we have a hint, collect as pending introduction
                    if not current_book and last_seen_book_hint and verse_num is None:
                        commentary_clean = commentary_md.strip()
                        if commentary_clean and len(commentary_clean) > 50 and not ('Ver.' in commentary_clean[:30] or 'ver.' in commentary_clean[:30].lower()):
                            pending_introduction.append(commentary_clean)
                            logger.info(f"Collected pending introduction paragraph (hint: {last_seen_book_hint}): {commentary_clean[:50]}...")
                        continue

    # Save any remaining introductions that weren't saved yet
    if in_introduction and current_book and current_introduction:
        intro_text = '\n\n'.join(current_introduction)
        if intro_text.strip():
            book_introductions[current_book] = intro_text.strip()
            logger.info(f"Captured final introduction for {current_book} ({len(current_introduction)} paragraphs)")

    # Also try to match introductions to books in commentary_data if names don't match exactly
    # This handles cases where book name detection might have slight variations
    for book_name in commentary_data.keys():
        if book_name not in book_introductions:
            # Try to find a matching introduction with a different case or slight variation
            for intro_book, intro_text in book_introductions.items():
                if book_name.upper() == intro_book.upper() or book_name.upper() in intro_book.upper() or intro_book.upper() in book_name.upper():
                    book_introductions[book_name] = intro_text
                    logger.info(f"Matched introduction from '{intro_book}' to '{book_name}'")
                    break

    logger.info(f"Processed {total_items} HTML items, {total_divs} resource divs")
    logger.info(f"Found {chapters_found} chapters and {verses_found} verse commentaries")
    logger.info(f"Extracted data for {len(commentary_data)} books")

    return dict(commentary_data), book_introductions


def generate_markdown_file(book_name: str, chapters: Dict[int, List[Dict[str, str]]], introduction: Optional[str], output_dir: Path, max_chapters: Optional[int] = None) -> bool:
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
        introduction: Optional introduction text for the book
        output_dir: Directory to save the Markdown file
        max_chapters: Maximum number of chapters to process (for testing), None for all chapters

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

    # Limit chapters if max_chapters is specified
    sorted_chapter_nums = sorted(chapters.keys())
    chapters_to_process = sorted_chapter_nums[:max_chapters] if max_chapters else sorted_chapter_nums
    total_chapters_in_book = len(chapters)
    chapters_processed = len(chapters_to_process)

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
            f.write(f"total_chapters: {total_chapters_in_book}\n")
            if max_chapters and chapters_processed < total_chapters_in_book:
                f.write(f"chapters_included: {chapters_processed} (test mode, limited from {total_chapters_in_book})\n")
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

            # Book introduction (if available)
            if introduction:
                f.write(f"{introduction}\n\n")

            # Table of Contents - matching Bible format exactly
            f.write("## Table of Contents\n\n")
            for chapter_num in chapters_to_process:
                # Use lowercase, hyphenated format for anchors (matching Bible files)
                f.write(f"- [Chapter {chapter_num}](#chapter-{chapter_num})\n")
            f.write("\n---\n\n")

            # Process each chapter - matching Bible format exactly
            for chapter_num in chapters_to_process:
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

        if max_chapters and chapters_processed < total_chapters_in_book:
            logger.info(f"Generated: {filename} ({chapters_processed}/{total_chapters_in_book} chapters, test mode limited to {max_chapters})")
        else:
            logger.info(f"Generated: {filename} ({chapters_processed} chapters, all complete)")
        return True

    except Exception as e:
        logger.error(f"Error generating markdown for {book_name}: {e}", exc_info=True)
        return False


def main(test_mode: bool = False, test_limit: int = 1, max_chapters: Optional[int] = 4) -> int:
    """Main extraction function.

    Args:
        test_mode: If True, only process the first N books (default: False)
        test_limit: Number of books to process in test mode (default: 1)
        max_chapters: Maximum number of chapters per book in test mode (default: 4, None for all chapters)

    Returns:
        Exit code: 0 for success, 1 for failure
    """
    if test_mode:
        chapters_info = f" (max {max_chapters} chapters per book)" if max_chapters else ""
        logger.info(f"🧪 TEST MODE: Processing only first {test_limit} books{chapters_info}...")
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
        commentary_data, book_introductions = process_epub_content(book)
    except Exception as e:
        logger.error(f"Error processing EPUB content: {e}", exc_info=True)
        return 1

    if not commentary_data:
        logger.error("No commentary data extracted from EPUB")
        return 1

    logger.info(f"Extracted commentary for {len(commentary_data)} books")
    if book_introductions:
        logger.info(f"Found introductions for {len(book_introductions)} books")

    # Sort books by canonical position for consistent processing order
    # Create a list of (book_name, canonical_position) tuples
    book_order = []
    for book_name in commentary_data.keys():
        canonical_info = get_canonical_info(book_name=book_name)
        if canonical_info:
            canonical_position = canonical_info['canonical_position']
        else:
            canonical_position = 99  # Fallback for unknown books
        book_order.append((book_name, canonical_position))

    # Sort by canonical position
    book_order.sort(key=lambda x: x[1])

    # Limit to test_limit books if in test mode
    if test_mode:
        book_order = book_order[:test_limit]
        logger.info(f"🧪 TEST MODE: Processing only first {test_limit} books in canonical order")

    # Generate markdown files
    success_count = 0
    total_count = len(book_order)

    for book_name, canonical_position in book_order:
        chapters = commentary_data.get(book_name)
        if not chapters:
            logger.warning(f"Skipping {book_name} - no chapters found")
            continue

        introduction = book_introductions.get(book_name)
        if generate_markdown_file(book_name, chapters, introduction, OUTPUT_DIR, max_chapters if test_mode else None):
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
    parser = argparse.ArgumentParser(description='Extract Haydock Catholic Bible Commentary from EPUB')
    parser.add_argument('--test', action='store_true', help='Test mode: process only first N books with limited chapters')
    parser.add_argument('--test-limit', type=int, default=1, help='Number of books to process in test mode (default: 1)')
    parser.add_argument('--max-chapters', type=int, default=4, help='Maximum number of chapters per book in test mode (default: 4, use 0 for all chapters)')

    args = parser.parse_args()

    # Convert max_chapters: 0 means None (all chapters)
    max_chapters = None if args.max_chapters == 0 else args.max_chapters

    exit(main(test_mode=args.test, test_limit=args.test_limit, max_chapters=max_chapters))
