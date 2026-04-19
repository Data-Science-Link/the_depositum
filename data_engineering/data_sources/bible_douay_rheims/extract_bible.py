#!/usr/bin/env python3
"""Extract Douay-Rheims Bible from Project Gutenberg #8300 HTML."""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import yaml
from bs4 import BeautifulSoup, Tag

canonical_books_path = Path(__file__).parent.parent
sys.path.insert(0, str(canonical_books_path))
from canonical_books import CATHOLIC_BIBLE_CANON  # noqa: E402

LOG_DIR = Path(__file__).parent.parent.parent.parent / "data_engineering" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "bible_extraction.log"
AUDIT_LOG_FILE = LOG_DIR / "bible_extraction_audit.log"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.handlers.clear()
_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
_file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
_file_handler.setLevel(logging.INFO)
_file_handler.setFormatter(_formatter)
logger.addHandler(_file_handler)
_console_handler = logging.StreamHandler()
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(_formatter)
logger.addHandler(_console_handler)

CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "pipeline_config.yaml"
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

try:
    with open(CONFIG_PATH, encoding="utf-8") as _f:
        _cfg = yaml.safe_load(_f)
    RAW_HTML_PATH = PROJECT_ROOT / _cfg["paths"]["raw_data"]["douay_rheims"]
    OUTPUT_DIR = PROJECT_ROOT / _cfg["paths"]["final_output"]["douay_rheims"]
except (OSError, yaml.YAMLError, KeyError, TypeError) as e:
    logger.warning("Could not load pipeline config, using defaults: %s", e)
    RAW_HTML_PATH = PROJECT_ROOT / "data_engineering/data_sources/bible_douay_rheims/raw/pg8300.html"
    OUTPUT_DIR = PROJECT_ROOT / "data_final/bible_douay_rheims"

# PG #8300 HTML order differs from Catholic canonical filename order for Job/Maccabees.
PG_ORDER_TO_CANON_INDEX: List[int] = (
    list(range(19))
    + [21]
    + [22, 23, 24, 25, 26, 27]
    + list(range(28, 46))
    + [19, 20]
    + list(range(46, 73))
)

VERSE_START_RE = re.compile(r"^(\d+):([0-9lI]+)\.\s*(.*)$")
# PG #8300 sometimes omits "chapter:" after the first verses in a section, e.g. Neh. 3 uses
# "4. ..." / "5. ..." instead of "3:4." / "3:5.". Only accept when consecutive (next verse).
BARE_VERSE_ONLY_RE = re.compile(r"^([0-9lI]{1,3})\.\s+(.*)$")
CHAPTER_HEADING_RE = re.compile(r"^(.+?)\s+Chapter\s+(\d+)\s*$")
BRACKETED_RE = re.compile(r"\[[^\]]*\]")
EMPHASIS_ASTERISKS_RE = re.compile(r"\*+([^*]+?)\*+")
# PG #8300 emits Challoner marginal notes as separate <p> blocks (no distinct class).
# They almost always begin with a short quotation from the verse (opening words) and an
# ellipsis before the explanatory sentence, e.g. "Enter not... No one but...".
CHALLONER_NOTE_LEAD_RE = re.compile(r"^[^\n.]{1,200}\.\.\.")
# Marginal notes that quote the verse with "Word,... rest of gloss" (comma + ellipsis).
CHALLONER_COMMA_ELLIPSIS_RE = re.compile(r"^[^\n]{1,150},\.\.\.")


class ParseStats:
    def __init__(self) -> None:
        self.skipped_commentary_blocks = 0
        self.skipped_preface_blocks = 0
        self.joined_continuation_blocks = 0
        self.audit_events: List[Dict[str, Any]] = []


def sanitize_verse_text(text: str) -> str:
    s = BRACKETED_RE.sub("", text)
    s = EMPHASIS_ASTERISKS_RE.sub(r"\1", s)
    # If a marginal gloss replay was concatenated into the verse, drop common tails (PG + DRBO QC).
    s = re.sub(r"\s+\d{1,3}\.\s+all\s+scripture\b.*$", "", s, flags=re.I)
    s = re.sub(r"\s+\d{1,3}\.\s+the\s+graves\s+of\s+lust\b.*$", "", s, flags=re.I)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _looks_like_challoner_commentary_paragraph(block: str) -> bool:
    """True if this <p> text matches the Challoner marginal-note pattern used in PG #8300."""
    s = block.strip()
    if not s:
        return False
    if CHALLONER_NOTE_LEAD_RE.match(s):
        return True
    if CHALLONER_COMMA_ELLIPSIS_RE.match(s):
        return True
    return False


def _is_psalm_superscription_only_chunk(chunk: str) -> bool:
    """True when verse 1 text is only a title line and the body is in the next <p> (PG #8300)."""
    t = chunk.strip()
    if len(t) > 220:
        return False
    if re.search(
        r"(?i)\b(canticle|instruction|maskil|maschil|degrees|title|for david|"
        r"chief musician|song of|praise of a canticle|understanding for)\b",
        t,
    ):
        return True
    if re.match(r"(?i)^a\s+gradual\s+canticle\.?$", t):
        return True
    # Short clause-only openings used as headings before the body paragraph.
    return len(t) < 90 and t.endswith(".")


def _is_continuation_block(
    block: str,
    current_parts: List[str],
    book_name: str,
    current_verse_num: Optional[str],
) -> bool:
    if not block:
        return False
    if _looks_like_challoner_commentary_paragraph(block):
        return False
    # Psalms: PG often puts only the superscription in 121:1., with verse body in the next <p>.
    if (
        book_name == "Psalms"
        and current_verse_num == "1"
        and current_parts
        and not VERSE_START_RE.match(block)
        and not BARE_VERSE_ONLY_RE.match(block)
    ):
        chunk = " ".join(current_parts).strip()
        if _is_psalm_superscription_only_chunk(chunk) and block[0].isupper():
            return True
    first = block[0]
    if first in "\"'(":
        return True
    if first.islower():
        return True
    chunk = " ".join(current_parts).rstrip()
    if chunk:
        last = chunk[-1]
        if last not in ".!?;:)\"'" and not chunk.endswith("etc"):
            return True
    return False


def _iter_book_anchors(soup: BeautifulSoup) -> List[Tag]:
    anchors: List[Tag] = []
    for i in range(1, 74):
        anchor = soup.find("a", id=f"Book{i:02d}")
        if not isinstance(anchor, Tag):
            raise ValueError(f"Missing Book anchor: Book{i:02d}")
        anchors.append(anchor)
    return anchors


def _iter_paragraph_blocks(book_anchor: Tag, next_anchor: Optional[Tag]) -> Iterable[str]:
    for node in book_anchor.next_elements:
        if next_anchor is not None and node is next_anchor:
            break
        if isinstance(node, Tag) and node.name == "p":
            txt = " ".join(node.get_text(" ", strip=True).split())
            if txt:
                yield txt


def parse_book_chapters_from_html(
    book_anchor: Tag,
    next_anchor: Optional[Tag],
    stats: ParseStats,
    book_name: str,
) -> List[Tuple[int, List[Tuple[str, str]]]]:
    chapters: List[Tuple[int, List[Tuple[str, str]]]] = []

    current_chapter_num: Optional[int] = None
    current_chapter_verses: List[Tuple[str, str]] = []
    current_verse_num: Optional[str] = None
    current_verse_parts: List[str] = []

    def flush_verse() -> None:
        nonlocal current_verse_num, current_verse_parts
        if current_verse_num is None:
            return
        verse_text = sanitize_verse_text(" ".join(current_verse_parts))
        if verse_text:
            current_chapter_verses.append((current_verse_num, verse_text))
        current_verse_num = None
        current_verse_parts = []

    def flush_chapter() -> None:
        nonlocal current_chapter_num, current_chapter_verses
        flush_verse()
        if current_chapter_num is not None and current_chapter_verses:
            chapters.append((current_chapter_num, current_chapter_verses.copy()))
        current_chapter_num = None
        current_chapter_verses = []

    for block in _iter_paragraph_blocks(book_anchor, next_anchor):
        chapter_match = CHAPTER_HEADING_RE.match(block)
        if chapter_match:
            flush_chapter()
            current_chapter_num = int(chapter_match.group(2))
            continue

        verse_match = VERSE_START_RE.match(block)
        if verse_match:
            if current_chapter_num is None:
                continue
            verse_chapter_num = int(verse_match.group(1))
            raw_verse_token = verse_match.group(2)
            normalized_verse_token = raw_verse_token.replace("l", "1").replace("I", "1")
            try:
                verse_num_candidate = int(normalized_verse_token)
            except ValueError:
                stats.skipped_commentary_blocks += 1
                stats.audit_events.append(
                    {
                        "type": "skipped_unparseable_verse_token",
                        "book": book_name,
                        "chapter": current_chapter_num,
                        "verse": current_verse_num,
                        "text": block,
                    }
                )
                continue

            if raw_verse_token != normalized_verse_token:
                stats.audit_events.append(
                    {
                        "type": "recovered_ocr_verse_token",
                        "book": book_name,
                        "chapter": current_chapter_num,
                        "verse": current_verse_num,
                        "text": block,
                    }
                )
            if (
                current_verse_num is None
                and verse_num_candidate == 1
                and verse_chapter_num == current_chapter_num - 1
            ):
                # PG #8300 occasionally mislabels the first verse in a chapter
                # with the previous chapter number (e.g., 3 Kings Chapter 2 starts
                # with "1:1. ..."). Recover it as current chapter verse 1.
                stats.audit_events.append(
                    {
                        "type": "recovered_first_verse_chapter_mismatch",
                        "book": book_name,
                        "chapter": current_chapter_num,
                        "verse": None,
                        "text": block,
                    }
                )
                verse_chapter_num = current_chapter_num
            elif (
                current_verse_num is not None
                and verse_chapter_num == current_chapter_num - 1
                and verse_num_candidate == int(current_verse_num)
            ):
                # Another Gutenberg OCR pattern: the chapter number is one less, and the
                # verse number repeats the current verse (e.g., Psalm 6 has "5:5." where
                # context requires current chapter verse +1). Recover as the next verse.
                verse_chapter_num = current_chapter_num
                verse_num_candidate = int(current_verse_num) + 1
                stats.audit_events.append(
                    {
                        "type": "recovered_prev_chapter_same_verse_label",
                        "book": book_name,
                        "chapter": current_chapter_num,
                        "verse": current_verse_num,
                        "text": block,
                    }
                )
            if verse_chapter_num != current_chapter_num:
                # Missing chapter heading in PG: next section starts with "32:1." while still on ch 31.
                if verse_chapter_num > current_chapter_num and verse_num_candidate == 1:
                    flush_verse()
                    if current_chapter_num is not None and current_chapter_verses:
                        chapters.append((current_chapter_num, current_chapter_verses.copy()))
                    current_chapter_verses = []
                    current_chapter_num = verse_chapter_num
                    stats.audit_events.append(
                        {
                            "type": "recovered_implicit_chapter_heading",
                            "book": book_name,
                            "chapter": current_chapter_num,
                            "verse": current_verse_num,
                            "text": block,
                        }
                    )
                else:
                    # Commentary blocks sometimes cite c:v references from elsewhere.
                    stats.skipped_commentary_blocks += 1
                    stats.audit_events.append(
                        {
                            "type": "skipped_crossref_paragraph",
                            "book": book_name,
                            "chapter": current_chapter_num,
                            "verse": current_verse_num,
                            "text": block,
                        }
                    )
                    continue
            if current_verse_num is not None and verse_num_candidate <= int(current_verse_num):
                # Gutenberg occasionally repeats a verse label by mistake (e.g., 2:3 then 2:3
                # where the second is contextually verse 4). If it's exactly repeated, recover
                # to next verse number; otherwise treat as cross-reference commentary.
                if verse_num_candidate == int(current_verse_num):
                    adjusted_current = int(current_verse_num)
                    if current_chapter_verses:
                        prev_committed_num = int(current_chapter_verses[-1][0])
                        if adjusted_current - prev_committed_num == 2:
                            # Fix pattern like 1,3,3 where the first "3" is really "2".
                            adjusted_current = adjusted_current - 1
                    current_verse_num = str(adjusted_current)
                    verse_num_candidate = int(current_verse_num) + 1
                    stats.audit_events.append(
                        {
                            "type": "recovered_duplicate_verse_label",
                            "book": book_name,
                            "chapter": current_chapter_num,
                            "verse": current_verse_num,
                            "text": block,
                        }
                    )
                else:
                    # Gutenberg OCR can occasionally drop the tens digit by one near chapter
                    # ends (e.g., 30:19 where context indicates 30:29). Recover when this
                    # looks like the immediate next verse.
                    if verse_num_candidate + 10 == int(current_verse_num) + 1:
                        verse_num_candidate = int(current_verse_num) + 1
                        stats.audit_events.append(
                            {
                                "type": "recovered_tens_digit_ocr_verse_label",
                                "book": book_name,
                                "chapter": current_chapter_num,
                                "verse": current_verse_num,
                                "text": block,
                            }
                        )
                    else:
                        stats.skipped_commentary_blocks += 1
                        stats.audit_events.append(
                            {
                                "type": "skipped_nonincreasing_crossref",
                                "book": book_name,
                                "chapter": current_chapter_num,
                                "verse": current_verse_num,
                                "text": block,
                            }
                        )
                        continue
            flush_verse()
            current_verse_num = str(verse_num_candidate)
            current_verse_parts = [verse_match.group(3)] if verse_match.group(3) else []
            continue

        bare_match = BARE_VERSE_ONLY_RE.match(block)
        if bare_match and current_chapter_num is not None and current_verse_num is not None:
            normalized_bare = bare_match.group(1).replace("l", "1").replace("I", "1")
            bare_body = bare_match.group(2)
            try:
                bare_next = int(normalized_bare)
            except ValueError:
                bare_next = None
            if bare_next is not None:
                prev_n = int(current_verse_num)
                if (
                    bare_next == prev_n + 1
                    and not _looks_like_challoner_commentary_paragraph(block)
                ):
                    flush_verse()
                    current_verse_num = str(bare_next)
                    current_verse_parts = [bare_body] if bare_body else []
                    stats.audit_events.append(
                        {
                            "type": "bare_verse_label",
                            "book": book_name,
                            "chapter": current_chapter_num,
                            "verse": current_verse_num,
                            "text": block,
                        }
                    )
                    continue

        if current_chapter_num is None:
            stats.skipped_preface_blocks += 1
            stats.audit_events.append(
                {
                    "type": "preface_or_intro",
                    "book": book_name,
                    "chapter": None,
                    "verse": None,
                    "text": block,
                }
            )
            continue

        if current_verse_num is None:
            stats.skipped_preface_blocks += 1
            stats.audit_events.append(
                {
                    "type": "chapter_preface",
                    "book": book_name,
                    "chapter": current_chapter_num,
                    "verse": None,
                    "text": block,
                }
            )
            continue

        if _is_continuation_block(
            block, current_verse_parts, book_name, current_verse_num
        ):
            current_verse_parts.append(block)
            stats.joined_continuation_blocks += 1
            stats.audit_events.append(
                {
                    "type": "continuation",
                    "book": book_name,
                    "chapter": current_chapter_num,
                    "verse": current_verse_num,
                    "text": block,
                }
            )
        else:
            stats.skipped_commentary_blocks += 1
            stats.audit_events.append(
                {
                    "type": "skipped_commentary",
                    "book": book_name,
                    "chapter": current_chapter_num,
                    "verse": current_verse_num,
                    "text": block,
                }
            )

    flush_chapter()
    return chapters


def safe_filename_component(name: str) -> str:
    safe = "".join(c for c in name if c.isalnum() or c in (" ", "-", "_")).strip()
    return safe.replace(" ", "_")


def write_book_markdown(
    book_meta: Dict[str, Any],
    chapters_data: List[Tuple[int, List[Tuple[str, str]]]],
    output_folder: Path,
    max_chapters: Optional[int] = None,
) -> bool:
    book_name = str(book_meta["name"])
    book_id = str(book_meta["id"])
    canonical_position = int(book_meta["canonical_position"])
    section = str(book_meta.get("section") or "")
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
            f.write("translation: Douay-Rheims (Challoner revision, Project Gutenberg #8300)\n")
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
            for chapter_num, _ in chapters_to_write:
                f.write(f"- [Chapter {chapter_num}](#chapter-{chapter_num})\n")
            f.write("\n---\n\n")

            for chapter_num, verses in chapters_to_write:
                f.write(f"## Chapter {chapter_num}\n\n")
                for verse_num, verse_text in verses:
                    f.write(f"**{verse_num}** {verse_text}  \n")
                f.write("\n---\n\n")
        return True
    except OSError as e:
        logger.error("Error writing %s: %s", book_name, e, exc_info=True)
        return False


def run_extraction(
    raw_path: Path,
    output_folder: Path,
    test_mode: bool = False,
    test_limit: int = 4,
    max_chapters: Optional[int] = None,
    audit_log_path: Path = AUDIT_LOG_FILE,
) -> int:
    if not raw_path.is_file():
        logger.error("Source file not found: %s", raw_path)
        return 1

    try:
        html = raw_path.read_text(encoding="utf-8")
    except OSError as e:
        logger.error("Failed to read source HTML file %s: %s", raw_path, e, exc_info=True)
        return 1

    soup = BeautifulSoup(html, "html.parser")

    try:
        book_anchors = _iter_book_anchors(soup)
    except ValueError as e:
        logger.error("%s", e)
        return 1

    output_folder.mkdir(parents=True, exist_ok=True)

    if test_mode:
        pg_indices_to_run = list(range(min(test_limit, 73)))
    else:
        pg_indices_to_run = list(range(73))

    total_skipped_commentary = 0
    total_skipped_preface = 0
    total_joined_continuation = 0
    all_audit_events: List[Dict[str, Any]] = []

    written = 0
    for run_idx, pg_idx in enumerate(pg_indices_to_run):
        canon_idx = PG_ORDER_TO_CANON_INDEX[pg_idx]
        book_meta = CATHOLIC_BIBLE_CANON[canon_idx]
        book_anchor = book_anchors[pg_idx]
        next_anchor = book_anchors[pg_idx + 1] if pg_idx + 1 < len(book_anchors) else None

        stats = ParseStats()
        chapters_data = parse_book_chapters_from_html(
            book_anchor, next_anchor, stats, str(book_meta["name"])
        )
        if not chapters_data:
            logger.error("No chapters parsed for %s", book_meta["name"])
            return 1

        if max_chapters:
            chapters_data = chapters_data[:max_chapters]

        if not write_book_markdown(book_meta, chapters_data, output_folder, max_chapters=max_chapters):
            return 1

        written += 1
        total_skipped_commentary += stats.skipped_commentary_blocks
        total_skipped_preface += stats.skipped_preface_blocks
        total_joined_continuation += stats.joined_continuation_blocks
        all_audit_events.extend(stats.audit_events)
        logger.info(
            "Saved %s (%s chapters) [skipped commentary blocks: %s]",
            book_meta["name"],
            len(chapters_data),
            stats.skipped_commentary_blocks,
        )
        logger.info("Progress: %s/%s", run_idx + 1, len(pg_indices_to_run))

    logger.info("Finished: %s books written to %s", written, output_folder)
    logger.info(
        "Parsing diagnostics: skipped_commentary=%s skipped_preface=%s joined_continuations=%s",
        total_skipped_commentary,
        total_skipped_preface,
        total_joined_continuation,
    )

    try:
        with open(audit_log_path, "w", encoding="utf-8") as f:
            f.write("Douay-Rheims HTML extraction audit log\n")
            f.write(f"source={raw_path}\n")
            f.write(f"books_written={written}\n")
            f.write(f"skipped_commentary={total_skipped_commentary}\n")
            f.write(f"skipped_preface={total_skipped_preface}\n")
            f.write(f"joined_continuations={total_joined_continuation}\n")
            f.write(f"events={len(all_audit_events)}\n")
            f.write("---\n")
            for event in all_audit_events:
                chapter = event["chapter"] if event["chapter"] is not None else "-"
                verse = event["verse"] if event["verse"] is not None else "-"
                text = str(event["text"]).replace("\n", " ").strip()
                f.write(
                    f"{event['type']} | {event['book']} | chapter={chapter} | "
                    f"verse={verse} | {text}\n"
                )
    except OSError as e:
        logger.error("Failed writing audit log %s: %s", audit_log_path, e, exc_info=True)
        return 1

    logger.info("Audit log written to %s", audit_log_path)
    return 0 if written == len(pg_indices_to_run) else 1


def main(
    test_mode: bool = False,
    test_limit: int = 4,
    max_chapters: Optional[int] = None,
    raw_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    audit_log_path: Optional[Path] = None,
) -> int:
    rp = raw_path or RAW_HTML_PATH
    od = output_dir or OUTPUT_DIR
    ap = audit_log_path or AUDIT_LOG_FILE
    logger.info("Source: %s", rp)
    logger.info("Output: %s", od)
    logger.info("Audit log: %s", ap)
    return run_extraction(
        raw_path=rp,
        output_folder=od,
        test_mode=test_mode,
        test_limit=test_limit,
        max_chapters=max_chapters,
        audit_log_path=ap,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract Douay-Rheims Bible (PG #8300 HTML)")
    parser.add_argument("--test", action="store_true", help="Process only first N books")
    parser.add_argument("--test-limit", type=int, default=4)
    parser.add_argument(
        "--max-chapters",
        type=int,
        default=None,
        help="With --test: limit chapters per book (default 3; 0 = all chapters)",
    )
    parser.add_argument("--raw", type=Path, default=None, help="Override path to pg8300.html")
    parser.add_argument("--output", type=Path, default=None, help="Override output directory")
    parser.add_argument(
        "--audit-log",
        type=Path,
        default=None,
        help="Override audit log path (default: data_engineering/logs/bible_extraction_audit.log)",
    )

    args = parser.parse_args()
    if args.test:
        if args.max_chapters == 0:
            parsed_max_chapters: Optional[int] = None
        elif args.max_chapters is not None:
            parsed_max_chapters = args.max_chapters
        else:
            parsed_max_chapters = 3
    else:
        parsed_max_chapters = None

    sys.exit(
        main(
            test_mode=args.test,
            test_limit=args.test_limit,
            max_chapters=parsed_max_chapters,
            raw_path=args.raw,
            output_dir=args.output,
            audit_log_path=args.audit_log,
        )
    )
