#!/usr/bin/env python3
"""
Douay-Rheims Bible Extraction Script

This script downloads the Douay-Rheims 1899 American Edition directly from
bible-api.com and converts it into clean, formatted Markdown files.

The API sources its text from ebible.org, a standard for public domain Bible data.
This ensures data integrity and canonical accuracy (73 books for Catholic translation).

Usage:
    python extract_bible.py
"""

import sys
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml
import requests

# Set up logging to both console and file
LOG_DIR = Path(__file__).parent.parent.parent.parent / "data_engineering" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "bible_extraction.log"

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
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
    API_BASE = config['api']['bible']['base_url']
    RATE_LIMIT_DELAY = config['api']['bible'].get('rate_limit_delay', 2.0)  # Default to 2 seconds for safety
    OUTPUT_DIR = Path(config['paths']['final_output']['douay_rheims'])
except (FileNotFoundError, yaml.YAMLError, KeyError) as e:
    logger.warning(f"Could not load config, using defaults: {e}")
    API_BASE = "https://bible-api.com/data/dra"
    RATE_LIMIT_DELAY = 0.5
    OUTPUT_DIR = Path(__file__).parent.parent.parent.parent / "data_final" / "bible_douay_rheims"

# Constants
REQUEST_TIMEOUT = 30
MAX_RETRIES = 5
INITIAL_RETRY_WAIT = 5  # seconds

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Canonical Catholic Bible order (73 books)
# This defines the correct order and numbering for all books in the Catholic canon
CATHOLIC_BIBLE_CANON = [
    # Old Testament (1-46)
    {'id': 'GEN', 'name': 'Genesis', 'canonical_position': 1},
    {'id': 'EXO', 'name': 'Exodus', 'canonical_position': 2},
    {'id': 'LEV', 'name': 'Leviticus', 'canonical_position': 3},
    {'id': 'NUM', 'name': 'Numbers', 'canonical_position': 4},
    {'id': 'DEU', 'name': 'Deuteronomy', 'canonical_position': 5},
    {'id': 'JOS', 'name': 'Joshua', 'canonical_position': 6},
    {'id': 'JDG', 'name': 'Judges', 'canonical_position': 7},
    {'id': 'RUT', 'name': 'Ruth', 'canonical_position': 8},
    {'id': '1SA', 'name': '1 Samuel', 'canonical_position': 9},
    {'id': '2SA', 'name': '2 Samuel', 'canonical_position': 10},
    {'id': '1KI', 'name': '1 Kings', 'canonical_position': 11},
    {'id': '2KI', 'name': '2 Kings', 'canonical_position': 12},
    {'id': '1CH', 'name': '1 Chronicles', 'canonical_position': 13},
    {'id': '2CH', 'name': '2 Chronicles', 'canonical_position': 14},
    {'id': 'EZR', 'name': 'Ezra', 'canonical_position': 15},
    {'id': 'NEH', 'name': 'Nehemiah', 'canonical_position': 16},
    {'id': 'EST', 'name': 'Esther', 'canonical_position': 17},
    {'id': 'TOB', 'name': 'Tobit', 'canonical_position': 18},  # Deuterocanonical
    {'id': 'JDT', 'name': 'Judith', 'canonical_position': 19},  # Deuterocanonical
    {'id': '1MA', 'name': '1 Maccabees', 'canonical_position': 20},  # Deuterocanonical
    {'id': '2MA', 'name': '2 Maccabees', 'canonical_position': 21},  # Deuterocanonical
    {'id': 'JOB', 'name': 'Job', 'canonical_position': 22},
    {'id': 'PSA', 'name': 'Psalms', 'canonical_position': 23},
    {'id': 'PRO', 'name': 'Proverbs', 'canonical_position': 24},
    {'id': 'ECC', 'name': 'Ecclesiastes', 'canonical_position': 25},
    {'id': 'SNG', 'name': 'Song of Solomon', 'canonical_position': 26},
    {'id': 'WIS', 'name': 'Wisdom', 'canonical_position': 27},  # Deuterocanonical
    {'id': 'SIR', 'name': 'Sirach', 'canonical_position': 28},  # Deuterocanonical (Ecclesiasticus)
    {'id': 'ISA', 'name': 'Isaiah', 'canonical_position': 29},
    {'id': 'JER', 'name': 'Jeremiah', 'canonical_position': 30},
    {'id': 'LAM', 'name': 'Lamentations', 'canonical_position': 31},
    {'id': 'BAR', 'name': 'Baruch', 'canonical_position': 32},  # Deuterocanonical
    {'id': 'EZK', 'name': 'Ezekiel', 'canonical_position': 33},
    {'id': 'DAN', 'name': 'Daniel', 'canonical_position': 34},
    {'id': 'HOS', 'name': 'Hosea', 'canonical_position': 35},
    {'id': 'JOL', 'name': 'Joel', 'canonical_position': 36},
    {'id': 'AMO', 'name': 'Amos', 'canonical_position': 37},
    {'id': 'OBA', 'name': 'Obadiah', 'canonical_position': 38},
    {'id': 'JON', 'name': 'Jonah', 'canonical_position': 39},
    {'id': 'MIC', 'name': 'Micah', 'canonical_position': 40},
    {'id': 'NAM', 'name': 'Nahum', 'canonical_position': 41},
    {'id': 'HAB', 'name': 'Habakkuk', 'canonical_position': 42},
    {'id': 'ZEP', 'name': 'Zephaniah', 'canonical_position': 43},
    {'id': 'HAG', 'name': 'Haggai', 'canonical_position': 44},
    {'id': 'ZEC', 'name': 'Zechariah', 'canonical_position': 45},
    {'id': 'MAL', 'name': 'Malachi', 'canonical_position': 46},
    # New Testament (47-73)
    {'id': 'MAT', 'name': 'Matthew', 'canonical_position': 47},
    {'id': 'MRK', 'name': 'Mark', 'canonical_position': 48},
    {'id': 'LUK', 'name': 'Luke', 'canonical_position': 49},
    {'id': 'JHN', 'name': 'John', 'canonical_position': 50},
    {'id': 'ACT', 'name': 'Acts', 'canonical_position': 51},
    {'id': 'ROM', 'name': 'Romans', 'canonical_position': 52},
    {'id': '1CO', 'name': '1 Corinthians', 'canonical_position': 53},
    {'id': '2CO', 'name': '2 Corinthians', 'canonical_position': 54},
    {'id': 'GAL', 'name': 'Galatians', 'canonical_position': 55},
    {'id': 'EPH', 'name': 'Ephesians', 'canonical_position': 56},
    {'id': 'PHP', 'name': 'Philippians', 'canonical_position': 57},
    {'id': 'COL', 'name': 'Colossians', 'canonical_position': 58},
    {'id': '1TH', 'name': '1 Thessalonians', 'canonical_position': 59},
    {'id': '2TH', 'name': '2 Thessalonians', 'canonical_position': 60},
    {'id': '1TI', 'name': '1 Timothy', 'canonical_position': 61},
    {'id': '2TI', 'name': '2 Timothy', 'canonical_position': 62},
    {'id': 'TIT', 'name': 'Titus', 'canonical_position': 63},
    {'id': 'PHM', 'name': 'Philemon', 'canonical_position': 64},
    {'id': 'HEB', 'name': 'Hebrews', 'canonical_position': 65},
    {'id': 'JAS', 'name': 'James', 'canonical_position': 66},
    {'id': '1PE', 'name': '1 Peter', 'canonical_position': 67},
    {'id': '2PE', 'name': '2 Peter', 'canonical_position': 68},
    {'id': '1JN', 'name': '1 John', 'canonical_position': 69},
    {'id': '2JN', 'name': '2 John', 'canonical_position': 70},
    {'id': '3JN', 'name': '3 John', 'canonical_position': 71},
    {'id': 'JUD', 'name': 'Jude', 'canonical_position': 72},
    {'id': 'REV', 'name': 'Revelation', 'canonical_position': 73},
]

# Deuterocanonical books missing from bible-api.com
# These are the 7 books that should be in the Catholic canon but are not returned by the API
DEUTEROCANONICAL_BOOKS = [
    {'id': 'TOB', 'name': 'Tobit', 'canonical_position': 18},
    {'id': 'JDT', 'name': 'Judith', 'canonical_position': 19},
    {'id': 'WIS', 'name': 'Wisdom', 'canonical_position': 27},
    {'id': 'SIR', 'name': 'Sirach', 'canonical_position': 28},
    {'id': 'BAR', 'name': 'Baruch', 'canonical_position': 32},
    {'id': '1MA', 'name': '1 Maccabees', 'canonical_position': 20},
    {'id': '2MA', 'name': '2 Maccabees', 'canonical_position': 21},
]


def get_canonical_position(book_id: str, book_name: str = None) -> Optional[int]:
    """Get the canonical position for a book in the Catholic Bible.

    Args:
        book_id: The book identifier (e.g., 'GEN', 'EXO')
        book_name: Optional book name for fallback matching

    Returns:
        Canonical position (1-73), or None if not found
    """
    # First try to match by ID
    for book in CATHOLIC_BIBLE_CANON:
        if book['id'] == book_id:
            return book['canonical_position']

    # Fallback: try to match by name (case-insensitive, handle variations)
    if book_name:
        book_name_lower = book_name.lower().strip()
        for book in CATHOLIC_BIBLE_CANON:
            if book['name'].lower() == book_name_lower:
                return book['canonical_position']
            # Handle variations like "1 Samuel" vs "1 Samuel"
            if book_name_lower.replace(' ', '') == book['name'].lower().replace(' ', ''):
                return book['canonical_position']

    return None


def get_deuterocanonical_books() -> List[Dict[str, Any]]:
    """Returns the list of deuterocanonical books that should be included in the Catholic canon.

    Returns:
        List of book dictionaries with 'id', 'name', and 'canonical_position' keys
    """
    return DEUTEROCANONICAL_BOOKS.copy()


def fetch_book_list() -> List[Dict[str, Any]]:
    """Fetches the list of books officially supported by the API for this translation.

    Returns:
        List of book dictionaries with 'id' and 'name' keys
    """
    logger.info(f"Fetching book list from {API_BASE}...")
    try:
        response = requests.get(API_BASE, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        books = data.get('books', [])
        logger.info(f"Found {len(books)} books")
        return books
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching book list: {e}")
        return []


def fetch_book_info(book_id: str, max_retries: int = MAX_RETRIES) -> Optional[Dict[str, Any]]:
    """Fetches book information and chapter list for a specific book with retry logic.

    Args:
        book_id: The book identifier (e.g., 'GEN', 'EXO')
        max_retries: Maximum number of retry attempts

    Returns:
        Dictionary with 'name' and 'chapters' keys, or None if fetch failed
    """
    url = f"{API_BASE}/{book_id}"
    logger.info(f"Fetching book info for {book_id}...")

    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)

            # Handle rate limiting with exponential backoff
            if response.status_code == 429:
                wait_time = INITIAL_RETRY_WAIT * (2 ** attempt)
                if attempt < max_retries - 1:
                    logger.warning(f"Rate limited on book {book_id}, waiting {wait_time}s before retry (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Rate limited on book {book_id} after {max_retries} attempts")
                    return None

            response.raise_for_status()
            data = response.json()

            # Extract book name from first chapter (all chapters have same book name)
            chapters = data.get('chapters', [])
            book_name = chapters[0].get('book', 'Unknown') if chapters else 'Unknown'

            return {
                'name': book_name,
                'chapters': chapters
            }
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = INITIAL_RETRY_WAIT * (2 ** attempt)
                logger.warning(f"Request failed for book {book_id}, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to fetch book info for {book_id} after {max_retries} attempts: {e}")
                return None

    return None


def fetch_chapter_verses(book_id: str, chapter_num: int, max_retries: int = MAX_RETRIES) -> Optional[List[Dict[str, Any]]]:
    """Fetches verses for a specific chapter with aggressive retry logic for rate limiting.

    Args:
        book_id: The book identifier (e.g., 'GEN', 'EXO')
        chapter_num: The chapter number
        max_retries: Maximum number of retry attempts

    Returns:
        List of verse dictionaries, or None if fetch failed
    """
    url = f"{API_BASE}/{book_id}/{chapter_num}"

    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)

            # Handle rate limiting with exponential backoff
            if response.status_code == 429:
                wait_time = INITIAL_RETRY_WAIT * (2 ** attempt)
                if attempt < max_retries - 1:
                    logger.warning(f"Rate limited on chapter {chapter_num}, waiting {wait_time}s before retry (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Rate limited on chapter {chapter_num} after {max_retries} attempts")
                    return None

            response.raise_for_status()
            data = response.json()
            verses = data.get('verses', [])
            if verses:
                return verses
            else:
                logger.warning(f"No verses returned for chapter {chapter_num}, retrying...")
                if attempt < max_retries - 1:
                    time.sleep(RATE_LIMIT_DELAY * 2)
                    continue
                return None
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = INITIAL_RETRY_WAIT * (2 ** attempt)
                logger.warning(f"Request failed for chapter {chapter_num}, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to fetch chapter {chapter_num} for {book_id} after {max_retries} attempts: {e}")
                return None

    return None


def generate_markdown(book_name: str, book_id: str, canonical_position: Optional[int], chapters: List[Dict[str, Any]], output_folder: Path) -> bool:
    """Converts a book's data into Markdown by fetching verses for each chapter.

    Args:
        book_name: The name of the book (e.g., 'Genesis')
        book_id: The book identifier (e.g., 'GEN')
        canonical_position: The canonical position in Catholic Bible (1-73), or None to auto-detect
        chapters: List of chapter dictionaries with chapter numbers
        output_folder: Directory to save the Markdown file

    Returns:
        True if successful, False otherwise
    """
    if not book_name or not chapters:
        logger.warning(f"Invalid book data for {book_name}")
        return False

    # Get canonical position if not provided
    if canonical_position is None:
        canonical_position = get_canonical_position(book_id, book_name)
        if canonical_position is None:
            logger.warning(f"Could not determine canonical position for {book_name} ({book_id}), using fallback")
            canonical_position = 99  # Fallback for unknown books

    # Clean filename with zero-padded canonical position and Bible_Book_ prefix
    # Format: Bible_Book_01_Genesis.md, Bible_Book_02_Exodus.md, etc.
    safe_filename = "".join(c for c in book_name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_filename = safe_filename.replace(' ', '_')
    filename = f"Bible_Book_{canonical_position:02d}_{safe_filename}.md"
    filepath = output_folder / filename

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            # Frontmatter
            f.write(f"---\n")
            f.write(f"title: {book_name}\n")
            f.write(f"tags: bible, douay-rheims\n")
            f.write(f"---\n\n")

            # Book title
            f.write(f"# {book_name}\n\n")

            # Process each chapter with validation
            total_chapters = len(chapters)
            successful_chapters = 0

            for chapter_info in chapters:
                chapter_num = chapter_info.get('chapter')
                if chapter_num is None:
                    continue

                logger.info(f"  Fetching chapter {chapter_num} ({successful_chapters + 1}/{total_chapters})...")

                # Fetch verses for this chapter with retries
                verses = fetch_chapter_verses(book_id, chapter_num)

                if not verses:
                    logger.error(f"  ❌ FAILED to fetch {book_name} chapter {chapter_num} after all retries")
                    logger.error(f"❌ Cannot proceed without all chapters. Skipping this book.")
                    return False

                f.write(f"## Chapter {chapter_num}\n\n")

                # Write verses in continuous flow (no paragraph breaks)
                for verse in verses:
                    verse_num = verse.get('verse')
                    text = verse.get('text', '').strip()

                    if not verse_num or not text:
                        logger.error(f"❌ Missing verse data in {book_name} chapter {chapter_num}")
                        logger.error(f"   Verse data: {verse}")
                        logger.error(f"❌ Cannot proceed without all verses. Skipping this book.")
                        return False

                    # Format: **1** In the beginning...
                    f.write(f"**{verse_num}** {text}  \n")

                # Horizontal rule between chapters
                f.write("\n---\n\n")

                successful_chapters += 1

                # Rate limiting delay between chapters
                time.sleep(RATE_LIMIT_DELAY)

            # Validate that we got all chapters
            if successful_chapters < total_chapters:
                logger.error(f"❌ INCOMPLETE: Only got {successful_chapters}/{total_chapters} chapters for {book_name}")
                logger.error(f"❌ Skipping this book.")
                return False

            logger.info(f"✅ Saved: {book_name} ({successful_chapters} chapters, all complete)")
            return True
    except (IOError, OSError) as e:
        logger.error(f"Error writing {book_name}: {e}", exc_info=True)
        return False


def main(test_mode: bool = False, test_limit: int = 5) -> int:
    """Main extraction function.

    Args:
        test_mode: If True, only process the first N books (default: False)
        test_limit: Number of books to process in test mode (default: 5)

    Returns:
        Exit code: 0 for success, 1 for failure
    """
    if test_mode:
        logger.info(f"🧪 TEST MODE: Processing only first {test_limit} books...")
    logger.info("Starting Douay-Rheims Bible extraction...")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {OUTPUT_DIR}")

    # Step 1: Get the list of books from API
    books = fetch_book_list()

    if not books:
        logger.error("Could not retrieve book list. Aborting.")
        return 1

    logger.info(f"Found {len(books)} books from API")

    # Create a mapping of book IDs to book info from API
    api_books_map = {book.get('id'): book for book in books if book.get('id')}

    # Step 2: Process books in canonical order (1-73)
    # This ensures files are created in the correct Catholic Bible order
    success_count = 0
    skipped_books = []  # Books that couldn't be found or processed
    failed_books = []  # Books that failed during processing

    # Determine how many books to process
    canonical_books_to_process = CATHOLIC_BIBLE_CANON[:test_limit] if test_mode else CATHOLIC_BIBLE_CANON

    logger.info(f"Processing {len(canonical_books_to_process)} books in canonical order...")
    logger.info(f"⚠️  Using {RATE_LIMIT_DELAY}s delay between requests to avoid rate limits")
    logger.info(f"📝 Logging to: {LOG_FILE}")

    for idx, canonical_book in enumerate(canonical_books_to_process, start=1):
        canonical_position = canonical_book['canonical_position']
        book_id = canonical_book['id']
        canonical_name = canonical_book['name']

        logger.info(f"\n📖 Processing {canonical_name} ({book_id}) - Canonical position: {canonical_position:02d} - Book {idx}/{len(canonical_books_to_process)}...")

        # Check if book is available in API
        api_book = api_books_map.get(book_id)

        if not api_book:
            # Try to fetch book info directly (might be available but not in list)
            logger.info(f"  Book {book_id} not in API list, attempting direct fetch...")
            book_info = fetch_book_info(book_id)

            if not book_info:
                logger.warning(f"  ⚠️  Skipping {canonical_name} ({book_id}) - not available in API")
                skipped_books.append({
                    'name': canonical_name,
                    'id': book_id,
                    'position': canonical_position,
                    'reason': 'Not available in API'
                })
                time.sleep(RATE_LIMIT_DELAY)  # Still wait to respect rate limits
                continue

            # Use the fetched info
            api_book_name = book_info['name']
            chapters = book_info['chapters']
        else:
            # Book is in API list, fetch full info
            api_book_name = api_book.get('name', canonical_name)
            book_info = fetch_book_info(book_id)

            if not book_info:
                logger.warning(f"  ⚠️  Skipping {canonical_name} ({book_id}) - failed to fetch book info")
                skipped_books.append({
                    'name': canonical_name,
                    'id': book_id,
                    'position': canonical_position,
                    'reason': 'Failed to fetch book info'
                })
                time.sleep(RATE_LIMIT_DELAY)
                continue

            chapters = book_info['chapters']

        # Rate limiting delay after fetching book info
        time.sleep(RATE_LIMIT_DELAY)

        # Generate markdown (this will fetch chapters individually)
        try:
            if generate_markdown(
                book_name=book_info['name'],
                book_id=book_id,
                canonical_position=canonical_position,
                chapters=chapters,
                output_folder=OUTPUT_DIR
            ):
                success_count += 1
                logger.info(f"  ✅ Successfully saved {canonical_name}")
            else:
                logger.warning(f"  ⚠️  Failed to generate markdown for {canonical_name}")
                failed_books.append({
                    'name': canonical_name,
                    'id': book_id,
                    'position': canonical_position,
                    'reason': 'Failed to generate markdown'
                })
        except Exception as e:
            logger.error(f"  ❌ Error processing {canonical_name}: {e}", exc_info=True)
            failed_books.append({
                'name': canonical_name,
                'id': book_id,
                'position': canonical_position,
                'reason': f'Exception: {str(e)}'
            })

        # Polite delay to respect API rate limits between books
        time.sleep(RATE_LIMIT_DELAY * 2)  # Longer delay between books

    # Final summary
    logger.info(f"\n{'='*60}")
    logger.info(f"📊 EXTRACTION SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"✅ Successfully processed: {success_count}/{len(canonical_books_to_process)} books")

    if skipped_books:
        logger.warning(f"\n⚠️  SKIPPED BOOKS ({len(skipped_books)}):")
        for book in skipped_books:
            logger.warning(f"   - {book['name']} ({book['id']}) - Position {book['position']:02d} - {book['reason']}")

    if failed_books:
        logger.error(f"\n❌ FAILED BOOKS ({len(failed_books)}):")
        for book in failed_books:
            logger.error(f"   - {book['name']} ({book['id']}) - Position {book['position']:02d} - {book['reason']}")

    total_expected = len(canonical_books_to_process)
    if success_count == total_expected:
        logger.info(f"\n🎉 All {total_expected} books completed successfully!")
        logger.info(f"Files saved in '{OUTPUT_DIR}/'")
        return 0
    else:
        missing_count = len(skipped_books) + len(failed_books)
        logger.warning(f"\n⚠️  INCOMPLETE: {success_count}/{total_expected} books extracted successfully")
        logger.warning(f"   {missing_count} books were skipped or failed")
        if skipped_books:
            logger.warning(f"   Missing books are not available from bible-api.com and must be obtained from an alternative source")
            logger.warning(f"   See README.md for information on alternative sources")
        logger.info(f"Files saved in '{OUTPUT_DIR}/'")
        return 1 if missing_count > 0 else 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Extract Douay-Rheims Bible to Markdown')
    parser.add_argument('--test', action='store_true', help='Test mode: process only first 5 books')
    parser.add_argument('--test-limit', type=int, default=5, help='Number of books to process in test mode (default: 5)')

    args = parser.parse_args()
    sys.exit(main(test_mode=args.test, test_limit=args.test_limit))

