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

# Deuterocanonical books missing from bible-api.com
# These are the 7 books that should be in the Catholic canon but are not returned by the API
DEUTEROCANONICAL_BOOKS = [
    {'id': 'TOB', 'name': 'Tobit', 'position': 17},  # After Esther
    {'id': 'JDT', 'name': 'Judith', 'position': 18},  # After Tobit
    {'id': 'WIS', 'name': 'Wisdom', 'position': 23},  # After Song of Solomon
    {'id': 'SIR', 'name': 'Sirach', 'position': 24},  # After Wisdom (also called Ecclesiasticus)
    {'id': 'BAR', 'name': 'Baruch', 'position': 26},  # After Lamentations
    {'id': '1MA', 'name': '1 Maccabees', 'position': 40},  # After Malachi
    {'id': '2MA', 'name': '2 Maccabees', 'position': 41},  # After 1 Maccabees
]


def get_deuterocanonical_books() -> List[Dict[str, Any]]:
    """Returns the list of deuterocanonical books that should be included in the Catholic canon.

    Returns:
        List of book dictionaries with 'id', 'name', and 'position' keys
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


def generate_markdown(book_name: str, book_id: str, book_number: int, chapters: List[Dict[str, Any]], output_folder: Path) -> bool:
    """Converts a book's data into Markdown by fetching verses for each chapter.

    Args:
        book_name: The name of the book (e.g., 'Genesis')
        book_id: The book identifier (e.g., 'GEN')
        book_number: The sequential number of the book (1, 2, 3, etc.)
        chapters: List of chapter dictionaries with chapter numbers
        output_folder: Directory to save the Markdown file

    Returns:
        True if successful, False otherwise
    """
    if not book_name or not chapters:
        logger.warning(f"Invalid book data for {book_name}")
        return False

    # Clean filename with book number prefix (e.g., "1_Genesis.md")
    safe_filename = "".join(c for c in book_name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_filename = safe_filename.replace(' ', '_')
    filename = f"{book_number}_{safe_filename}.md"
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
                    logger.error(f"❌ CRITICAL: Cannot proceed without all chapters. Exiting.")
                    sys.exit(1)

                f.write(f"## Chapter {chapter_num}\n\n")

                # Write verses in continuous flow (no paragraph breaks)
                for verse in verses:
                    verse_num = verse.get('verse')
                    text = verse.get('text', '').strip()

                    if not verse_num or not text:
                        logger.error(f"❌ CRITICAL: Missing verse data in {book_name} chapter {chapter_num}")
                        logger.error(f"   Verse data: {verse}")
                        logger.error(f"❌ Cannot proceed without all verses. Exiting.")
                        sys.exit(1)

                    # Format: **1** In the beginning...
                    f.write(f"**{verse_num}** {text}  \n")

                # Horizontal rule between chapters
                f.write("\n---\n\n")

                successful_chapters += 1

                # Rate limiting delay between chapters
                time.sleep(RATE_LIMIT_DELAY)

            # Validate that we got all chapters (should never reach here if we exit on failure)
            if successful_chapters < total_chapters:
                logger.error(f"❌ INCOMPLETE: Only got {successful_chapters}/{total_chapters} chapters for {book_name}")
                logger.error(f"❌ CRITICAL: Cannot proceed without all chapters. Exiting.")
                sys.exit(1)

            logger.info(f"✅ Saved: {book_name} ({successful_chapters} chapters, all complete)")
            return True
    except (IOError, OSError) as e:
        logger.error(f"Error writing {book_name}: {e}", exc_info=True)
        return False


def main() -> int:
    """Main extraction function.

    Returns:
        Exit code: 0 for success, 1 for failure
    """
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

    # Step 1.5: Check for missing deuterocanonical books and try to fetch them
    api_book_ids = {book.get('id') for book in books}
    deuterocanonical_books = get_deuterocanonical_books()
    missing_books = [book for book in deuterocanonical_books if book['id'] not in api_book_ids]
    unavailable_books = []  # Books that are not available from the API

    if missing_books:
        logger.warning(f"⚠️  API is missing {len(missing_books)} deuterocanonical books: {', '.join(b['name'] for b in missing_books)}")
        logger.info(f"Attempting to fetch missing books directly from API...")

        for missing_book in missing_books:
            book_id = missing_book['id']
            logger.info(f"  Trying to fetch {missing_book['name']} ({book_id})...")

            # Try to fetch the book info directly
            book_info = fetch_book_info(book_id)

            if book_info:
                logger.info(f"  ✅ Successfully found {missing_book['name']} in API (not in book list)")
                # Add it to the books list with a placeholder entry
                books.append({
                    'id': book_id,
                    'name': book_info['name'],
                    'is_deuterocanonical': True,
                    'position': missing_book['position']
                })
            else:
                logger.warning(f"  ❌ {missing_book['name']} ({book_id}) is not available in the API")
                logger.warning(f"     This book must be obtained from an alternative source")
                unavailable_books.append(missing_book)

            time.sleep(RATE_LIMIT_DELAY)

    # Validate book count
    total_books = len(books)
    expected_books = 73

    if total_books < expected_books:
        logger.error(f"❌ CRITICAL: Only {total_books} books found, but Catholic Douay-Rheims should have {expected_books} books")
        logger.error(f"   Missing {expected_books - total_books} books from the Catholic canon")
        if unavailable_books:
            logger.error(f"   The following deuterocanonical books are not available from the API:")
            for book in unavailable_books:
                logger.error(f"     - {book['name']} ({book['id']})")
        logger.error(f"   These books are not available from bible-api.com and must be obtained from an alternative source")
        logger.error(f"   See README.md for information on alternative sources")
        logger.error(f"   Continuing with available books, but extraction is incomplete...")
    elif total_books > expected_books:
        logger.warning(f"⚠️  Found {total_books} books, expected {expected_books} for Catholic canon")
    else:
        logger.info(f"✅ Found all {expected_books} books for Catholic canon")

    logger.info(f"Starting download of {total_books} books...")
    logger.info(f"⚠️  Using {RATE_LIMIT_DELAY}s delay between requests to avoid rate limits")
    logger.info(f"📝 Logging to: {LOG_FILE}")


    # Step 2: Loop through each book and process
    # Note: Script exits immediately if any book/chapter/verse fails
    success_count = 0
    for idx, book in enumerate(books, start=1):
        book_id = book.get('id')
        book_name_from_list = book.get('name')

        if not book_id:
            logger.warning(f"Skipping book with no ID: {book_name_from_list}")
            continue

        logger.info(f"\n📖 Processing {book_name_from_list} ({book_id}) - Book {idx}/{len(books)}...")

        # Fetch book info (name and chapter list)
        book_info = fetch_book_info(book_id)

        if not book_info:
            logger.error(f"❌ Failed to fetch book info for {book_id} after all retries")
            logger.error(f"❌ CRITICAL: Cannot proceed without book info. Exiting.")
            sys.exit(1)

        # Rate limiting delay after fetching book info
        time.sleep(RATE_LIMIT_DELAY)

        # Generate markdown (this will fetch chapters individually)
        # Note: generate_markdown will exit if any chapter/verse fails
        if generate_markdown(
            book_name=book_info['name'],
            book_id=book_id,
            book_number=idx,
            chapters=book_info['chapters'],
            output_folder=OUTPUT_DIR
        ):
            success_count += 1
        else:
            # Should never reach here since we exit on failure, but keep for safety
            logger.error(f"❌ Book {book_name_from_list} failed - missing chapters!")
            sys.exit(1)

        # Polite delay to respect API rate limits between books
        time.sleep(RATE_LIMIT_DELAY * 2)  # Longer delay between books

    # Final summary
    logger.info(f"\n{'='*60}")
    logger.info(f"📊 EXTRACTION SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"✅ Successfully processed: {success_count}/{len(books)} books")

    if total_books < expected_books:
        logger.error(f"❌ INCOMPLETE: Only {total_books}/{expected_books} books extracted")
        logger.error(f"   Missing {expected_books - total_books} deuterocanonical books from Catholic canon")
        logger.error(f"   The bible-api.com service only provides 66 books (Protestant canon)")
        logger.error(f"   To get the complete 73-book Catholic canon, you need to obtain the missing books from an alternative source")
        logger.info(f"Files saved in '{OUTPUT_DIR}/'")
        return 1
    else:
        logger.info(f"🎉 All {expected_books} books completed successfully!")
        logger.info(f"Files saved in '{OUTPUT_DIR}/'")
        return 0


if __name__ == "__main__":
    sys.exit(main())

