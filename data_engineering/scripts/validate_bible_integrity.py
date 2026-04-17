#!/usr/bin/env python3
"""Structural and internal integrity checks for Douay-Rheims Bible output."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

from bs4 import BeautifulSoup

from data_engineering.data_sources.bible_douay_rheims import extract_bible as html_parser
from data_engineering.data_sources.canonical_books import CATHOLIC_BIBLE_CANON

BOOK_FILE_RE = re.compile(r"^Bible_Book_(\d{2})_(.+)\.md$")
CHAPTER_RE = re.compile(r"^## Chapter (\d+)\s*$")
VERSE_RE = re.compile(r"^\*\*(\d+)\*\*\s+(.*)\s*$")

HISTORY_JSONL = Path("data_engineering/logs/bible_integrity_history.jsonl")
AUDIT_LOG = Path("data_engineering/logs/bible_extraction_audit.log")
TREND_ALERT_THRESHOLD = 0.20  # 20%


@dataclass
class IntegrityResult:
    ok: bool
    errors: List[str]
    warnings: List[str]
    summary: Dict[str, int]


def _norm_text(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9\s]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s


def _book_filename(book_meta: Dict[str, object]) -> str:
    pos = int(book_meta["canonical_position"])
    name = str(book_meta["name"])
    safe = "".join(c for c in name if c.isalnum() or c in (" ", "-", "_")).strip().replace(" ", "_")
    return f"Bible_Book_{pos:02d}_{safe}.md"


def _parse_markdown_book(path: Path) -> Dict[int, List[Tuple[int, str]]]:
    chapters: Dict[int, List[Tuple[int, str]]] = {}
    current_chapter = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        cm = CHAPTER_RE.match(raw_line.strip())
        if cm:
            current_chapter = int(cm.group(1))
            chapters.setdefault(current_chapter, [])
            continue
        vm = VERSE_RE.match(raw_line.rstrip())
        if vm and current_chapter is not None:
            verse_num = int(vm.group(1))
            verse_text = vm.group(2)
            chapters[current_chapter].append((verse_num, verse_text))
    return chapters


def _source_book_chapters(raw_html_path: Path) -> List[Dict[int, Dict[int, str]]]:
    soup = BeautifulSoup(raw_html_path.read_text(encoding="utf-8"), "html.parser")
    anchors = html_parser._iter_book_anchors(soup)
    source_books: List[Dict[int, Dict[int, str]]] = []

    for pg_idx in range(73):
        stats = html_parser.ParseStats()
        current = anchors[pg_idx]
        nxt = anchors[pg_idx + 1] if pg_idx + 1 < len(anchors) else None
        chapters_raw = html_parser.parse_book_chapters_from_html(current, nxt, stats, f"PGBook{pg_idx+1}")
        chapter_map: Dict[int, Dict[int, str]] = {}
        for ch_num, verses in chapters_raw:
            chapter_map[ch_num] = {int(vnum): vtext for vnum, vtext in verses}
        source_books.append(chapter_map)
    return source_books


def _parse_audit_summary(audit_log_path: Path) -> Dict[str, int]:
    out = {"skipped_commentary": -1, "skipped_preface": -1, "joined_continuations": -1}
    if not audit_log_path.is_file():
        return out
    for line in audit_log_path.read_text(encoding="utf-8").splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if key in out:
            try:
                out[key] = int(value)
            except ValueError:
                continue
    return out


def _append_and_check_trend(summary: Dict[str, int]) -> List[str]:
    warnings: List[str] = []
    HISTORY_JSONL.parent.mkdir(parents=True, exist_ok=True)

    prev = None
    if HISTORY_JSONL.is_file():
        lines = [ln for ln in HISTORY_JSONL.read_text(encoding="utf-8").splitlines() if ln.strip()]
        if lines:
            try:
                prev = json.loads(lines[-1])
            except json.JSONDecodeError:
                prev = None

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "skipped_commentary": summary.get("skipped_commentary", -1),
        "skipped_preface": summary.get("skipped_preface", -1),
        "joined_continuations": summary.get("joined_continuations", -1),
    }
    with open(HISTORY_JSONL, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    if prev:
        for key in ("skipped_commentary", "skipped_preface", "joined_continuations"):
            old = int(prev.get(key, -1))
            new = int(record.get(key, -1))
            if old <= 0 or new < 0:
                continue
            delta_ratio = abs(new - old) / old
            if delta_ratio > TREND_ALERT_THRESHOLD:
                warnings.append(
                    f"Trend alert for {key}: previous={old}, current={new}, "
                    f"change={delta_ratio:.1%} (> {TREND_ALERT_THRESHOLD:.0%})"
                )
    return warnings


def validate_bible_integrity(config: Dict[str, object]) -> IntegrityResult:
    errors: List[str] = []
    warnings: List[str] = []

    output_dir = Path(str(config["paths"]["final_output"]["douay_rheims"]))
    raw_html = Path(str(config["paths"]["raw_data"]["douay_rheims"]))

    if not output_dir.is_dir():
        return IntegrityResult(False, [f"Bible output directory missing: {output_dir}"], [], {})
    if not raw_html.is_file():
        return IntegrityResult(False, [f"Bible raw HTML source missing: {raw_html}"], [], {})

    md_files = sorted(output_dir.glob("Bible_Book_*.md"))
    if len(md_files) != 73:
        errors.append(f"Expected 73 Bible markdown files, found {len(md_files)} in {output_dir}")

    expected_filenames = {_book_filename(book) for book in CATHOLIC_BIBLE_CANON}
    found_filenames = {p.name for p in md_files}
    missing = sorted(expected_filenames - found_filenames)
    unexpected = sorted(found_filenames - expected_filenames)
    if missing:
        errors.append(f"Missing expected Bible files: {', '.join(missing[:5])}" + (" ..." if len(missing) > 5 else ""))
    if unexpected:
        errors.append(
            f"Unexpected Bible files present: {', '.join(unexpected[:5])}" + (" ..." if len(unexpected) > 5 else "")
        )

    source_books = _source_book_chapters(raw_html)
    source_by_canon: Dict[int, Dict[int, Dict[int, str]]] = {}
    for pg_idx, chapter_map in enumerate(source_books):
        canon_idx = html_parser.PG_ORDER_TO_CANON_INDEX[pg_idx]
        canon_pos = int(CATHOLIC_BIBLE_CANON[canon_idx]["canonical_position"])
        source_by_canon[canon_pos] = chapter_map

    checked_verses = 0
    for book_meta in CATHOLIC_BIBLE_CANON:
        canon_pos = int(book_meta["canonical_position"])
        fname = _book_filename(book_meta)
        md_path = output_dir / fname
        if not md_path.is_file():
            continue

        md_chapters = _parse_markdown_book(md_path)
        src_chapters = source_by_canon.get(canon_pos, {})

        if len(md_chapters) != len(src_chapters):
            errors.append(
                f"{fname}: chapter count mismatch (markdown={len(md_chapters)}, source={len(src_chapters)})"
            )

        for ch_num, md_verses in md_chapters.items():
            src_verses = src_chapters.get(ch_num, {})
            verse_nums = [vnum for vnum, _ in md_verses]
            if len(verse_nums) != len(set(verse_nums)):
                errors.append(f"{fname} chapter {ch_num}: duplicate verse numbers detected")
            if verse_nums != sorted(verse_nums):
                errors.append(f"{fname} chapter {ch_num}: verse numbers are not monotonic increasing")
            if src_verses:
                source_keys = sorted(src_verses.keys())
                if verse_nums != source_keys:
                    errors.append(
                        f"{fname} chapter {ch_num}: verse-number set mismatch with source "
                        f"(markdown={len(verse_nums)}, source={len(source_keys)})"
                    )

            for verse_num, verse_text in md_verses:
                checked_verses += 1
                if verse_num not in src_verses:
                    errors.append(f"{fname} chapter {ch_num} verse {verse_num}: missing from source c:v paragraphs")
                    continue
                src_text = src_verses[verse_num]
                if _norm_text(verse_text) != _norm_text(src_text):
                    errors.append(f"{fname} chapter {ch_num} verse {verse_num}: text mismatch with source c:v paragraph")

    audit_summary = _parse_audit_summary(AUDIT_LOG)
    trend_warnings = _append_and_check_trend(audit_summary)
    warnings.extend(trend_warnings)

    summary = {
        "files_found": len(md_files),
        "verses_checked": checked_verses,
        "skipped_commentary": audit_summary.get("skipped_commentary", -1),
        "skipped_preface": audit_summary.get("skipped_preface", -1),
        "joined_continuations": audit_summary.get("joined_continuations", -1),
    }
    return IntegrityResult(ok=(len(errors) == 0), errors=errors, warnings=warnings, summary=summary)

