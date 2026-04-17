"""Tests for Project Gutenberg Douay-Rheims HTML extraction helpers."""

from pathlib import Path

import pytest

# Import from extraction module (loads canonical_books via sys.path)
from data_engineering.data_sources.bible_douay_rheims import extract_bible as eb


SAMPLE_HTML = """
<html><body>
<a id="Book01"></a>
<p>Genesis Chapter 1</p>
<p>1:1. In the beginning God created heaven, and earth.</p>
<p>1:2. And the earth was void and empty</p>
<p>and darkness was upon the face of the deep.</p>
<p>A firmament... This is commentary and should be skipped.</p>
<p>1:3. And God said: Be light made. And light was made.</p>
<a id="Book02"></a>
</body></html>
"""


def test_iter_book_anchors_and_blocks() -> None:
    soup = eb.BeautifulSoup(SAMPLE_HTML, "html.parser")
    first = soup.find("a", id="Book01")
    second = soup.find("a", id="Book02")
    assert first is not None
    assert second is not None
    blocks = list(eb._iter_paragraph_blocks(first, second))
    assert "Genesis Chapter 1" in blocks
    assert any(b.startswith("1:1.") for b in blocks)


def test_parse_book_chapters_from_html_skips_commentary() -> None:
    soup = eb.BeautifulSoup(SAMPLE_HTML, "html.parser")
    first = soup.find("a", id="Book01")
    second = soup.find("a", id="Book02")
    assert first is not None
    assert second is not None
    stats = eb.ParseStats()
    chapters = eb.parse_book_chapters_from_html(first, second, stats, "Genesis")
    assert len(chapters) == 1
    chapter_num, verses = chapters[0]
    assert chapter_num == 1
    assert [v[0] for v in verses] == ["1", "2", "3"]
    assert "commentary" not in " ".join(v[1].lower() for v in verses)
    assert stats.skipped_commentary_blocks >= 1


def test_sanitize_verse_text() -> None:
    s = eb.sanitize_verse_text("Hello [See note 1] *world*  ")
    assert "[" not in s
    assert "*" not in s
    assert "world" in s


def test_find_all_book_anchors_full_file() -> None:
    raw = Path("data_engineering/data_sources/bible_douay_rheims/raw/pg8300.html")
    if not raw.is_file():
        pytest.skip("pg8300.html not present")
    soup = eb.BeautifulSoup(raw.read_text(encoding="utf-8"), "html.parser")
    anchors = eb._iter_book_anchors(soup)
    assert len(anchors) == 73


def test_pg_order_mapping_length() -> None:
    assert len(eb.PG_ORDER_TO_CANON_INDEX) == 73
    assert len(set(eb.PG_ORDER_TO_CANON_INDEX)) == 73
