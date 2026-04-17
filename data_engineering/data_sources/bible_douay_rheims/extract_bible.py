#!/usr/bin/env python3
"""
Douay-Rheims Bible extraction from Project Gutenberg eBook #8300.

Parses the UTF-8 plain-text file into Markdown books matching the pipeline SOP:
Bible_Book_XX_Name.md with YAML frontmatter, Table of Contents, chapters, and
**verse** lines (same structure as the legacy bible-api extractor).
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

# Shared canon (73 books, filenames, sections)
canonical_books_path = Path(__file__).parent.parent
sys.path.insert(0, str(canonical_books_path))
from canonical_books import CATHOLIC_BIBLE_CANON  # noqa: E402

LOG_DIR = Path(__file__).parent.parent.parent.parent / "data_engineering" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "bible_extraction.log"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.handlers.clear()
_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
_fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
_fh.setLevel(logging.INFO)
_fh.setFormatter(_formatter)
logger.addHandler(_fh)
_ch = logging.StreamHandler()
_ch.setLevel(logging.INFO)
_ch.setFormatter(_formatter)
logger.addHandler(_ch)

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "pipeline_config.yaml"
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

try:
    with open(CONFIG_PATH, encoding="utf-8") as _cf:
        _cfg = yaml.safe_load(_cf)
    RAW_TEXT_PATH = PROJECT_ROOT / _cfg["paths"]["raw_data"]["douay_rheims"]
    OUTPUT_DIR = PROJECT_ROOT / _cfg["paths"]["final_output"]["douay_rheims"]
except (OSError, yaml.YAMLError, KeyError, TypeError) as e:
    logger.warning("Could not load pipeline config, using defaults: %s", e)
    RAW_TEXT_PATH = PROJECT_ROOT / "data_engineering/data_sources/bible_douay_rheims/raw/pg8300.txt"
    OUTPUT_DIR = PROJECT_ROOT / "data_final/bible_douay_rheims"

# Exact title lines as they appear in PG #8300 (73 books, Catholic order).
PG_BOOK_HEADERS: List[str] = [
    "THE BOOK OF GENESIS",
    "THE BOOK OF EXODUS",
    "THE BOOK OF LEVITICUS",
    "THE BOOK OF NUMBERS",
    "THE BOOK OF DEUTERONOMY",
    "THE BOOK OF JOSUE",
    "THE BOOK OF JUDGES",
    "THE BOOK OF RUTH",
    "THE FIRST BOOK OF SAMUEL, OTHERWISE CALLED THE FIRST BOOK OF KINGS",
    "THE SECOND BOOK OF KINGS",
    "THE THIRD BOOK OF KINGS",
    "THE FOURTH BOOK OF KINGS",
    "THE FIRST BOOK OF PARALIPOMENON",
    "THE SECOND BOOK OF PARALIPOMENON",
    "THE FIRST BOOK OF ESDRAS",
    "THE BOOK OF NEHEMIAS, WHICH IS CALLED THE SECOND OF ESDRAS",
    "THE BOOK OF TOBIAS",
    "THE BOOK OF JUDITH",
    "THE BOOK OF ESTHER",
    "THE BOOK OF JOB",
    "THE BOOK OF PSALMS",
    "THE BOOK OF PROVERBS",
    "ECCLESIASTES",
    "SOLOMON'S CANTICLE OF CANTICLES",
    "THE BOOK OF WISDOM",
    "ECCLESIASTICUS",
    "THE PROPHECY OF ISAIAS",
    "THE PROPHECY OF JEREMIAS",
    "THE LAMENTATIONS OF JEREMIAS",
    "THE PROPHECY OF BARUCH",
    "THE PROPHECY OF EZECHIEL",
    "THE PROPHECY OF DANIEL",
    "THE PROPHECY OF OSEE",
    "THE PROPHECY OF JOEL",
    "THE PROPHECY OF AMOS",
    "THE PROPHECY OF ABDIAS",
    "THE PROPHECY OF JONAS",
    "THE PROPHECY OF MICHEAS",
    "THE PROPHECY OF NAHUM",
    "THE PROPHECY OF HABACUC",
    "THE PROPHECY OF SOPHONIAS",
    "THE PROPHECY OF AGGEUS",
    "THE PROPHECY OF ZACHARIAS",
    "THE PROPHECY OF MALACHIAS",
    "THE FIRST BOOK OF MACHABEES",
    "THE SECOND BOOK OF MACHABEES",
    "THE HOLY GOSPEL OF JESUS CHRIST ACCORDING TO SAINT MATTHEW",
    "THE HOLY GOSPEL OF JESUS CHRIST ACCORDING TO ST. MARK",
    "THE HOLY GOSPEL OF JESUS CHRIST ACCORDING TO ST. LUKE",
    "THE HOLY GOSPEL OF JESUS CHRIST ACCORDING TO ST. JOHN",
    "THE ACTS OF THE APOSTLES",
    "THE EPISTLE OF ST. PAUL THE APOSTLE TO THE ROMANS",
    "THE FIRST EPISTLE OF ST. PAUL TO THE CORINTHIANS",
    "THE SECOND EPISTLE OF ST. PAUL TO THE CORINTHIANS",
    "THE EPISTLE OF ST. PAUL TO THE GALATIANS",
    "THE EPISTLE OF ST. PAUL TO THE EPHESIANS",
    "THE EPISTLE OF ST. PAUL TO THE PHILIPPIANS",
    "THE EPISTLE OF ST. PAUL TO THE COLOSSIANS",
    "THE FIRST EPISTLE OF ST. PAUL TO THE THESSALONIANS",
    "THE SECOND EPISTLE OF ST. PAUL TO THE THESSALONIANS",
    "THE FIRST EPISTLE OF ST. PAUL TO TIMOTHY",
    "THE SECOND EPISTLE OF ST. PAUL TO TIMOTHY",
    "THE EPISTLE OF ST. PAUL TO TITUS",
    "THE EPISTLE OF ST. PAUL TO PHILEMON",
    "THE EPISTLE OF ST. PAUL TO THE HEBREWS",
    "THE CATHOLIC EPISTLE OF ST. JAMES THE APOSTLE",
    "THE FIRST EPISTLE OF ST. PETER THE APOSTLE",
    "THE SECOND EPISTLE OF ST. PETER THE APOSTLE",
    "THE FIRST EPISTLE OF ST. JOHN THE APOSTLE",
    "THE SECOND EPISTLE OF ST. JOHN THE APOSTLE",
    "THE THIRD EPISTLE OF ST. JOHN THE APOSTLE",
    "THE CATHOLIC EPISTLE OF ST. JUDE",
    "THE APOCALYPSE OF ST. JOHN THE APOSTLE",
]

# PG #8300 file order differs from Catholic canon order (Job & Psalms–Sirach
# appear before 1–2 Maccabees). Map each PG book index 0..72 -> index into
# CATHOLIC_BIBLE_CANON (same canonical_position / filenames as before).
PG_ORDER_TO_CANON_INDEX: List[int] = (
    list(range(19))  # Genesis–Esther
    + [21]  # Job
    + [22, 23, 24, 25, 26, 27]  # Psalms–Sirach
    + list(range(28, 46))  # Isaiah–Malachi
    + [19, 20]  # 1–2 Maccabees
    + list(range(46, 73))  # Matthew–Revelation
)

VERSE_START_RE = re.compile(r"^(\d+):(\d+)\.\s*(.*)$")
CHAPTER_HEADING_RE = re.compile(r"^(.+?)\s+Chapter\s+(\d+)\s*$")
# Footnotes / bracketed notes (Challoner annotations in brackets)
BRACKETED_RE = re.compile(r"\[[^\]]*\]")
# Emphasis asterisks often used around words in the PG text
EMPHASIS_ASTERISKS_RE = re.compile(r"\*+([^*]+?)\*+")


def trim_gutenberg_ebook(text: str) -> str:
    """Keep only the body between PG START and END markers."""
    upper = text.upper()
    start_tag = "*** START OF THE PROJECT GUTENBERG EBOOK"
    end_tag = "*** END OF THE PROJECT GUTENBERG EBOOK"
    si = upper.find(start_tag)
    if si == -1:
        raise ValueError("Missing Project Gutenberg START marker in source text")
    # Content begins after the first line containing START
    start_line_end = text.find("\n", si)
    if start_line_end == -1:
        body_start = si
    else:
        body_start = start_line_end + 1
    ei = upper.find(end_tag, body_start)
    if ei == -1:
        raise ValueError("Missing Project Gutenberg END marker in source text")
    return text[body_start:ei]


def sanitize_verse_text(text: str) -> str:
    """Audio-first cleanup: bracketed notes, editorial asterisks, whitespace."""
    s = BRACKETED_RE.sub("", text)
    s = EMPHASIS_ASTERISKS_RE.sub(r"\1", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _is_continuation_line(stripped: str, acc_lines: List[str]) -> bool:
    """Heuristic: wrapped verse vs interlinear Challoner commentary (no verse prefix)."""
    if not stripped:
        return False
    first = stripped[0]
    if first in "\"'(":
        return True
    if first.islower():
        return True
    chunk = " ".join(acc_lines).rstrip()
    if chunk:
        last = chunk[-1]
        if last not in ".!?;:)\"'" and not chunk.endswith("etc"):
            return True
    return False


def parse_verses_from_lines(lines: List[str]) -> List[Tuple[str, str]]:
    """Return (verse_display_number, text) for scripture lines only."""
    verses: List[Tuple[str, str]] = []
    current_num: Optional[str] = None
    current_parts: Optional[List[str]] = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        m = VERSE_START_RE.match(stripped)
        if m:
            if current_num is not None and current_parts is not None:
                raw = " ".join(current_parts)
                verses.append((current_num, sanitize_verse_text(raw)))
            # Second number is always the verse index in this edition (incl. Psalms).
            current_num = m.group(2)
            current_parts = [m.group(3)] if m.group(3) else []
            continue
        if current_num is None:
            continue
        assert current_parts is not None
        if _is_continuation_line(stripped, current_parts):
            current_parts.append(stripped)
        # Else: commentary line — skip until next numbered verse
    if current_num is not None and current_parts is not None:
        raw = " ".join(current_parts)
        verses.append((current_num, sanitize_verse_text(raw)))
    return verses


def split_book_into_chapters(
    book_lines: List[str],
) -> List[Tuple[int, List[str]]]:
    """Return list of (chapter_number, lines for that chapter body)."""
    chapter_indices: List[Tuple[int, int, str]] = []
    for i, line in enumerate(book_lines):
        s = line.strip()
        m = CHAPTER_HEADING_RE.match(s)
        if m:
            ch_num = int(m.group(2))
            chapter_indices.append((i, ch_num, m.group(1).strip()))

    if not chapter_indices:
        logger.warning("No chapter headings found in book slice (first lines may be intro only)")
        return []

    chapters: List[Tuple[int, List[str]]] = []
    for j, (line_idx, ch_num, _title) in enumerate(chapter_indices):
        end = chapter_indices[j + 1][0] if j + 1 < len(chapter_indices) else len(book_lines)
        body = book_lines[line_idx + 1 : end]
        chapters.append((ch_num, body))
    return chapters


def find_book_header_line_indices(lines: List[str]) -> List[int]:
    """0-based line indices where each PG book title appears (in order)."""
    want = 0
    found: List[int] = []
    for i, line in enumerate(lines):
        if want >= len(PG_BOOK_HEADERS):
            break
        if line.strip() == PG_BOOK_HEADERS[want]:
            found.append(i)
            want += 1
    if want != len(PG_BOOK_HEADERS):
        raise ValueError(
            f"Expected {len(PG_BOOK_HEADERS)} book headers in order, matched {want}"
        )
    return found


def safe_filename_component(name: str) -> str:
    safe = "".join(c for c in name if c.isalnum() or c in (" ", "-", "_")).strip()
    return safe.replace(" ", "_")


def write_book_markdown(
    book_meta: Dict[str, Any],
    chapters_data: List[Tuple[int, List[Tuple[str, str]]]],
    output_folder: Path,
    max_chapters: Optional[int] = None,
) -> bool:
    """Write one Bible_Book_XX_Name.md file."""
    book_name = book_meta["name"]
    book_id = book_meta["id"]
    canonical_position = book_meta["canonical_position"]
    section = book_meta.get("section") or ""
    testament = "Old Testament" if canonical_position <= 46 else "New Testament"

    total_chapters_in_book = len(chapters_data)
    chapters_to_write = chapters_data[:max_chapters] if max_chapters else chapters_data
    chapters_processed = len(chapters_to_write)

    filename = f"Bible_Book_{canonical_position:02d}_{safe_filename_component(book_name)}.md"
    filepath = output_folder / filename

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("---\n")
            f.write(f"title: {book_name}\n")
            f.write(f"canonical_position: {canonical_position}\n")
            f.write(f"testament: {testament}\n")
            if section:
                f.write(f"section: {section}\n")
            f.write(f"book_id: {book_id}\n")
            f.write(
                "translation: Douay-Rheims (Challoner revision, Project Gutenberg #8300)\n"
            )
            f.write(f"total_chapters: {total_chapters_in_book}\n")
            if max_chapters and chapters_processed < total_chapters_in_book:
                f.write(
                    f"chapters_included: {chapters_processed} "
                    f"(test mode, limited from {total_chapters_in_book})\n"
                )
            f.write("tags:\n")
            f.write("  - bible\n")
            f.write("  - douay-rheims\n")
            f.write(f"  - {testament.lower().replace(' ', '-')}\n")
            if section:
                f.write(f"  - {section.lower().replace(' ', '-')}\n")
            f.write("  - catholic-canon\n")
            f.write("language: en\n")
            f.write("format: markdown\n")
            f.write("---\n\n")

            f.write(f"# {book_name}\n\n")
            f.write("## Table of Contents\n\n")
            for ch_num, _ in chapters_to_write:
                anchor = f"chapter-{ch_num}".lower()
                f.write(f"- [Chapter {ch_num}](#{anchor})\n")
            f.write("\n---\n\n")

            for ch_num, verse_list in chapters_to_write:
                f.write(f"## Chapter {ch_num}\n\n")
                for vnum, vtext in verse_list:
                    if not vtext:
                        continue
                    f.write(f"**{vnum}** {vtext}  \n")
                f.write("\n---\n\n")

        logger.info("Saved %s (%s chapters)", book_name, chapters_processed)
        return True
    except OSError as e:
        logger.error("Error writing %s: %s", book_name, e, exc_info=True)
        return False


def extract_single_book(
    book_lines: List[str],
    book_meta: Dict[str, Any],
    max_chapters: Optional[int],
) -> Optional[List[Tuple[int, List[Tuple[str, str]]]]]:
    """Parse chapters and verses for one book."""
    chapter_slices = split_book_into_chapters(book_lines)
    if not chapter_slices:
        return None

    chapters_out: List[Tuple[int, List[Tuple[str, str]]]] = []
    for ch_num, ch_body in chapter_slices:
        verses = parse_verses_from_lines(ch_body)
        if not verses:
            logger.error("No verses parsed for %s chapter %s", book_meta["name"], ch_num)
            return None
        chapters_out.append((ch_num, verses))

    if max_chapters:
        chapters_out = chapters_out[:max_chapters]
    return chapters_out


def run_extraction(
    raw_path: Path,
    output_folder: Path,
    test_mode: bool = False,
    test_limit: int = 4,
    max_chapters: Optional[int] = None,
) -> int:
    """Run full extraction. Returns 0 on success."""
    if not raw_path.is_file():
        logger.error("Source file not found: %s", raw_path)
        return 1

    text = raw_path.read_text(encoding="utf-8")
    try:
        body = trim_gutenberg_ebook(text)
    except ValueError as e:
        logger.error("%s", e)
        return 1

    lines = body.splitlines()
    boundaries = find_book_header_line_indices(lines)

    output_folder.mkdir(parents=True, exist_ok=True)

    success = 0
    if test_mode:
        pg_indices_to_run = list(range(min(test_limit, 73)))
    else:
        pg_indices_to_run = list(range(73))

    for run_i, pg_idx in enumerate(pg_indices_to_run):
        canon_idx = PG_ORDER_TO_CANON_INDEX[pg_idx]
        book_meta = CATHOLIC_BIBLE_CANON[canon_idx]
        start = boundaries[pg_idx] + 1
        end = boundaries[pg_idx + 1] if pg_idx + 1 < len(boundaries) else len(lines)
        slice_lines = lines[start:end]

        logger.info(
            "Processing %s (%s) PG %s/%s",
            book_meta["name"],
            book_meta["id"],
            run_i + 1,
            len(pg_indices_to_run),
        )

        chapters_data = extract_single_book(slice_lines, book_meta, max_chapters)
        if not chapters_data:
            logger.error("Failed to parse book %s", book_meta["name"])
            return 1

        if not write_book_markdown(
            book_meta, chapters_data, output_folder, max_chapters=max_chapters
        ):
            return 1
        success += 1

    expected = len(pg_indices_to_run)
    logger.info("Finished: %s books written to %s", success, output_folder)
    return 0 if success == expected else 1


def main(
    test_mode: bool = False,
    test_limit: int = 4,
    max_chapters: Optional[int] = None,
    raw_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> int:
    rp = raw_path or RAW_TEXT_PATH
    od = output_dir or OUTPUT_DIR
    logger.info("Source: %s", rp)
    logger.info("Output: %s", od)
    return run_extraction(rp, od, test_mode=test_mode, test_limit=test_limit, max_chapters=max_chapters)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract Douay-Rheims Bible (PG #8300) to Markdown"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Process only first N books (see --test-limit)",
    )
    parser.add_argument("--test-limit", type=int, default=4)
    parser.add_argument(
        "--max-chapters",
        type=int,
        default=None,
        help="With --test: limit chapters per book (default 3; 0 = all chapters)",
    )
    parser.add_argument("--raw", type=Path, default=None, help="Override path to pg8300.txt")
    parser.add_argument("--output", type=Path, default=None, help="Override output directory")
    args = parser.parse_args()
    if args.test:
        if args.max_chapters == 0:
            mc: Optional[int] = None
        elif args.max_chapters is not None:
            mc = args.max_chapters
        else:
            mc = 3
    else:
        mc = None
    sys.exit(
        main(
            test_mode=args.test,
            test_limit=args.test_limit,
            max_chapters=mc,
            raw_path=args.raw,
            output_dir=args.output,
        )
    )
