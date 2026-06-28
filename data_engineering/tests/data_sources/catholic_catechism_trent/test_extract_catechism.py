import pytest

from data_engineering.data_sources.catholic_catechism_trent.extract_catechism import clean_text

def test_clean_text_removes_null_bytes_and_carriage_returns():
    """Test that null bytes and carriage returns are removed."""
    input_text = "Hello\x00 World\r\nThis is a test\r."
    expected = "Hello World\nThis is a test."
    assert clean_text(input_text) == expected

def test_clean_text_removes_page_number_references_with_dots():
    """Test that page number references with excessive dots are removed."""
    input_text = "Text.............................................................................25\nMore text"
    expected = "Text\nMore text"
    assert clean_text(input_text) == expected

def test_clean_text_removes_standalone_page_numbers():
    """Test that standalone page numbers on a single line are removed."""
    input_text = "Some text\n  42  \nMore text"
    expected = "Some text\n\nMore text"
    assert clean_text(input_text) == expected

def test_clean_text_removes_embedded_page_numbers():
    """Test that embedded page numbers at the end of text or before a capital letter are removed."""
    # Test case 1: Number before a capital letter
    input_text1 = "PART I : THE CREED33\nTHE SACRAMENTS"
    # Actually the function works on `([A-Za-z])\s*(\d{1,3})(\s+[A-Z])` so `PART I : THE CREED33\nTHE SACRAMENTS` matches
    expected1 = "PART I : THE CREED\nTHE SACRAMENTS"
    assert clean_text(input_text1) == expected1

    # Test case 2: Number at the end of line
    input_text2 = "The Necessity Of Religious Instruction29\nNext line"
    expected2 = "The Necessity Of Religious Instruction\nNext line"
    assert clean_text(input_text2) == expected2

def test_clean_text_removes_excessive_spacing_dots():
    """Test that excessive dots are removed from the text."""
    input_text = "Some text......more text"
    expected = "Some textmore text"
    assert clean_text(input_text) == expected

def test_clean_text_normalizes_spaces():
    """Test that excessive spaces and tabs are normalized to a single space."""
    input_text = "This    is \t a   test"
    expected = "This is a test"
    assert clean_text(input_text) == expected

def test_clean_text_normalizes_line_breaks():
    """Test that more than two consecutive line breaks are normalized to two line breaks."""
    input_text = "Paragraph One\n\n\n\nParagraph Two\n\n\nParagraph Three"
    expected = "Paragraph One\n\nParagraph Two\n\nParagraph Three"
    assert clean_text(input_text) == expected

def test_clean_text_preserves_content():
    """Test that actual text content is preserved without modification."""
    input_text = "This is a normal sentence. It has punctuation, and regular formatting."
    expected = "This is a normal sentence. It has punctuation, and regular formatting."
    assert clean_text(input_text) == expected
