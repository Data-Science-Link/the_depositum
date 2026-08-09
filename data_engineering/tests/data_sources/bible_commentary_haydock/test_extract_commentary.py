import pytest
from data_engineering.data_sources.bible_commentary_haydock.extract_commentary import extract_verse_number

def test_extract_verse_number_standard():
    """Test standard verse extractions."""
    assert extract_verse_number("Ver. 1.") == 1
    assert extract_verse_number("Ver. 12.") == 12
    assert extract_verse_number("Ver. 123 ") == 123

def test_extract_verse_number_case_insensitive():
    """Test case insensitivity."""
    assert extract_verse_number("ver. 5") == 5
    assert extract_verse_number("VER. 9.") == 9
    assert extract_verse_number("vEr. 10") == 10

def test_extract_verse_number_spacing():
    """Test different spacing around the verse number."""
    assert extract_verse_number("Ver.1") == 1
    assert extract_verse_number("Ver.   42") == 42
    assert extract_verse_number("Ver.\t7") == 7

def test_extract_verse_number_extra_text():
    """Test extraction when there is extra text around."""
    assert extract_verse_number("Here is Ver. 7 in the middle") == 7
    assert extract_verse_number("Ver. 2 and then some") == 2
    assert extract_verse_number("Beginning text Ver. 99") == 99

def test_extract_verse_number_invalid_inputs():
    """Test invalid or missing inputs."""
    assert extract_verse_number("Not a verse") is None
    assert extract_verse_number("Verse 1") is None
    assert extract_verse_number("V. 1") is None
    assert extract_verse_number("") is None
    assert extract_verse_number("Ver.") is None
    assert extract_verse_number("Ver. abc") is None
