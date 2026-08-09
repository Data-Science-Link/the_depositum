import pytest
from data_engineering.data_sources.bible_commentary_haydock.extract_commentary import parse_chapter_header

def test_parse_chapter_header_valid():
    """Test parse_chapter_header with valid inputs."""
    # Standard cases
    assert parse_chapter_header("GENESIS 19") == ("GENESIS", 19)
    assert parse_chapter_header("EXODUS 1") == ("EXODUS", 1)

    # Numbered books
    assert parse_chapter_header("1 SAMUEL 1") == ("1 SAMUEL", 1)
    assert parse_chapter_header("2 CORINTHIANS 3") == ("2 CORINTHIANS", 3)
    assert parse_chapter_header("1 JOHN 1") == ("1 JOHN", 1)

    # Books with multiple words
    assert parse_chapter_header("SONG OF SOLOMON 5") == ("SONG OF SOLOMON", 5)

    # Inputs with extra whitespace (should be stripped)
    assert parse_chapter_header("  GENESIS 19  ") == ("GENESIS", 19)
    assert parse_chapter_header("1   SAMUEL   1") == ("1 SAMUEL", 1)


def test_parse_chapter_header_invalid():
    """Test parse_chapter_header with invalid inputs."""
    # Missing chapter
    assert parse_chapter_header("GENESIS") is None

    # Missing book
    assert parse_chapter_header("19") is None

    # Lowercase book name (regex requires uppercase)
    assert parse_chapter_header("Genesis 19") is None
    assert parse_chapter_header("genesis 19") is None

    # Extra text after chapter number
    assert parse_chapter_header("GENESIS 19 20") is None
    assert parse_chapter_header("GENESIS 19 text") is None

    # Invalid format (not a number)
    assert parse_chapter_header("GENESIS XIX") is None

    # Empty string
    assert parse_chapter_header("") is None
