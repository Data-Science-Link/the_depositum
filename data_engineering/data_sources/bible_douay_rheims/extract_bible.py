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

    # Step 1: Get the list of books
    books = fetch_book_list()

    if not books:
        logger.error("Could not retrieve book list. Aborting.")
        return 1

    logger.info(f"Found {len(books)} books. Starting download...")
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

    # Final summary (only reached if all books succeed)
    logger.info(f"\n{'='*60}")
    logger.info(f"📊 EXTRACTION SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"✅ Successfully processed: {success_count}/{len(books)} books")
    logger.info(f"🎉 All books completed successfully!")
    logger.info(f"Files saved in '{OUTPUT_DIR}/'")
    return 0


if __name__ == "__main__":
    sys.exit(main())

