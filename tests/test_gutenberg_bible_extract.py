"""Tests for Project Gutenberg Douay-Rheims extraction helpers."""

from pathlib import Path

import pytest

# Import from extraction module (loads canonical_books via sys.path)
from data_engineering.data_sources.bible_douay_rheims import extract_bible as eb


SAMPLE_PG = """
Header noise

*** START OF THE PROJECT GUTENBERG EBOOK FOO ***

THE BOOK OF GENESIS

Intro paragraph not a verse.

Genesis Chapter 1

1:1. In the beginning God created heaven, and earth.

1:2. And the earth was void and empty, and darkness was upon the face of
the deep; and the spirit of God moved over the waters.

A commentary line Without a verse number should be skipped.

1:3. And God said: Be light made. And light was made.

Genesis Chapter 2

2:1. So the heavens and the earth were finished.

*** END OF THE PROJECT GUTENBERG EBOOK FOO ***

Trailer
"""


def test_trim_gutenberg_ebook() -> None:
    body = eb.trim_gutenberg_ebook(SAMPLE_PG)
    assert "*** START" not in body
    assert "THE BOOK OF GENESIS" in body
    assert "Trailer" not in body


def test_parse_verses_from_lines_skips_commentary() -> None:
    lines = [
        "Genesis Chapter 1",
        "",
        "1:1. First verse.",
        "1:2. Second verse start",
        "continued with lowercase.",
        "Commentary Line Starts Here.",
        "1:3. Third verse.",
    ]
    verses = eb.parse_verses_from_lines(lines)
    nums = [v[0] for v in verses]
    assert nums == ["1", "2", "3"]
    assert "continued" in verses[1][1]
    assert "Commentary" not in " ".join(v[1] for v in verses)


def test_sanitize_verse_text() -> None:
    s = eb.sanitize_verse_text("Hello [See note 1] *world*  ")
    assert "[" not in s
    assert "*" not in s
    assert "world" in s


def test_find_book_header_line_indices_full_file() -> None:
    raw = Path("data_engineering/data_sources/bible_douay_rheims/raw/pg8300.txt")
    if not raw.is_file():
        pytest.skip("pg8300.txt not present")
    text = raw.read_text(encoding="utf-8")
    body = eb.trim_gutenberg_ebook(text)
    lines = body.splitlines()
    idx = eb.find_book_header_line_indices(lines)
    assert len(idx) == 73


def test_pg_order_mapping_length() -> None:
    assert len(eb.PG_ORDER_TO_CANON_INDEX) == 73
    assert len(set(eb.PG_ORDER_TO_CANON_INDEX)) == 73
