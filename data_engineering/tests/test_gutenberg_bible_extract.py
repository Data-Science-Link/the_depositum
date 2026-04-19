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

# Mirrors PG #8300 Leviticus 16: verse ends with comma, then a separate <p> Challoner note
# ("Enter not...") was incorrectly merged as a line wrap; it must be skipped.
SAMPLE_HTML_LEV_COMMENTARY = """
<html><body>
<a id="Book01"></a>
<p>Leviticus Chapter 16</p>
<p>16:2. And he commanded him, saying: Speak to Aaron thy brother, that
            he enter not at all into the sanctuary, which is within the
            veil before the propitiatory, with which the ark is covered,
            lest he die, (for I will appear in a cloud over the oracle),</p>
<p>Enter not... No one but the high priest, and he but once a year,
            could enter into the sanctuary; to signify that no one could
            enter into the sanctuary of heaven, till Christ our high priest
            opened it by his passion. Heb. 10.8.</p>
<p>16:3. Unless he first do these things. He shall offer a calf for
            sin, and a ram for a holocaust.</p>
<a id="Book02"></a>
</body></html>
"""

# PG sometimes uses "4." / "5." instead of "3:4." between full "chapter:verse." labels (see Nehemiah 3).
SAMPLE_HTML_BARE_VERSES = """
<html><body>
<a id="Book01"></a>
<p>X Chapter 3</p>
<p>3:3. But the fish gate the sons of Asnaa built.</p>
<p>4. And next to him built Mosollam the son of Barachias.</p>
<p>5. And next to them the Thecuites built.</p>
<p>3:6. And Joiada the son of Phasea built the old gate.</p>
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


def test_skips_challoner_note_after_comma_ended_verse() -> None:
    soup = eb.BeautifulSoup(SAMPLE_HTML_LEV_COMMENTARY, "html.parser")
    first = soup.find("a", id="Book01")
    second = soup.find("a", id="Book02")
    assert first is not None
    assert second is not None
    stats = eb.ParseStats()
    chapters = eb.parse_book_chapters_from_html(first, second, stats, "Leviticus")
    assert len(chapters) == 1
    _, verses = chapters[0]
    assert [v[0] for v in verses] == ["2", "3"]
    text2 = next(v[1] for v in verses if v[0] == "2")
    assert "Christ" not in text2
    assert "sanctuary of heaven" not in text2
    assert "oracle" in text2
    assert stats.skipped_commentary_blocks >= 1


def test_bare_verse_only_mid_chapter() -> None:
    soup = eb.BeautifulSoup(SAMPLE_HTML_BARE_VERSES, "html.parser")
    first = soup.find("a", id="Book01")
    second = soup.find("a", id="Book02")
    assert first is not None and second is not None
    stats = eb.ParseStats()
    chapters = eb.parse_book_chapters_from_html(first, second, stats, "Nehemiah")
    assert len(chapters) == 1
    _, verses = chapters[0]
    assert [v[0] for v in verses] == ["3", "4", "5", "6"]
    assert "Mosollam" in next(t for n, t in verses if n == "4")
    assert any(e["type"] == "bare_verse_label" for e in stats.audit_events)


def test_looks_like_challoner_commentary_paragraph() -> None:
    assert eb._looks_like_challoner_commentary_paragraph(
        "Enter not... No one but the high priest."
    )
    assert not eb._looks_like_challoner_commentary_paragraph(
        "and darkness was upon the face of the deep."
    )


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
