#!/usr/bin/env python3
"""
Deuterocanonical Books Extraction Script

This script downloads the 7 Deuterocanonical books from the GitHub repository
https://github.com/xxruyle/Bible-DouayRheims/tree/main/Douay-Rheims
and converts them into clean, formatted Markdown files matching the format
of the existing Bible extraction script.

The Deuterocanonical books are:
- Tobit (TOB) - position 17
- Judith (JDT) - position 18
- Wisdom (WIS) - position 27
- Sirach (SIR) - position 28
- Baruch (BAR) - position 32
- 1 Maccabees (1MA) - position 20
- 2 Maccabees (2MA) - position 21

Usage:
    python extract_deuterocanonical.py
"""

import sys
import time
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml
import requests

# Add parent directory to path to import shared canonical_books module
canonical_books_path = Path(__file__).parent.parent
sys.path.insert(0, str(canonical_books_path))
from canonical_books import DEUTEROCANONICAL_BOOKS, get_canonical_info

# Set up logging to both console and file
LOG_DIR = Path(__file__).parent.parent.parent.parent / "data_engineering" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "deuterocanonical_extraction.log"

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

# Console handler with immediate flush for real-time output
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
console_handler.stream = sys.stdout  # Ensure we're writing to stdout
logger.addHandler(console_handler)

# Force immediate output
import sys
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None

# Load configuration
CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "pipeline_config.yaml"
try:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    output_path = config['paths']['final_output']['douay_rheims']
    # Resolve to absolute path relative to project root
    if Path(output_path).is_absolute():
        OUTPUT_DIR = Path(output_path)
    else:
        # Resolve relative to project root (4 levels up from this script)
        project_root = Path(__file__).parent.parent.parent.parent
        OUTPUT_DIR = (project_root / output_path).resolve()
except (FileNotFoundError, yaml.YAMLError, KeyError) as e:
    logger.warning(f"Could not load config, using defaults: {e}")
    # Resolve relative to project root (4 levels up from this script)
    project_root = Path(__file__).parent.parent.parent.parent
    OUTPUT_DIR = (project_root / "data_final" / "bible_douay_rheims").resolve()

# Constants
GITHUB_BASE_URL = "https://raw.githubusercontent.com/xxruyle/Bible-DouayRheims/main/Douay-Rheims"
REQUEST_TIMEOUT = 30
MAX_RETRIES = 5
INITIAL_RETRY_WAIT = 5  # seconds
RATE_LIMIT_DELAY = 0.5  # seconds between requests

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def fetch_json_from_github(book_name: str, max_retries: int = MAX_RETRIES) -> Optional[Dict[str, Any]]:
    """Fetches JSON file for a book from GitHub repository.

    Args:
        book_name: The book name (e.g., 'Tobit', 'Judith')
        max_retries: Maximum number of retry attempts

    Returns:
        Dictionary with book data, or None if fetch failed
    """
    # Map English names to Latin/Vulgate names used in GitHub repository
    # Based on the actual filenames in the repository
    latin_name_mapping = {
        'Tobit': 'Tobias',
        'Judith': 'Judith',  # Same in Latin
        'Wisdom': 'Wisdom',  # Same in Latin
        'Sirach': 'Ecclesiasticus',  # Latin name for Sirach
        'Baruch': 'Baruch',  # Same in Latin
        '1 Maccabees': '1 Machabees',  # Latin spelling
        '2 Maccabees': '2 Machabees',  # Latin spelling
    }

    # Get Latin name if available, otherwise use English name
    latin_name = latin_name_mapping.get(book_name, book_name)

    # Try different possible filename formats
    # Start with Latin name (most likely), then try English name
    base_names = [latin_name, book_name] if latin_name != book_name else [book_name]

    possible_names = []
    for base_name in base_names:
        possible_names.extend([
            base_name,  # Exact match (e.g., "Tobias")
            base_name.replace(' ', '_'),  # Spaces to underscores (e.g., "1_Machabees")
            base_name.replace(' ', ''),  # No spaces (e.g., "1Machabees")
            base_name.replace('1 ', '1_'),  # For "1 Maccabees" -> "1_Maccabees"
            base_name.replace('2 ', '2_'),  # For "2 Maccabees" -> "2_Maccabees"
            base_name.title(),  # Title case
            base_name.lower(),  # Lowercase
        ])

    # Remove duplicates while preserving order
    seen = set()
    unique_names = []
    for name in possible_names:
        if name not in seen:
            seen.add(name)
            unique_names.append(name)
    possible_names = unique_names

    logger.info(f"Trying {len(possible_names)} name variants: {', '.join(possible_names[:5])}{'...' if len(possible_names) > 5 else ''}")

    for attempt in range(max_retries):
        for name_variant in possible_names:
            url = f"{GITHUB_BASE_URL}/{name_variant}.json"
            logger.info(f"[Attempt {attempt + 1}/{max_retries}] Trying {name_variant}.json...")
            sys.stdout.flush()  # Force immediate output

            try:
                # Always use SSL verification for security
                response = requests.get(url, timeout=REQUEST_TIMEOUT, verify=True)

                # Handle rate limiting with exponential backoff
                if response.status_code == 429:
                    wait_time = INITIAL_RETRY_WAIT * (2 ** attempt)
                    if attempt < max_retries - 1:
                        logger.warning(f"Rate limited, waiting {wait_time}s before retry (attempt {attempt + 1}/{max_retries})...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Rate limited after {max_retries} attempts")
                        return None

                if response.status_code == 404:
                    # Try next name variant
                    logger.debug(f"404 for {name_variant}.json, trying next variant...")
                    continue

                response.raise_for_status()
                data = response.json()
                logger.info(f"✅ Successfully fetched {name_variant}.json")
                return data

            except requests.exceptions.SSLError as e:
                logger.error(f"SSL error for {name_variant}.json: {e}")
                # Don't retry on SSL errors - they won't fix themselves
                continue
            except requests.exceptions.Timeout as e:
                logger.warning(f"Timeout for {name_variant}.json: {e}")
                if attempt < max_retries - 1:
                    wait_time = INITIAL_RETRY_WAIT * (2 ** attempt)
                    logger.warning(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Timeout after {max_retries} attempts for {name_variant}.json")
                    continue
            except requests.exceptions.ConnectionError as e:
                logger.error(f"Connection error for {name_variant}.json: {e}")
                if attempt < max_retries - 1:
                    wait_time = INITIAL_RETRY_WAIT * (2 ** attempt)
                    logger.warning(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Connection failed after {max_retries} attempts for {name_variant}.json")
                    continue
            except requests.exceptions.RequestException as e:
                # Log the actual error for debugging
                error_msg = str(e)
                status_code = None
                if hasattr(e, 'response') and e.response is not None:
                    status_code = e.response.status_code
                    logger.warning(f"Request failed for {name_variant}.json: HTTP {status_code} - {error_msg}")
                else:
                    logger.warning(f"Request failed for {name_variant}.json: {error_msg}")

                if attempt < max_retries - 1:
                    wait_time = INITIAL_RETRY_WAIT * (2 ** attempt)
                    logger.warning(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch {name_variant}.json after {max_retries} attempts")
                    continue

    logger.error(f"Could not find {book_name}.json in GitHub repository after trying all variants")
    return None


def parse_json_structure(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Parses JSON data and extracts book information and chapters.

    This function handles different possible JSON structures from the GitHub repository.

    Args:
        data: The JSON data from GitHub

    Returns:
        Dictionary with 'name', 'chapters' keys, or None if parsing failed
    """
    if not data:
        return None

    # Try different possible JSON structures
    # Structure 1: Direct chapters array
    if isinstance(data, list):
        # Assume it's a list of chapters
        chapters = []
        for idx, chapter_data in enumerate(data, start=1):
            if isinstance(chapter_data, dict):
                # Check if it has verses or is a chapter object
                if 'verses' in chapter_data:
                    chapters.append({
                        'chapter': chapter_data.get('chapter', idx),
                        'verses': chapter_data['verses']
                    })
                else:
                    # Might be a flat chapter dict, try to extract verses
                    verses = []
                    # Extract numeric keys first, then sort numerically
                    numeric_items = []
                    for key, value in chapter_data.items():
                        if str(key).isdigit():
                            numeric_items.append((int(key), value))
                        elif 'verse' in str(key).lower():
                            verse_num = chapter_data.get('verse', chapter_data.get('v', len(verses) + 1))
                            text = value if isinstance(value, str) else chapter_data.get('text', chapter_data.get('t', ''))
                            verses.append({'verse': verse_num, 'text': text})
                    # Sort numeric items and add to verses
                    for key, value in sorted(numeric_items, key=lambda x: x[0]):
                        verses.append({'verse': key, 'text': str(value)})
                    if verses:
                        chapters.append({
                            'chapter': chapter_data.get('chapter', idx),
                            'verses': verses
                        })
            elif isinstance(chapter_data, list):
                # List of verses
                chapters.append({
                    'chapter': idx,
                    'verses': chapter_data
                })
        return {'name': None, 'chapters': chapters}

    # Structure 2: Object with 'chapters' key
    if 'chapters' in data:
        chapters = []
        for idx, chapter_data in enumerate(data['chapters'], start=1):
            if isinstance(chapter_data, dict):
                chapter_num = chapter_data.get('chapter', idx)
                if 'verses' in chapter_data:
                    chapters.append({
                        'chapter': chapter_num,
                        'verses': chapter_data['verses']
                    })
                else:
                    # Try to extract verses from dict keys
                    verses = []
                    # Sort keys numerically, not as strings
                    numeric_keys = [(int(k), v) for k, v in chapter_data.items() if str(k).isdigit()]
                    for key, value in sorted(numeric_keys, key=lambda x: x[0]):
                        verses.append({'verse': key, 'text': str(value)})
                    if verses:
                        chapters.append({
                            'chapter': chapter_num,
                            'verses': verses
                        })
                    else:
                        # Fallback: treat the whole dict as one verse
                        chapters.append({
                            'chapter': chapter_num,
                            'verses': [chapter_data]
                        })
            elif isinstance(chapter_data, list):
                chapters.append({
                    'chapter': idx,
                    'verses': chapter_data
                })
        return {
            'name': data.get('name', data.get('book', None)),
            'chapters': chapters
        }

    # Structure 3: Object with chapter numbers as keys (e.g., {"1": [...], "2": [...]})
    numeric_keys = [k for k in data.keys() if str(k).isdigit()]
    if numeric_keys:
        chapters = []
        for key in sorted(numeric_keys, key=int):
            chapter_data = data[key]
            if isinstance(chapter_data, list):
                chapters.append({
                    'chapter': int(key),
                    'verses': chapter_data
                })
            elif isinstance(chapter_data, dict):
                if 'verses' in chapter_data:
                    chapters.append({
                        'chapter': int(key),
                        'verses': chapter_data['verses']
                    })
                else:
                    # Try to extract verses from dict
                    verses = []
                    # Sort keys numerically, not as strings
                    numeric_items = [(int(k), v) for k, v in chapter_data.items() if str(k).isdigit()]
                    for v_key, v_value in sorted(numeric_items, key=lambda x: x[0]):
                        verses.append({'verse': v_key, 'text': str(v_value)})
                    if verses:
                        chapters.append({
                            'chapter': int(key),
                            'verses': verses
                        })
        return {
            'name': data.get('name', data.get('book', None)),
            'chapters': chapters
        }

    # Structure 4: Flat structure with verses having chapter/verse numbers
    if 'verses' in data:
        verses_list = data['verses'] if isinstance(data['verses'], list) else [data['verses']]
        # Group verses by chapter
        verses_by_chapter = {}

        for verse_data in verses_list:
            if isinstance(verse_data, dict):
                chapter_num = verse_data.get('chapter', verse_data.get('ch', 1))
                verse_num = verse_data.get('verse', verse_data.get('v', verse_data.get('number', 1)))
                text = verse_data.get('text', verse_data.get('t', verse_data.get('content', '')))

                if chapter_num not in verses_by_chapter:
                    verses_by_chapter[chapter_num] = []
                verses_by_chapter[chapter_num].append({
                    'verse': verse_num,
                    'text': text
                })

        chapters = []
        for chapter_num in sorted(verses_by_chapter.keys()):
            chapters.append({
                'chapter': chapter_num,
                'verses': sorted(verses_by_chapter[chapter_num], key=lambda v: int(v.get('verse', 0)) if str(v.get('verse', 0)).isdigit() else 0)
            })

        return {
            'name': data.get('name', data.get('book', None)),
            'chapters': chapters
        }

    # Structure 5: Try to find any structure with verse-like data
    # Look for nested structures that might contain verses
    for key, value in data.items():
        if isinstance(value, (list, dict)) and key.lower() in ['verses', 'chapters', 'data', 'content']:
            # Recursively try to parse
            sub_result = parse_json_structure(value if isinstance(value, dict) else {'chapters': value})
            if sub_result:
                sub_result['name'] = data.get('name', data.get('book', sub_result.get('name')))
                return sub_result

    logger.warning(f"Unknown JSON structure. Keys: {list(data.keys())[:10] if isinstance(data, dict) else type(data)}")
    # Last resort: try to save the raw data for manual inspection
    logger.debug(f"Raw data sample: {str(data)[:500]}")
    return None


def generate_markdown(book_name: str, book_id: str, canonical_position: int, parsed_data: Dict[str, Any], output_folder: Path) -> bool:
    """Converts parsed JSON data into Markdown format matching the existing Bible extraction.

    Args:
        book_name: The name of the book (e.g., 'Tobit')
        book_id: The book identifier (e.g., 'TOB')
        canonical_position: The canonical position in Catholic Bible (17-32)
        parsed_data: Dictionary with 'name' and 'chapters' keys from parse_json_structure
        output_folder: Directory to save the Markdown file

    Returns:
        True if successful, False otherwise
    """
    if not parsed_data or not parsed_data.get('chapters'):
        logger.warning(f"Invalid parsed data for {book_name}")
        return False

    chapters = parsed_data['chapters']
    book_name = parsed_data.get('name') or book_name

    # Get canonical info
    canonical_info = get_canonical_info(book_id=book_id, book_name=book_name)
    section = canonical_info.get('section', '') if canonical_info else ''

    # Determine testament (Old Testament: 1-46)
    testament = "Old Testament" if canonical_position <= 46 else "New Testament"

    # Clean filename with zero-padded canonical position and Bible_Book_ prefix
    # Sanitize to prevent path traversal and special characters
    safe_filename = "".join(c for c in book_name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_filename = safe_filename.replace(' ', '_')
    # Additional safety: ensure no path separators or other dangerous characters
    safe_filename = safe_filename.replace('/', '_').replace('\\', '_').replace('..', '_')
    # Limit length to prevent filesystem issues
    if len(safe_filename) > 100:
        safe_filename = safe_filename[:100]
    filename = f"Bible_Book_{canonical_position:02d}_{safe_filename}.md"
    # Use Path.resolve() to ensure we're writing to the intended directory
    output_folder_resolved = output_folder.resolve()
    filepath = (output_folder / filename).resolve()
    # Double-check that the resolved path is still within the output directory
    try:
        filepath.relative_to(output_folder_resolved)
    except ValueError:
        logger.error(f"Security check failed: filepath {filepath} is outside output directory {output_folder_resolved}")
        return False

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            # Enhanced frontmatter following markdown best practices
            # Escape YAML special characters in book_name for safety
            safe_title = book_name.replace(':', '-').replace('|', '-').replace('@', '-')
            f.write(f"---\n")
            f.write(f"title: {safe_title}\n")
            f.write(f"canonical_position: {canonical_position}\n")
            f.write(f"testament: {testament}\n")
            if section:
                f.write(f"section: {section}\n")
            f.write(f"book_id: {book_id}\n")
            f.write(f"translation: Douay-Rheims 1899 American Edition\n")
            f.write(f"total_chapters: {len(chapters)}\n")
            f.write(f"tags:\n")
            f.write(f"  - bible\n")
            f.write(f"  - douay-rheims\n")
            f.write(f"  - old-testament\n")
            if section:
                section_tag = section.lower().replace(' ', '-')
                f.write(f"  - {section_tag}\n")
            f.write(f"  - catholic-canon\n")
            f.write(f"  - deuterocanonical\n")
            f.write(f"language: en\n")
            f.write(f"format: markdown\n")
            f.write(f"---\n\n")

            # Book title
            f.write(f"# {book_name}\n\n")

            # Table of Contents
            f.write(f"## Table of Contents\n\n")
            for chapter_info in chapters:
                chapter_num = chapter_info.get('chapter')
                if chapter_num is not None:
                    chapter_anchor = f"chapter-{chapter_num}".lower()
                    f.write(f"- [Chapter {chapter_num}](#{chapter_anchor})\n")
            f.write(f"\n---\n\n")

            # Process each chapter
            total_chapters = len(chapters)
            successful_chapters = 0

            for chapter_info in chapters:
                chapter_num = chapter_info.get('chapter')
                if chapter_num is None:
                    continue

                logger.info(f"  Processing chapter {chapter_num} ({successful_chapters + 1}/{total_chapters})...")

                verses = chapter_info.get('verses', [])
                if not verses:
                    logger.warning(f"  ⚠️  No verses found for chapter {chapter_num}")
                    continue

                # Use anchor-friendly heading for TOC links
                f.write(f"## Chapter {chapter_num}\n\n")

                # Sort verses numerically before writing
                def get_verse_number(verse):
                    """Extract verse number for sorting."""
                    if isinstance(verse, dict):
                        verse_num = verse.get('verse', verse.get('v', verse.get('number', 0)))
                        # Try to convert to int, fallback to 0
                        try:
                            return int(verse_num) if verse_num else 0
                        except (ValueError, TypeError):
                            return 0
                    return 0

                sorted_verses = sorted(verses, key=get_verse_number)

                # Write verses
                for verse in sorted_verses:
                    # Handle different verse structures
                    if isinstance(verse, dict):
                        verse_num = verse.get('verse', verse.get('v', verse.get('number', '')))
                        text = verse.get('text', verse.get('t', verse.get('content', '')))
                    elif isinstance(verse, str):
                        # If verse is just a string, try to parse it or use index
                        verse_num = successful_chapters + 1
                        text = verse
                    else:
                        logger.warning(f"  ⚠️  Unknown verse format: {type(verse)}")
                        continue

                    if not verse_num or not text:
                        logger.warning(f"  ⚠️  Missing verse data in chapter {chapter_num}: verse_num={verse_num}, text={bool(text)}")
                        continue

                    # Format: **1** In the beginning...
                    f.write(f"**{verse_num}** {text.strip()}  \n")

                # Horizontal rule between chapters
                f.write("\n---\n\n")

                successful_chapters += 1

            # Validate that we got all chapters
            if successful_chapters < total_chapters:
                logger.warning(f"⚠️  INCOMPLETE: Only processed {successful_chapters}/{total_chapters} chapters for {book_name}")

            logger.info(f"✅ Saved: {book_name} ({successful_chapters} chapters)")
            return True

    except (IOError, OSError) as e:
        logger.error(f"Error writing {book_name}: {e}", exc_info=True)
        return False


def main() -> int:
    """Main extraction function.

    Returns:
        Exit code: 0 for success, 1 for failure
    """
    logger.info("Starting Deuterocanonical books extraction from GitHub...")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {OUTPUT_DIR}")

    # Get list of Deuterocanonical books
    books_to_extract = DEUTEROCANONICAL_BOOKS
    logger.info(f"Extracting {len(books_to_extract)} Deuterocanonical books...")
    logger.info(f"📝 Logging to: {LOG_FILE}")

    success_count = 0
    failed_books = []

    for idx, book_info in enumerate(books_to_extract, start=1):
        book_id = book_info['id']
        book_name = book_info['name']
        canonical_position = book_info['canonical_position']

        logger.info(f"\n📖 Processing {book_name} ({book_id}) - Canonical position: {canonical_position:02d} - Book {idx}/{len(books_to_extract)}...")

        # Fetch JSON from GitHub
        json_data = fetch_json_from_github(book_name)

        if not json_data:
            logger.error(f"  ❌ Failed to fetch {book_name} from GitHub")
            failed_books.append({
                'name': book_name,
                'id': book_id,
                'position': canonical_position,
                'reason': 'Failed to fetch from GitHub'
            })
            time.sleep(RATE_LIMIT_DELAY)
            continue

        # Parse JSON structure
        parsed_data = parse_json_structure(json_data)
        if not parsed_data:
            logger.error(f"  ❌ Failed to parse JSON structure for {book_name}")
            failed_books.append({
                'name': book_name,
                'id': book_id,
                'position': canonical_position,
                'reason': 'Failed to parse JSON structure'
            })
            time.sleep(RATE_LIMIT_DELAY)
            continue

        # Generate markdown
        try:
            if generate_markdown(
                book_name=book_name,
                book_id=book_id,
                canonical_position=canonical_position,
                parsed_data=parsed_data,
                output_folder=OUTPUT_DIR
            ):
                success_count += 1
                logger.info(f"  ✅ Successfully saved {book_name}")
            else:
                logger.warning(f"  ⚠️  Failed to generate markdown for {book_name}")
                failed_books.append({
                    'name': book_name,
                    'id': book_id,
                    'position': canonical_position,
                    'reason': 'Failed to generate markdown'
                })
        except Exception as e:
            logger.error(f"  ❌ Error processing {book_name}: {e}", exc_info=True)
            failed_books.append({
                'name': book_name,
                'id': book_id,
                'position': canonical_position,
                'reason': f'Exception: {str(e)}'
            })

        # Rate limiting delay between books
        time.sleep(RATE_LIMIT_DELAY)

    # Final summary
    logger.info(f"\n{'='*60}")
    logger.info(f"📊 EXTRACTION SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"✅ Successfully processed: {success_count}/{len(books_to_extract)} books")

    if failed_books:
        logger.error(f"\n❌ FAILED BOOKS ({len(failed_books)}):")
        for book in failed_books:
            logger.error(f"   - {book['name']} ({book['id']}) - Position {book['position']:02d} - {book['reason']}")

    total_expected = len(books_to_extract)
    if success_count == total_expected:
        logger.info(f"\n🎉 All {total_expected} Deuterocanonical books completed successfully!")
        logger.info(f"Files saved in '{OUTPUT_DIR}/'")
        return 0
    else:
        missing_count = len(failed_books)
        logger.warning(f"\n⚠️  INCOMPLETE: {success_count}/{total_expected} books extracted successfully")
        logger.warning(f"   {missing_count} books failed")
        logger.info(f"Files saved in '{OUTPUT_DIR}/'")
        return 1 if missing_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())

