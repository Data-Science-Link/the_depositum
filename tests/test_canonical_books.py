import pytest
from data_engineering.data_sources.canonical_books import get_canonical_info

def test_get_canonical_info_by_id():
    """Test matching by book ID."""
    info = get_canonical_info(book_id='GEN')
    assert info is not None
    assert info['id'] == 'GEN'
    assert info['canonical_name'] == 'Genesis'
    assert info['canonical_position'] == 1

def test_get_canonical_info_by_name_exact():
    """Test exact matching by book name."""
    info = get_canonical_info(book_name='Genesis')
    assert info is not None
    assert info['id'] == 'GEN'

def test_get_canonical_info_by_name_case_insensitive():
    """Test case-insensitive matching by book name."""
    info = get_canonical_info(book_name=' EXODUS ')
    assert info is not None
    assert info['id'] == 'EXO'

def test_get_canonical_info_by_name_whitespace():
    """Test whitespace handling."""
    info = get_canonical_info(book_name='1Samuel')
    assert info is not None
    assert info['id'] == '1SA'

def test_get_canonical_info_by_name_variation():
    """Test matching by known variation."""
    info = get_canonical_info(book_name='josue')
    assert info is not None
    assert info['id'] == 'JOS'

def test_get_canonical_info_by_name_partial():
    """Test partial matching for compound names."""
    info = get_canonical_info(book_name='CANTICLE OF CANTICLES')
    assert info is not None
    assert info['id'] == 'SNG'
    assert info['canonical_name'] == 'Song of Solomon'

def test_get_canonical_info_fallback():
    """Test fallback to name if ID is provided but invalid."""
    info = get_canonical_info(book_id='INVALID', book_name='Genesis')
    assert info is not None
    assert info['id'] == 'GEN'

def test_get_canonical_info_none():
    """Test edge cases that should return None."""
    assert get_canonical_info() is None
    assert get_canonical_info(book_id='NONEXISTENT') is None
    assert get_canonical_info(book_name='Unknown Book') is None
