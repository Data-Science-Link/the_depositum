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

import requests
import json
import os
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration
CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "pipeline_config.yaml"
try:
    with open(CONFIG_PATH, 'r') as f:
        config = yaml.safe_load(f)
    API_BASE = config['api']['bible']['base_url']
    RATE_LIMIT_DELAY = config['api']['bible']['rate_limit_delay']
    OUTPUT_DIR = Path(config['paths']['processed_data']['douay_rheims'])
except Exception as e:
    logger.warning(f"Could not load config, using defaults: {e}")
    API_BASE = "https://bible-api.com/data/dra"
    RATE_LIMIT_DELAY = 0.5
    OUTPUT_DIR = Path(__file__).parent.parent.parent / "processed_data" / "bible_douay_rheims"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def fetch_book_list() -> List[Dict[str, Any]]:
    """Fetches the list of books officially supported by the API for this translation.

    Returns:
        List of book dictionaries with 'id' and 'name' keys
    """
    logger.info(f"Fetching book list from {API_BASE}...")
    try:
        response = requests.get(API_BASE, timeout=30)
        response.raise_for_status()
        data = response.json()
        books = data.get('books', [])
        logger.info(f"Found {len(books)} books")
        return books
    except Exception as e:
        logger.error(f"Error fetching book list: {e}")
        return []


def fetch_book_content(book_id: str) -> Optional[Dict[str, Any]]:
    """Fetches the full text of a specific book by its ID.

    Args:
        book_id: The book identifier (e.g., 'genesis', 'exodus')

    Returns:
        Book data dictionary or None if fetch failed
    """
    url = f"{API_BASE}/{book_id}"
    logger.info(f"Downloading {book_id}...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Failed to download {book_id}: {e}")
        return None


def generate_markdown(book_data: Dict[str, Any], output_folder: Path) -> bool:
    """Converts a single book's JSON data into Markdown.

    Args:
        book_data: Dictionary containing book name and chapters
        output_folder: Directory to save the Markdown file

    Returns:
        True if successful, False otherwise
    """
    book_name = book_data.get('name', 'Unknown')
    chapters = book_data.get('chapters', [])

    if not book_name or not chapters:
        logger.warning(f"Invalid book data for {book_name}")
        return False

    # Clean filename (removes spaces and special chars for safer file handling)
    safe_filename = "".join(c for c in book_name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_filename = safe_filename.replace(' ', '_')
    filename = f"{safe_filename}.md"
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

            # Process chapters
            for chapter in chapters:
                chapter_num = chapter.get('chapter')
                if chapter_num is None:
                    continue

                f.write(f"## Chapter {chapter_num}\n\n")

                verses = chapter.get('verses', [])
                for verse in verses:
                    verse_num = verse.get('verse')
                    text = verse.get('text', '').strip()

                    if verse_num and text:
                        # Format: **1** In the beginning...
                        f.write(f"**{verse_num}** {text}  \n")

                # Horizontal rule between chapters
                f.write("\n---\n\n")

        logger.info(f"Saved: {book_name}")
        return True
    except Exception as e:
        logger.error(f"Error writing {book_name}: {e}")
        return False


def main():
    """Main extraction function."""
    logger.info("Starting Douay-Rheims Bible extraction...")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {OUTPUT_DIR}")

    # Step 1: Get the list of books
    books = fetch_book_list()

    if not books:
        logger.error("Could not retrieve book list. Aborting.")
        return

    logger.info(f"Found {len(books)} books. Starting download...")

    # Step 2: Loop through each book and process
    success_count = 0
    for book in books:
        book_id = book.get('id')
        book_name = book.get('name')

        if not book_id:
            logger.warning(f"Skipping book with no ID: {book_name}")
            continue

        # Download data for this specific book
        book_data = fetch_book_content(book_id)

        if book_data:
            if generate_markdown(book_data, OUTPUT_DIR):
                success_count += 1

        # Polite delay to respect API rate limits
        time.sleep(RATE_LIMIT_DELAY)

    logger.info(f"\n✅ Success! Processed {success_count}/{len(books)} books")
    logger.info(f"Files saved in '{OUTPUT_DIR}/'")


if __name__ == "__main__":
    main()

