import pytest
from data_engineering.data_sources.catholic_catechism_trent.extract_catechism import _split_long_lines

def test_split_long_lines_part_marker():
    """Test splitting on PART markers."""
    text = "Some intro text PART I : The Creed"
    expected = "Some intro text\nPART I : The Creed"
    assert _split_long_lines(text) == expected

def test_split_long_lines_article_marker():
    """Test splitting on ARTICLE markers."""
    text = "End of previous article. ARTICLE II : Second Article"
    expected = "End of previous article.\nARTICLE II : Second Article"
    assert _split_long_lines(text) == expected

def test_split_long_lines_all_caps_word():
    """Test splitting on all-caps structural words."""
    text = "This is a sentence. PREFACE The preface starts here."
    expected = "This is a sentence.\nPREFACE The preface starts here."
    assert _split_long_lines(text) == expected

def test_split_long_lines_all_caps_word_at_end():
    """Test splitting on all-caps structural words at the end of string."""
    text = "This is a sentence. INTRODUCTORY"
    expected = "This is a sentence.\nINTRODUCTORY"
    assert _split_long_lines(text) == expected

def test_split_long_lines_multiple_markers():
    """Test splitting with multiple markers in the text."""
    text = "Text before PART II : Second Part More text ARTICLE I : First Article"
    expected = "Text before\nPART II : Second Part More text\nARTICLE I : First Article"
    assert _split_long_lines(text) == expected

def test_split_long_lines_no_split_needed():
    """Test that no split occurs if no markers are present."""
    text = "Just a regular sentence with no structural markers."
    expected = text
    assert _split_long_lines(text) == expected

def test_split_long_lines_no_content_removed():
    """Test that all non-whitespace characters are preserved."""
    text = "Some text here PART I : The Creed And more text ARTICLE II : Test"
    result = _split_long_lines(text)

    # Check that non-whitespace characters match
    orig_chars = [c for c in text if not c.isspace()]
    result_chars = [c for c in result if not c.isspace()]
    assert orig_chars == result_chars
