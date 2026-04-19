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

# Missing "Chapter 2" heading; next verse is only labeled 2:1.
SAMPLE_HTML_IMPLICIT_CHAPTER = """
<html><body>
<a id="Book01"></a>
<p>X Chapter 1</p>
<p>1:40. Last verse of chapter one.</p>
<p>2:1. First verse of chapter two without heading.</p>
<a id="Book02"></a>
</body></html>
"""

# Psalm title in 121:1., verse body in following <p> (PG #8300 pattern).
SAMPLE_HTML_PSALM_TITLE = """
<html><body>
<a id="Book01"></a>
<p>Psalms Chapter 121</p>
<p>121:1. A gradual canticle.</p>
<p>I rejoiced at the things that were said to me: We shall go into the house of the Lord.</p>
<p>121:2. Our feet were standing in thy courts, O Jerusalem.</p>
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


def test_implicit_chapter_heading_from_verse_label() -> None:
    soup = eb.BeautifulSoup(SAMPLE_HTML_IMPLICIT_CHAPTER, "html.parser")
    first = soup.find("a", id="Book01")
    second = soup.find("a", id="Book02")
    stats = eb.ParseStats()
    chapters = eb.parse_book_chapters_from_html(first, second, stats, "TestBook")
    assert [(c[0], [v[0] for v in c[1]]) for c in chapters] == [(1, ["40"]), (2, ["1"])]
    assert any(e["type"] == "recovered_implicit_chapter_heading" for e in stats.audit_events)


def test_psalms_superscription_merged_into_verse_one() -> None:
    soup = eb.BeautifulSoup(SAMPLE_HTML_PSALM_TITLE, "html.parser")
    first = soup.find("a", id="Book01")
    second = soup.find("a", id="Book02")
    stats = eb.ParseStats()
    chapters = eb.parse_book_chapters_from_html(first, second, stats, "Psalms")
    ch121 = next(c for c in chapters if c[0] == 121)
    v1 = next(t for n, t in ch121[1] if n == "1")
    assert "gradual canticle" in v1.lower()
    assert "I rejoiced" in v1
    assert "house of the Lord" in v1


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
    assert eb._looks_like_challoner_commentary_paragraph(
        "All scripture,... Every part of divine scripture is certainly profitable."
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
    raw_adjusted = Path(
        "data_engineering/data_sources/bible_douay_rheims/raw/pg8300_adjusted.html"
    )
    raw_plain = Path("data_engineering/data_sources/bible_douay_rheims/raw/pg8300.html")
    raw = raw_adjusted if raw_adjusted.is_file() else raw_plain
    if not raw.is_file():
        pytest.skip("pg8300_adjusted.html or pg8300.html not present")
    soup = eb.BeautifulSoup(raw.read_text(encoding="utf-8"), "html.parser")
    anchors = eb._iter_book_anchors(soup)
    assert len(anchors) == 73


def test_pg_order_mapping_length() -> None:
    assert len(eb.PG_ORDER_TO_CANON_INDEX) == 73
    assert len(set(eb.PG_ORDER_TO_CANON_INDEX)) == 73


def test_proverbs_chapter_12_duplicate_verse_labels_merge_not_shift() -> None:
    """PG #8300 repeats '12:12.' twice (split <p>); merging avoids off-by-one shift through ch.22+."""
    raw_adjusted = Path(
        "data_engineering/data_sources/bible_douay_rheims/raw/pg8300_adjusted.html"
    )
    if not raw_adjusted.is_file():
        pytest.skip("pg8300_adjusted.html not present")
    soup = eb.BeautifulSoup(raw_adjusted.read_text(encoding="utf-8"), "html.parser")
    anchors = eb._iter_book_anchors(soup)
    canon_idx_proverbs = 23  # 24th canon book
    pg_idx = eb.PG_ORDER_TO_CANON_INDEX.index(canon_idx_proverbs)
    stats = eb.ParseStats()
    chapters = eb.parse_book_chapters_from_html(
        anchors[pg_idx], anchors[pg_idx + 1], stats, "Proverbs"
    )
    by_num = {c[0]: dict(c[1]) for c in chapters}
    ch12 = by_num[12]
    assert len(ch12) == 28
    assert "tilleth" in ch12["11"].lower() and "wine" in ch12["11"].lower()
    assert "desire of the wicked" in ch12["12"].lower()
    assert "wine" not in ch12["12"].lower()
    assert ch12["22"].startswith("Lying lips")
    assert ch12["23"].startswith("A cautious")
