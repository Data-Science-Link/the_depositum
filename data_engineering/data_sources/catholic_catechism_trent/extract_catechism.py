#!/usr/bin/env python3
"""
McHugh & Callan Catechism Extraction Script

This script extracts the Catechism of the Council of Trent (McHugh & Callan Translation)
from an RTF file and converts it to clean Markdown format.

The script uses the striprtf library to convert Rich Text Format to plain text,
then applies regex patterns to detect headers and insert Markdown syntax.

Prerequisites:
    - Download the RTF file from SaintsBooks.net
    - Place it in the raw/ directory

Usage:
    python extract_catechism.py
"""

import re
import os
import logging
from pathlib import Path
from typing import Optional
import yaml
from striprtf.striprtf import rtf_to_text

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
    INPUT_FILENAME = Path(config['paths']['raw_data']['catechism'])
    OUTPUT_DIR = Path(config['paths']['processed_data']['catechism'])
    OUTPUT_FILENAME = config['output']['naming']['catechism']
except Exception as e:
    logger.warning(f"Could not load config, using defaults: {e}")
    INPUT_FILENAME = Path(__file__).parent / "raw" / "Catechism of the Council of Trent.rtf"
    OUTPUT_DIR = Path(__file__).parent.parent.parent / "processed_data" / "catholic_catechism_trent"
    OUTPUT_FILENAME = "Catechism_McHugh_Callan.md"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILEPATH = OUTPUT_DIR / OUTPUT_FILENAME


def clean_text(text: str) -> str:
    """Cleans up the raw text converted from RTF.

    Args:
        text: Raw text from RTF conversion

    Returns:
        Cleaned text string
    """
    # Normalize line breaks (RTF often creates excessive whitespace)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Remove common OCR/RTF artifacts
    text = text.replace('\x00', '')
    text = text.replace('\r', '')

    # Clean up extra spaces
    text = re.sub(r'[ \t]+', ' ', text)

    return text


def add_markdown_headers(text: str) -> str:
    """Identifies headers based on capitalization conventions in the McHugh/Callan text
    and applies Markdown syntax.

    Args:
        text: Cleaned plain text

    Returns:
        Text with Markdown headers applied
    """
    # 1. Main Parts (e.g., "PART I") -> # Header 1
    text = re.sub(r'^PART ([IVX]+)', r'# PART \1', text, flags=re.MULTILINE)

    # 2. Articles (e.g., "ARTICLE I") -> ## Header 2
    text = re.sub(r'^ARTICLE ([IVX]+)', r'## ARTICLE \1', text, flags=re.MULTILINE)

    # 3. Questions/Sub-sections -> ### Header 3
    # Note: Sometimes these are "QUESTION I" or just bolded text.
    # This pattern looks for "QUESTION" at the start of a line.
    text = re.sub(r'^(QUESTION [IVX0-9]+)', r'### \1', text, flags=re.MULTILINE)

    # 4. Additional patterns for sections (adjust based on your RTF structure)
    # Common patterns in catechisms:
    text = re.sub(r'^SECTION ([IVX0-9]+)', r'### SECTION \1', text, flags=re.MULTILINE)
    text = re.sub(r'^CHAPTER ([IVX0-9]+)', r'## CHAPTER \1', text, flags=re.MULTILINE)

    return text


def main():
    """Main extraction function."""
    logger.info("Starting Catechism extraction...")

    # Check if RTF file exists
    if not INPUT_FILENAME.exists():
        logger.error(f"Error: Could not find '{INPUT_FILENAME}' in this folder.")
        logger.info("Please download the RTF file from SaintsBooks.net and place it in the raw/ directory")
        return

    logger.info(f"Reading {INPUT_FILENAME}...")

    # RTF files can sometimes be quirky with encoding. 'utf-8' or 'latin-1' usually works.
    try:
        with open(INPUT_FILENAME, 'r', encoding='utf-8', errors='ignore') as f:
            rtf_content = f.read()
    except UnicodeDecodeError:
        logger.info("UTF-8 encoding failed, trying latin-1...")
        try:
            with open(INPUT_FILENAME, 'r', encoding='latin-1', errors='ignore') as f:
                rtf_content = f.read()
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            return
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        return

    logger.info("Converting RTF to Plain Text...")
    try:
        text_content = rtf_to_text(rtf_content)
    except Exception as e:
        logger.error(f"Error parsing RTF: {e}")
        return

    logger.info("Applying Markdown formatting...")
    clean_content = clean_text(text_content)
    final_content = add_markdown_headers(clean_content)

    # Write output file
    try:
        with open(OUTPUT_FILEPATH, 'w', encoding='utf-8') as f:
            f.write(final_content)

        file_size_kb = OUTPUT_FILEPATH.stat().st_size / 1024
        logger.info(f"✅ Success! Converted text saved to: {OUTPUT_FILEPATH}")
        logger.info(f"File size: {file_size_kb:.2f} KB")
    except Exception as e:
        logger.error(f"Error writing output file: {e}")
        return


if __name__ == "__main__":
    main()

