#!/usr/bin/env python3
"""
Haydock Bible Commentary Extraction Script

This script extracts the Haydock Catholic Bible Commentary (1859 Edition) from
an EPUB file and converts it to clean Markdown format.

The script assumes the standard structure found in the John Blood/Isidore EPUBs.
If the specific EPUB you download has a different internal structure, you may
need to adjust the BeautifulSoup parsing logic.

Prerequisites:
    - Download the EPUB file from Isidore E-Book Library or JohnBlood GitLab
    - Place it in the raw/ directory

Usage:
    python extract_commentary.py
"""

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import os
import re
import logging
from pathlib import Path
from typing import Optional
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
    INPUT_EPUB = Path(config['paths']['raw_data']['haydock'])
    OUTPUT_DIR = Path(config['paths']['processed_data']['haydock'])
except Exception as e:
    logger.warning(f"Could not load config, using defaults: {e}")
    INPUT_EPUB = Path(__file__).parent / "raw" / "Haydock Catholic Bible Commentary.epub"
    OUTPUT_DIR = Path(__file__).parent.parent.parent / "processed_data" / "bible_commentary_haydock"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def clean_text(text: str) -> str:
    """Cleans up extra whitespace and weird artifacts.

    Args:
        text: Raw text string

    Returns:
        Cleaned text string
    """
    if not text:
        return ""
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove common artifacts
    text = text.replace('\x00', '')
    return text


def process_book_content(html_content: bytes, output_folder: Path, item_name: str) -> bool:
    """Parses the HTML of a single book/chapter.

    The logic below targets the specific layout of the common Haydock EPUBs.
    You may need to inspect the EPUB HTML manually to find the exact class names
    or structure used in your specific EPUB version.

    Args:
        html_content: Raw HTML bytes from EPUB
        output_folder: Directory to save Markdown files
        item_name: Name of the EPUB item (for filename generation)

    Returns:
        True if successful, False otherwise
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')

        # Try to find the book title (usually in an <h1> or <h2>)
        header = soup.find(['h1', 'h2'])
        if not header:
            # Try to extract title from item name
            title = item_name.replace('.html', '').replace('.xhtml', '')
        else:
            title = clean_text(header.get_text())

        if not title or len(title) < 2:
            logger.warning(f"Could not determine title for {item_name}")
            return False

        # Create a safe filename
        safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
        if not safe_title:
            safe_title = re.sub(r'[^\w\s-]', '', item_name).strip()

        filename = f"{safe_title}.md"
        filepath = output_folder / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n")

            # In the Haydock EPUB, commentary is often distinct from verse text.
            # We look for paragraphs or divs that might contain the commentary.
            # Note: You may need to inspect the EPUB HTML manually once to find
            # the exact class name. This is a generic "get all text" approach.

            paragraphs = soup.find_all('p')
            for p in paragraphs:
                text = clean_text(p.get_text())

                # Heuristic: Haydock notes often start with a verse number or
                # specific keywords. This captures the content.
                # You can refine this filter based on your EPUB structure.
                if len(text) > 5:
                    f.write(f"{text}\n\n")

            # Also check for divs with commentary content
            divs = soup.find_all('div', class_=re.compile(r'comment|note|verse', re.I))
            for div in divs:
                text = clean_text(div.get_text())
                if len(text) > 5:
                    f.write(f"{text}\n\n")

        logger.info(f"Processed: {title}")
        return True
    except Exception as e:
        logger.error(f"Error processing {item_name}: {e}")
        return False


def main():
    """Main extraction function."""
    logger.info("Starting Haydock Commentary extraction...")

    # Check if EPUB file exists
    if not INPUT_EPUB.exists():
        logger.error(f"Error: Could not find '{INPUT_EPUB}'.")
        logger.info("Please download the EPUB file and place it in the raw/ directory")
        return

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {OUTPUT_DIR}")

    logger.info(f"Reading {INPUT_EPUB}...")
    try:
        book = epub.read_epub(str(INPUT_EPUB))
    except Exception as e:
        logger.error(f"Error reading EPUB file: {e}")
        return

    logger.info("Extracting chapters...")
    count = 0
    success_count = 0

    # Iterate through all documents in the EPUB
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            # We only care about HTML content
            item_name = item.get_name()
            if process_book_content(item.get_content(), OUTPUT_DIR, item_name):
                success_count += 1
            count += 1

    logger.info(f"✅ Success! Processed {success_count}/{count} sections")
    logger.info(f"Files saved in '{OUTPUT_DIR}/'")


if __name__ == "__main__":
    main()

