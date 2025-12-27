"""
Canonical Catholic Bible Book Definitions

This module defines the canonical order and structure of all 73 books
in the Catholic Bible. It is shared across extraction scripts to ensure
consistent naming and numbering.

Section labels from USCCB: https://bible.usccb.org/bible
"""

from typing import Optional

# Canonical Catholic Bible order (73 books)
# This defines the correct order and numbering for all books in the Catholic canon
CATHOLIC_BIBLE_CANON = [
    # Old Testament (1-46)
    # The Pentateuch
    {'id': 'GEN', 'name': 'Genesis', 'canonical_position': 1, 'section': 'The Pentateuch'},
    {'id': 'EXO', 'name': 'Exodus', 'canonical_position': 2, 'section': 'The Pentateuch'},
    {'id': 'LEV', 'name': 'Leviticus', 'canonical_position': 3, 'section': 'The Pentateuch'},
    {'id': 'NUM', 'name': 'Numbers', 'canonical_position': 4, 'section': 'The Pentateuch'},
    {'id': 'DEU', 'name': 'Deuteronomy', 'canonical_position': 5, 'section': 'The Pentateuch'},
    # Historical Introduction
    {'id': 'JOS', 'name': 'Joshua', 'canonical_position': 6, 'section': 'Historical Introduction'},
    {'id': 'JDG', 'name': 'Judges', 'canonical_position': 7, 'section': 'Historical Introduction'},
    {'id': 'RUT', 'name': 'Ruth', 'canonical_position': 8, 'section': 'Historical Introduction'},
    {'id': '1SA', 'name': '1 Samuel', 'canonical_position': 9, 'section': 'Historical Introduction'},
    {'id': '2SA', 'name': '2 Samuel', 'canonical_position': 10, 'section': 'Historical Introduction'},
    {'id': '1KI', 'name': '1 Kings', 'canonical_position': 11, 'section': 'Historical Introduction'},
    {'id': '2KI', 'name': '2 Kings', 'canonical_position': 12, 'section': 'Historical Introduction'},
    {'id': '1CH', 'name': '1 Chronicles', 'canonical_position': 13, 'section': 'Historical Introduction'},
    {'id': '2CH', 'name': '2 Chronicles', 'canonical_position': 14, 'section': 'Historical Introduction'},
    {'id': 'EZR', 'name': 'Ezra', 'canonical_position': 15, 'section': 'Historical Introduction'},
    {'id': 'NEH', 'name': 'Nehemiah', 'canonical_position': 16, 'section': 'Historical Introduction'},
    # Biblical Novellas
    {'id': 'TOB', 'name': 'Tobit', 'canonical_position': 17, 'section': 'Biblical Novellas'},  # Deuterocanonical
    {'id': 'JDT', 'name': 'Judith', 'canonical_position': 18, 'section': 'Biblical Novellas'},  # Deuterocanonical
    {'id': 'EST', 'name': 'Esther', 'canonical_position': 19, 'section': 'Biblical Novellas'},
    {'id': '1MA', 'name': '1 Maccabees', 'canonical_position': 20, 'section': 'Biblical Novellas'},  # Deuterocanonical
    {'id': '2MA', 'name': '2 Maccabees', 'canonical_position': 21, 'section': 'Biblical Novellas'},  # Deuterocanonical
    # Wisdom Books
    {'id': 'JOB', 'name': 'Job', 'canonical_position': 22, 'section': 'Wisdom Books'},
    {'id': 'PSA', 'name': 'Psalms', 'canonical_position': 23, 'section': 'Wisdom Books'},
    {'id': 'PRO', 'name': 'Proverbs', 'canonical_position': 24, 'section': 'Wisdom Books'},
    {'id': 'ECC', 'name': 'Ecclesiastes', 'canonical_position': 25, 'section': 'Wisdom Books'},
    {'id': 'SNG', 'name': 'Song of Solomon', 'canonical_position': 26, 'section': 'Wisdom Books'},
    {'id': 'WIS', 'name': 'Wisdom', 'canonical_position': 27, 'section': 'Wisdom Books'},  # Deuterocanonical
    {'id': 'SIR', 'name': 'Sirach', 'canonical_position': 28, 'section': 'Wisdom Books'},  # Deuterocanonical (Ecclesiasticus)
    # Prophetic Books
    {'id': 'ISA', 'name': 'Isaiah', 'canonical_position': 29, 'section': 'Prophetic Books'},
    {'id': 'JER', 'name': 'Jeremiah', 'canonical_position': 30, 'section': 'Prophetic Books'},
    {'id': 'LAM', 'name': 'Lamentations', 'canonical_position': 31, 'section': 'Prophetic Books'},
    {'id': 'BAR', 'name': 'Baruch', 'canonical_position': 32, 'section': 'Prophetic Books'},  # Deuterocanonical
    {'id': 'EZK', 'name': 'Ezekiel', 'canonical_position': 33, 'section': 'Prophetic Books'},
    {'id': 'DAN', 'name': 'Daniel', 'canonical_position': 34, 'section': 'Prophetic Books'},
    {'id': 'HOS', 'name': 'Hosea', 'canonical_position': 35, 'section': 'Prophetic Books'},
    {'id': 'JOL', 'name': 'Joel', 'canonical_position': 36, 'section': 'Prophetic Books'},
    {'id': 'AMO', 'name': 'Amos', 'canonical_position': 37, 'section': 'Prophetic Books'},
    {'id': 'OBA', 'name': 'Obadiah', 'canonical_position': 38, 'section': 'Prophetic Books'},
    {'id': 'JON', 'name': 'Jonah', 'canonical_position': 39, 'section': 'Prophetic Books'},
    {'id': 'MIC', 'name': 'Micah', 'canonical_position': 40, 'section': 'Prophetic Books'},
    {'id': 'NAM', 'name': 'Nahum', 'canonical_position': 41, 'section': 'Prophetic Books'},
    {'id': 'HAB', 'name': 'Habakkuk', 'canonical_position': 42, 'section': 'Prophetic Books'},
    {'id': 'ZEP', 'name': 'Zephaniah', 'canonical_position': 43, 'section': 'Prophetic Books'},
    {'id': 'HAG', 'name': 'Haggai', 'canonical_position': 44, 'section': 'Prophetic Books'},
    {'id': 'ZEC', 'name': 'Zechariah', 'canonical_position': 45, 'section': 'Prophetic Books'},
    {'id': 'MAL', 'name': 'Malachi', 'canonical_position': 46, 'section': 'Prophetic Books'},
    # New Testament (47-73)
    # The Gospels
    {'id': 'MAT', 'name': 'Matthew', 'canonical_position': 47, 'section': 'The Gospels'},
    {'id': 'MRK', 'name': 'Mark', 'canonical_position': 48, 'section': 'The Gospels'},
    {'id': 'LUK', 'name': 'Luke', 'canonical_position': 49, 'section': 'The Gospels'},
    {'id': 'JHN', 'name': 'John', 'canonical_position': 50, 'section': 'The Gospels'},
    {'id': 'ACT', 'name': 'Acts', 'canonical_position': 51, 'section': 'Acts of the Apostles'},
    # New Testament Letters
    {'id': 'ROM', 'name': 'Romans', 'canonical_position': 52, 'section': 'New Testament Letters'},
    {'id': '1CO', 'name': '1 Corinthians', 'canonical_position': 53, 'section': 'New Testament Letters'},
    {'id': '2CO', 'name': '2 Corinthians', 'canonical_position': 54, 'section': 'New Testament Letters'},
    {'id': 'GAL', 'name': 'Galatians', 'canonical_position': 55, 'section': 'New Testament Letters'},
    {'id': 'EPH', 'name': 'Ephesians', 'canonical_position': 56, 'section': 'New Testament Letters'},
    {'id': 'PHP', 'name': 'Philippians', 'canonical_position': 57, 'section': 'New Testament Letters'},
    {'id': 'COL', 'name': 'Colossians', 'canonical_position': 58, 'section': 'New Testament Letters'},
    {'id': '1TH', 'name': '1 Thessalonians', 'canonical_position': 59, 'section': 'New Testament Letters'},
    {'id': '2TH', 'name': '2 Thessalonians', 'canonical_position': 60, 'section': 'New Testament Letters'},
    {'id': '1TI', 'name': '1 Timothy', 'canonical_position': 61, 'section': 'New Testament Letters'},
    {'id': '2TI', 'name': '2 Timothy', 'canonical_position': 62, 'section': 'New Testament Letters'},
    {'id': 'TIT', 'name': 'Titus', 'canonical_position': 63, 'section': 'New Testament Letters'},
    {'id': 'PHM', 'name': 'Philemon', 'canonical_position': 64, 'section': 'New Testament Letters'},
    {'id': 'HEB', 'name': 'Hebrews', 'canonical_position': 65, 'section': 'New Testament Letters'},
    # Catholic Letters
    {'id': 'JAS', 'name': 'James', 'canonical_position': 66, 'section': 'Catholic Letters'},
    {'id': '1PE', 'name': '1 Peter', 'canonical_position': 67, 'section': 'Catholic Letters'},
    {'id': '2PE', 'name': '2 Peter', 'canonical_position': 68, 'section': 'Catholic Letters'},
    {'id': '1JN', 'name': '1 John', 'canonical_position': 69, 'section': 'Catholic Letters'},
    {'id': '2JN', 'name': '2 John', 'canonical_position': 70, 'section': 'Catholic Letters'},
    {'id': '3JN', 'name': '3 John', 'canonical_position': 71, 'section': 'Catholic Letters'},
    {'id': 'JUD', 'name': 'Jude', 'canonical_position': 72, 'section': 'Catholic Letters'},
    {'id': 'REV', 'name': 'Revelation', 'canonical_position': 73, 'section': 'Revelation'},
]

# Deuterocanonical books missing from bible-api.com
# These are the 7 books that should be in the Catholic canon but are not returned by the API
DEUTEROCANONICAL_BOOKS = [
    {'id': 'TOB', 'name': 'Tobit', 'canonical_position': 17},  # Biblical Novellas
    {'id': 'JDT', 'name': 'Judith', 'canonical_position': 18},  # Biblical Novellas
    {'id': 'WIS', 'name': 'Wisdom', 'canonical_position': 27},  # Wisdom Books
    {'id': 'SIR', 'name': 'Sirach', 'canonical_position': 28},  # Wisdom Books
    {'id': 'BAR', 'name': 'Baruch', 'canonical_position': 32},  # Prophetic Books
    {'id': '1MA', 'name': '1 Maccabees', 'canonical_position': 20},  # Biblical Novellas
    {'id': '2MA', 'name': '2 Maccabees', 'canonical_position': 21},  # Biblical Novellas
]

# Name variations mapping (Latin/Vulgate names to canonical English names)
# Used for matching book names from different sources (e.g., Haydock Commentary EPUB)
BOOK_NAME_VARIATIONS = {
    # Historical books
    'josue': 'Joshua',
    'tobias': 'Tobit',
    '1 kings': '1 Samuel',  # Vulgate numbering: 1 Kings = 1 Samuel
    '2 kings': '2 Samuel',  # Vulgate numbering: 2 Kings = 2 Samuel
    '3 kings': '1 Kings',  # Vulgate numbering: 3 Kings = 1 Kings
    '4 kings': '2 Kings',  # Vulgate numbering: 4 Kings = 2 Kings
    '1 paralipomenon': '1 Chronicles',  # Latin name for Chronicles
    '2 paralipomenon': '2 Chronicles',  # Latin name for Chronicles
    '1 esdras': 'Ezra',  # Latin name for Ezra
    '2 esdras': 'Nehemiah',  # Latin name for Nehemiah
    '1 machabees': '1 Maccabees',  # Alternative spelling
    '2 machabees': '2 Maccabees',  # Alternative spelling
    # Wisdom books
    'psalm': 'Psalms',
    'psalms': 'Psalms',
    'ecclesiasticus': 'Sirach',
    'canticle of canticles': 'Song of Solomon',
    'song of solomon': 'Song of Solomon',
    # Prophetic books
    'isaias': 'Isaiah',
    'jeremias': 'Jeremiah',
    'ezechiel': 'Ezekiel',
    'osee': 'Hosea',
    'abdias': 'Obadiah',
    'jonas': 'Jonah',
    'micheas': 'Micah',
    'habacuc': 'Habakkuk',
    'sophonias': 'Zephaniah',
    'aggeus': 'Haggai',
    'zacharias': 'Zechariah',
    'malachias': 'Malachi',
    # New Testament
    'apocalypse': 'Revelation',
}


def get_canonical_info(book_id: str = None, book_name: str = None) -> Optional[dict]:
    """Get the canonical information for a book in the Catholic Bible.

    Args:
        book_id: The book identifier (e.g., 'GEN', 'EXO')
        book_name: The book name (e.g., 'Genesis', 'Exodus')

    Returns:
        Dictionary with 'canonical_position', 'canonical_name', 'section', and 'id',
        or None if not found
    """
    # First try to match by ID
    if book_id:
        for book in CATHOLIC_BIBLE_CANON:
            if book['id'] == book_id:
                return {
                    'canonical_position': book['canonical_position'],
                    'canonical_name': book['name'],
                    'section': book.get('section', ''),
                    'id': book['id']
                }

    # Fallback: try to match by name (case-insensitive, handle variations)
    if book_name:
        book_name_lower = book_name.lower().strip()

        # First, check if there's a known variation mapping
        if book_name_lower in BOOK_NAME_VARIATIONS:
            canonical_name = BOOK_NAME_VARIATIONS[book_name_lower]
            # Now look up the canonical name
            for book in CATHOLIC_BIBLE_CANON:
                if book['name'].lower() == canonical_name.lower():
                    return {
                        'canonical_position': book['canonical_position'],
                        'canonical_name': book['name'],
                        'section': book.get('section', ''),
                        'id': book['id']
                    }

        # Try direct match
        for book in CATHOLIC_BIBLE_CANON:
            if book['name'].lower() == book_name_lower:
                return {
                    'canonical_position': book['canonical_position'],
                    'canonical_name': book['name'],
                    'section': book.get('section', ''),
                    'id': book['id']
                }
            # Handle variations like "1 Samuel" vs "1 Samuel" (spaces)
            if book_name_lower.replace(' ', '') == book['name'].lower().replace(' ', ''):
                return {
                    'canonical_position': book['canonical_position'],
                    'canonical_name': book['name'],
                    'section': book.get('section', ''),
                    'id': book['id']
                }

        # Try partial matches for compound names (e.g., "CANTICLE OF CANTICLES" -> "Song of Solomon")
        # Check if any variation key is contained in the book name
        for variation_key, canonical_name in BOOK_NAME_VARIATIONS.items():
            if variation_key in book_name_lower or book_name_lower in variation_key:
                for book in CATHOLIC_BIBLE_CANON:
                    if book['name'].lower() == canonical_name.lower():
                        return {
                            'canonical_position': book['canonical_position'],
                            'canonical_name': book['name'],
                            'section': book.get('section', ''),
                            'id': book['id']
                        }

    return None

