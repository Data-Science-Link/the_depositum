#!/usr/bin/env python3
"""Structural and internal integrity checks for Douay-Rheims Bible output."""

from __future__ import annotations

import json
import random
import re
from difflib import SequenceMatcher
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from bs4 import BeautifulSoup
import requests

from data_engineering.data_sources.bible_douay_rheims import extract_bible as html_parser
from data_engineering.data_sources.canonical_books import CATHOLIC_BIBLE_CANON

BOOK_FILE_RE = re.compile(r"^Bible_Book_(\d{2})_(.+)\.md$")
CHAPTER_RE = re.compile(r"^## Chapter (\d+)\s*$")
VERSE_RE = re.compile(r"^\*\*(\d+)\*\*\s+(.*)\s*$")

HISTORY_JSONL = Path("data_engineering/logs/bible_integrity_history.jsonl")
AUDIT_LOG = Path("data_engineering/logs/bible_extraction_audit.log")
TREND_ALERT_THRESHOLD = 0.20  # 20%
VALIDATION_LATEST_MD = Path(
    "data_engineering/data_sources/bible_douay_rheims/accuracy_reports/bible_parsing_accuracy_report.md"
)
VALIDATION_LATEST_JSON = Path(
    "data_engineering/data_sources/bible_douay_rheims/accuracy_reports/bible_parsing_accuracy_report.json"
)
VALIDATION_ARCHIVE_DIR = Path(
    "data_engineering/data_sources/bible_douay_rheims/accuracy_reports/validation_reports"
)
DEFAULT_SPOTCHECK_SAMPLE_SIZE = 100
DEFAULT_SPOTCHECK_BASE_URL = "https://www.drbo.org"
NEAR_MATCH_THRESHOLD = 0.985
# After the fixed-size random sample: keep drawing until this many true mismatches (below
# near-match threshold) or this many successful comparisons—whichever comes first.
MISMATCH_HUNT_TARGET_MISMATCHES = 20
MISMATCH_HUNT_MAX_SAMPLES = 400
MISMATCH_HUNT_SEED_OFFSET = 1_000_003
CANONICAL_VARIANT_MAPPINGS: List[Tuple[str, str]] = [
    ("to morrow", "tomorrow"),
    ("bloodofferings", "blood offerings"),
    ("mayst", "mayest"),
    ("fulfil", "fulfill"),
    ("fahter", "father"),
    ("begot", "beget"),
]


@dataclass
class IntegrityResult:
    ok: bool
    errors: List[str]
    warnings: List[str]
    summary: Dict[str, object]


@dataclass
class SpotCheckSample:
    canonical_position: int
    book: str
    chapter: int
    verse: int
    local_text: str
    remote_text: Optional[str]
    local_norm: str
    remote_norm: Optional[str]
    similarity: Optional[float]
    match: Optional[bool]
    note: str


def _norm_text(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9\s]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s


def _apply_canonical_variant_mappings(s: str) -> str:
    text = s
    for src, dst in CANONICAL_VARIANT_MAPPINGS:
        text = re.sub(rf"\b{re.escape(src)}\b", dst, text)
    return text


def _normalized_compare_text(s: str) -> str:
    lowered = s.lower().strip()
    mapped = _apply_canonical_variant_mappings(lowered)
    return _norm_text(mapped)


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


def _collect_output_verses(output_dir: Path) -> List[Dict[str, object]]:
    entries: List[Dict[str, object]] = []
    for book_meta in CATHOLIC_BIBLE_CANON:
        canonical_position = int(book_meta["canonical_position"])
        book_name = str(book_meta["name"])
        md_path = output_dir / _book_filename(book_meta)
        if not md_path.is_file():
            continue
        chapters = _parse_markdown_book(md_path)
        for chapter_num, verses in chapters.items():
            for verse_num, verse_text in verses:
                entries.append(
                    {
                        "canonical_position": canonical_position,
                        "book": book_name,
                        "chapter": chapter_num,
                        "verse": verse_num,
                        "text": verse_text,
                    }
                )
    return entries


def _canonical_position_to_drbo_book_id(canonical_position: int) -> int:
    canon_idx = canonical_position - 1
    try:
        pg_idx = html_parser.PG_ORDER_TO_CANON_INDEX.index(canon_idx)
    except ValueError as exc:
        raise ValueError(f"Unable to map canonical position {canonical_position} to DRBO book ID") from exc
    return pg_idx + 1


def _drbo_chapter_url(base_url: str, canonical_position: int, chapter_num: int) -> str:
    drbo_book_id = _canonical_position_to_drbo_book_id(canonical_position)
    return f"{base_url.rstrip('/')}/chapter/{drbo_book_id:02d}{chapter_num:03d}.htm"


def _parse_drbo_chapter_verses(html_text: str) -> Dict[int, str]:
    soup = BeautifulSoup(html_text, "html.parser")
    verses: Dict[int, str] = {}
    body = soup.select_one("td.textarea")
    if body is None:
        return verses

    for paragraph in body.find_all("p"):
        classes = paragraph.get("class", [])
        if "note" in classes or "desc" in classes:
            continue

        for anchor in paragraph.find_all("a", class_="vn"):
            href = anchor.get("href", "")
            verse_num_match = re.search(r"[?&]l=(\d+)-", href)
            if not verse_num_match:
                continue
            verse_num = int(verse_num_match.group(1))
            text_parts: List[str] = []
            for sib in anchor.next_siblings:
                if getattr(sib, "name", None) == "a" and "vn" in (sib.get("class", []) if hasattr(sib, "get") else []):
                    break
                if hasattr(sib, "get_text"):
                    text_parts.append(sib.get_text(" ", strip=True))
                else:
                    text_parts.append(str(sib).strip())
            verse_text = " ".join(part for part in text_parts if part).strip()
            verse_text = re.sub(r"\s+", " ", verse_text).strip()
            if verse_text:
                verses[verse_num] = verse_text
    return verses


def _build_spot_sample_from_verse_row(
    row: Dict[str, object],
    chapter_cache: Dict[Tuple[int, int], Dict[int, str]],
    session: requests.Session,
    base_url: str,
    warnings: List[str],
) -> Optional[SpotCheckSample]:
    """Compare one local verse to DRBO; return None if that verse is unavailable remotely."""
    canon_pos = int(row["canonical_position"])
    chapter_num = int(row["chapter"])
    verse_num = int(row["verse"])
    local_text = str(row["text"])
    cache_key = (canon_pos, chapter_num)
    if cache_key not in chapter_cache:
        url = _drbo_chapter_url(base_url, canon_pos, chapter_num)
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()
            chapter_cache[cache_key] = _parse_drbo_chapter_verses(response.text)
        except requests.exceptions.RequestException as exc:
            warnings.append(f"DRBO fetch failed for book={canon_pos} chapter={chapter_num}: {exc}")
            chapter_cache[cache_key] = {}

    remote_chapter = chapter_cache[cache_key]
    remote_text = remote_chapter.get(verse_num)
    if remote_text is None:
        return None

    local_norm = _normalized_compare_text(local_text)
    remote_norm = _normalized_compare_text(remote_text)
    similarity = SequenceMatcher(None, local_norm, remote_norm).ratio()
    is_exact_match = local_norm == remote_norm
    is_near_match = (not is_exact_match) and similarity >= NEAR_MATCH_THRESHOLD
    return SpotCheckSample(
        canonical_position=canon_pos,
        book=str(row["book"]),
        chapter=chapter_num,
        verse=verse_num,
        local_text=local_text,
        remote_text=remote_text,
        local_norm=local_norm,
        remote_norm=remote_norm,
        similarity=similarity,
        match=(is_exact_match or is_near_match),
        note="exact_match" if is_exact_match else ("near_match" if is_near_match else "text mismatch"),
    )


def _spot_check_summary_from_samples(
    samples: List[SpotCheckSample],
    unavailable: int,
    seed: int,
    attempted_refs: int,
) -> Dict[str, object]:
    exact_matched = sum(1 for s in samples if s.note == "exact_match")
    near_matched = sum(1 for s in samples if s.note == "near_match")
    matched = exact_matched + near_matched
    mismatched = sum(1 for s in samples if s.note == "text mismatch")
    exact_pct = (100.0 * exact_matched / len(samples)) if samples else 0.0
    near_plus_exact_pct = (100.0 * matched / len(samples)) if samples else 0.0
    return {
        "sampled": len(samples),
        "exact_matched": exact_matched,
        "exact_match_percent": round(exact_pct, 2),
        "near_matched": near_matched,
        "matched": matched,
        "near_plus_exact_percent": round(near_plus_exact_pct, 2),
        "mismatched": mismatched,
        "unavailable": unavailable,
        "attempted_refs": attempted_refs,
        "seed": seed,
        "near_match_threshold": NEAR_MATCH_THRESHOLD,
    }


def _run_drbo_spot_check(
    output_dir: Path,
    sample_size: int,
    base_url: str,
    seed: int,
) -> Tuple[List[SpotCheckSample], Dict[str, object], List[str]]:
    warnings: List[str] = []
    all_verses = _collect_output_verses(output_dir)
    if not all_verses:
        warnings.append("DRBO spot-check skipped: no local Bible verses found.")
        return [], {"sampled": 0, "matched": 0, "near_matched": 0, "mismatched": 0, "unavailable": 0}, warnings

    sample_n = min(sample_size, len(all_verses))
    rng = random.Random(seed)
    shuffled = all_verses[:]
    rng.shuffle(shuffled)

    chapter_cache: Dict[Tuple[int, int], Dict[int, str]] = {}
    session = requests.Session()
    session.headers.update({"User-Agent": "the-depositum-validation/1.0"})

    samples: List[SpotCheckSample] = []
    unavailable = 0
    used_refs: set[Tuple[int, int, int]] = set()
    cursor = 0
    while len(samples) < sample_n and cursor < len(shuffled):
        row = shuffled[cursor]
        cursor += 1
        ref_key = (int(row["canonical_position"]), int(row["chapter"]), int(row["verse"]))
        if ref_key in used_refs:
            continue
        used_refs.add(ref_key)

        sample = _build_spot_sample_from_verse_row(
            row, chapter_cache, session, base_url, warnings
        )
        if sample is None:
            unavailable += 1
            continue
        samples.append(sample)

    summary = _spot_check_summary_from_samples(
        samples, unavailable, seed, len(used_refs)
    )
    return samples, summary, warnings


def _run_drbo_mismatch_hunt(
    output_dir: Path,
    target_mismatches: int,
    max_samples: int,
    base_url: str,
    seed: int,
) -> Tuple[List[SpotCheckSample], Dict[str, object], List[str]]:
    """
    Keep sampling (new shuffle) until `target_mismatches` true DRBO text mismatches
    (not near matches) or `max_samples` successful comparisons—whichever is first.
    """
    warnings: List[str] = []
    all_verses = _collect_output_verses(output_dir)
    if not all_verses:
        warnings.append("DRBO mismatch-hunt skipped: no local Bible verses found.")
        return [], {"sampled": 0, "matched": 0, "near_matched": 0, "mismatched": 0, "unavailable": 0}, warnings

    cap = min(max_samples, len(all_verses))
    rng = random.Random(seed)
    shuffled = all_verses[:]
    rng.shuffle(shuffled)

    chapter_cache: Dict[Tuple[int, int], Dict[int, str]] = {}
    session = requests.Session()
    session.headers.update({"User-Agent": "the-depositum-validation/1.0"})

    samples: List[SpotCheckSample] = []
    unavailable = 0
    used_refs: set[Tuple[int, int, int]] = set()
    cursor = 0
    true_mismatches = 0
    while (
        true_mismatches < target_mismatches
        and len(samples) < cap
        and cursor < len(shuffled)
    ):
        row = shuffled[cursor]
        cursor += 1
        ref_key = (int(row["canonical_position"]), int(row["chapter"]), int(row["verse"]))
        if ref_key in used_refs:
            continue
        used_refs.add(ref_key)

        sample = _build_spot_sample_from_verse_row(
            row, chapter_cache, session, base_url, warnings
        )
        if sample is None:
            unavailable += 1
            continue
        samples.append(sample)
        if sample.note == "text mismatch":
            true_mismatches += 1

    summary = _spot_check_summary_from_samples(
        samples, unavailable, seed, len(used_refs)
    )
    extra: Dict[str, object] = {
        "target_mismatches": target_mismatches,
        "max_samples": cap,
        "true_mismatches": true_mismatches,
        "stopped_because": (
            "target_mismatches"
            if true_mismatches >= target_mismatches
            else ("max_samples" if len(samples) >= cap else "exhausted_candidates")
        ),
    }
    merged = {**summary, **extra}
    return samples, merged, warnings


def _append_drbo_sample_table(
    lines: List[str],
    spot_samples: List[SpotCheckSample],
    spot_summary: Dict[str, object],
    *,
    variant: str,
) -> None:
    """Append summary bullets + markdown table for one DRBO comparison pass."""
    if spot_summary.get("sampled", 0) <= 0:
        lines.append(
            "- Spot-check not run." if variant == "random" else "- Mismatch hunt not run."
        )
        return

    if variant == "mismatch_hunt":
        trg = spot_summary.get("target_mismatches")
        mcap = spot_summary.get("max_samples")
        why = spot_summary.get("stopped_because", "")
        tm = spot_summary.get("true_mismatches")
        lines.append(
            f"- Stop rule: stop after `{trg}` **text mismatch** results (strict; not near match) "
            f"or after `{mcap}` successful comparisons—whichever happens first. "
            f"Observed text mismatches in this table: `{tm}`. "
            f"Stopped because: `{why}`."
        )

    lines.append(
        f"- Sample size: `{spot_summary['sampled']}` | exact: `{spot_summary['exact_matched']}` "
        f"({spot_summary['exact_match_percent']}%) | near: `{spot_summary['near_matched']}` | "
        f"exact+near: `{spot_summary['matched']}` ({spot_summary['near_plus_exact_percent']}%) | "
        f"mismatched: `{spot_summary['mismatched']}` | unavailable: `{spot_summary['unavailable']}` | "
        f"attempted_refs: `{spot_summary['attempted_refs']}` | seed: `{spot_summary['seed']}` | "
        f"near-threshold: `{spot_summary['near_match_threshold']}`"
    )
    repl_tail = (
        "until target sample size is reached or candidates are exhausted."
        if variant == "random"
        else "until the stop rule is satisfied or candidates are exhausted."
    )
    lines.append(
        "- Replacement sampling is enabled: if a sampled ref is unavailable, we keep sampling additional refs "
        + repl_tail
    )
    lines.append("")
    result_rank = {"text mismatch": 0, "near_match": 1, "exact_match": 2}
    if variant == "mismatch_hunt":
        table_samples = [s for s in spot_samples if s.note == "text mismatch"]
        lines.append(
            "- **Table:** only **text mismatch** rows (strict; below near-match threshold). "
            "Exact and near matches are omitted here but remain in the aggregate counts above."
        )
        lines.append("")
        sorted_samples = sorted(
            table_samples,
            key=lambda s: (
                0.0 if s.similarity is None else s.similarity,
                s.book,
                s.chapter,
                s.verse,
            ),
        )
    else:
        sorted_samples = sorted(
            spot_samples,
            key=lambda s: (
                result_rank.get(s.note, 99),
                0.0 if s.similarity is None else s.similarity,
                s.book,
                s.chapter,
                s.verse,
            ),
        )

    if variant == "mismatch_hunt" and not sorted_samples:
        lines.append("*No strict text mismatches occurred in this extended hunt.*")
        return

    lines.append("| Book | Ref | Result | Similarity | Local norm | DRBO norm |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for sample in sorted_samples:
        ref = f"{sample.chapter}:{sample.verse}"
        remote_norm = sample.remote_norm or ""
        similarity_text = f"{sample.similarity:.4f}" if sample.similarity is not None else ""
        lines.append(
            "| "
            f"{_escape_md_cell(sample.book)} | {ref} | {_escape_md_cell(sample.note)} | {similarity_text} | "
            f"{_escape_md_cell(sample.local_norm)} | {_escape_md_cell(remote_norm)} |"
        )


def _escape_md_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def _write_validation_report(
    result: IntegrityResult,
    spot_samples: List[SpotCheckSample],
    spot_summary: Dict[str, object],
    mismatch_hunt_samples: List[SpotCheckSample],
    mismatch_hunt_summary: Dict[str, object],
    report_timestamp: datetime,
) -> str:
    VALIDATION_LATEST_MD.parent.mkdir(parents=True, exist_ok=True)

    lines: List[str] = []
    lines.append("# Bible Validation Report")
    lines.append("")
    lines.append(f"- Generated (UTC): `{report_timestamp.isoformat()}`")
    lines.append(f"- Overall status: `{'PASS' if result.ok else 'FAIL'}`")
    lines.append("")
    lines.append("## Integrity Summary")
    lines.append("")
    lines.append(
        "Plain-English: this section reports the core structural and parser-health checks for the Bible output."
    )
    lines.append(
        "- `files_found`: whether all 73 expected Bible book files exist."
    )
    lines.append(
        "- `verses_checked`: total verses compared against parsed source `c:v.` paragraphs."
    )
    lines.append(
        "- `skipped_commentary` / `skipped_preface`: non-scripture blocks detected and excluded."
    )
    lines.append(
        "- `joined_continuations`: wrapped verse lines merged back into one verse."
    )
    lines.append("")
    for key in ("files_found", "verses_checked", "skipped_commentary", "skipped_preface", "joined_continuations"):
        if key in result.summary:
            lines.append(f"- {key}: `{result.summary[key]}`")
    lines.append("")
    lines.append("## Trend / Warnings")
    lines.append("")
    lines.append(
        "Plain-English: this checks run-to-run drift in parser behavior (especially skipped block counts)."
    )
    lines.append(
        "If this says `None`, no drift crossed the configured alert threshold, and no external spot-check fetch warnings were raised."
    )
    lines.append("")
    if result.warnings:
        for warning in result.warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- None")
    lines.append("")
    lines.append("## Integrity Errors")
    lines.append("")
    lines.append(
        "Plain-English: this is where hard validation failures appear."
    )
    lines.append(
        "Checks include: expected filenames, chapter counts, monotonic verse numbering, duplicate detection, verse-number set equality vs source, and normalized verse-text equality vs source."
    )
    lines.append(
        "If this says `None`, all those checks passed on this run."
    )
    lines.append("")
    if result.errors:
        for err in result.errors[:50]:
            lines.append(f"- {err}")
        if len(result.errors) > 50:
            lines.append(f"- ... and {len(result.errors) - 50} more")
    else:
        lines.append("- None")
    lines.append("")
    lines.append("## DRBO Spot Check")
    lines.append("")
    lines.append(
        "Plain-English: this samples random verse references and compares normalized local output to DRBO for external confidence."
    )
    lines.append(
        "Before comparison, canonical variant mappings are applied to BOTH sides to reduce false negatives from spelling variants."
    )
    lines.append("- Canonical variant mappings in use:")
    for src, dst in CANONICAL_VARIANT_MAPPINGS:
        lines.append(f"  - `{src}` -> `{dst}`")
    lines.append(
        "- `exact_matched`: normalized texts are exactly equal after mapping."
    )
    lines.append(
        "- `near_matched`: normalized texts are not exact but are above the near-match similarity threshold."
    )
    lines.append(
        "- `mismatched`: same reference found in both, but remains below the near-match threshold."
    )
    lines.append(
        "- `unavailable`: DRBO text for that sampled reference could not be retrieved/parsing-ready."
    )
    lines.append(
        "If `unavailable` is `0`, none of the attempted references failed DRBO retrieval/parsing."
    )
    lines.append("")
    _append_drbo_sample_table(lines, spot_samples, spot_summary, variant="random")

    lines.append("")
    lines.append("## DRBO Mismatch Hunt (extended sampling)")
    lines.append("")
    lines.append(
        "Plain-English: after the fixed random sample above, we run a second pass with the same "
        "comparison rules. It keeps drawing new random verses until it records **20** strict "
        "**text mismatch** outcomes (similarity strictly below the near-match threshold—not counting "
        "near matches), **or** until **400** successful comparisons are accumulated—whichever occurs "
        "first. Summary bullets below include full-run exact/near/mismatch counts; the markdown table "
        "lists **only** problematic (**text mismatch**) rows (same columns as the random sample table)."
    )
    lines.append(
        f"- Independent shuffle seed offset from the random sample seed: `{MISMATCH_HUNT_SEED_OFFSET}` "
        "(mismatch-hunt seed = random-sample seed + offset)."
    )
    lines.append("")
    _append_drbo_sample_table(
        lines,
        mismatch_hunt_samples,
        mismatch_hunt_summary,
        variant="mismatch_hunt",
    )

    report_text = "\n".join(lines) + "\n"
    VALIDATION_LATEST_MD.write_text(report_text, encoding="utf-8")

    json_payload = {
        "generated_utc": report_timestamp.isoformat(),
        "integrity_ok": result.ok,
        "summary": result.summary,
        "warnings": result.warnings,
        "errors": result.errors,
        "spotcheck": {
            "summary": spot_summary,
            "samples": [
                {
                    "canonical_position": s.canonical_position,
                    "book": s.book,
                    "chapter": s.chapter,
                    "verse": s.verse,
                    "match": s.match,
                    "note": s.note,
                    "local_text": s.local_text,
                    "remote_text": s.remote_text,
                    "local_norm": s.local_norm,
                    "remote_norm": s.remote_norm,
                    "similarity": s.similarity,
                }
                for s in spot_samples
            ],
        },
        "mismatch_hunt": {
            "summary": mismatch_hunt_summary,
            "samples": [
                {
                    "canonical_position": s.canonical_position,
                    "book": s.book,
                    "chapter": s.chapter,
                    "verse": s.verse,
                    "match": s.match,
                    "note": s.note,
                    "local_text": s.local_text,
                    "remote_text": s.remote_text,
                    "local_norm": s.local_norm,
                    "remote_norm": s.remote_norm,
                    "similarity": s.similarity,
                }
                for s in mismatch_hunt_samples
            ],
        },
    }
    VALIDATION_LATEST_JSON.write_text(json.dumps(json_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(VALIDATION_LATEST_MD)


def _source_book_chapters(raw_html_path: Path) -> List[Dict[int, Dict[int, str]]]:
    soup = BeautifulSoup(raw_html_path.read_text(encoding="utf-8"), "html.parser")
    anchors = html_parser._iter_book_anchors(soup)
    source_books: List[Dict[int, Dict[int, str]]] = []

    for pg_idx in range(73):
        stats = html_parser.ParseStats()
        current = anchors[pg_idx]
        nxt = anchors[pg_idx + 1] if pg_idx + 1 < len(anchors) else None
        canon_idx = html_parser.PG_ORDER_TO_CANON_INDEX[pg_idx]
        book_name = str(CATHOLIC_BIBLE_CANON[canon_idx]["name"])
        chapters_raw = html_parser.parse_book_chapters_from_html(current, nxt, stats, book_name)
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
    validation_cfg = dict(config.get("validation", {}).get("douay_rheims", {}))

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

    report_timestamp = datetime.now(timezone.utc)

    spot_cfg = validation_cfg.get("drbo_spot_check", {})
    if not isinstance(spot_cfg, dict):
        spot_cfg = {}
    spot_enabled = bool(spot_cfg.get("enabled", True))
    spot_size = int(spot_cfg.get("sample_size", DEFAULT_SPOTCHECK_SAMPLE_SIZE))
    spot_base_url = str(spot_cfg.get("base_url", DEFAULT_SPOTCHECK_BASE_URL))
    spot_seed = int(spot_cfg.get("seed", int(report_timestamp.timestamp())))

    spot_samples: List[SpotCheckSample] = []
    spot_summary: Dict[str, object] = {
        "sampled": 0,
        "exact_matched": 0,
        "exact_match_percent": 0.0,
        "near_matched": 0,
        "matched": 0,
        "near_plus_exact_percent": 0.0,
        "mismatched": 0,
        "unavailable": 0,
        "seed": spot_seed,
        "near_match_threshold": NEAR_MATCH_THRESHOLD,
    }
    mismatch_hunt_samples: List[SpotCheckSample] = []
    hunt_seed = spot_seed + MISMATCH_HUNT_SEED_OFFSET
    mismatch_hunt_summary: Dict[str, object] = {
        "sampled": 0,
        "exact_matched": 0,
        "exact_match_percent": 0.0,
        "near_matched": 0,
        "matched": 0,
        "near_plus_exact_percent": 0.0,
        "mismatched": 0,
        "unavailable": 0,
        "seed": hunt_seed,
        "near_match_threshold": NEAR_MATCH_THRESHOLD,
        "target_mismatches": MISMATCH_HUNT_TARGET_MISMATCHES,
        "max_samples": 0,
        "true_mismatches": 0,
        "stopped_because": "disabled",
        "attempted_refs": 0,
    }

    if spot_enabled:
        sampled, sampled_summary, sampled_warnings = _run_drbo_spot_check(
            output_dir=output_dir,
            sample_size=spot_size,
            base_url=spot_base_url,
            seed=spot_seed,
        )
        spot_samples = sampled
        spot_summary = sampled_summary
        warnings.extend(sampled_warnings)

        hunted, hunted_summary, hunt_warnings = _run_drbo_mismatch_hunt(
            output_dir=output_dir,
            target_mismatches=MISMATCH_HUNT_TARGET_MISMATCHES,
            max_samples=MISMATCH_HUNT_MAX_SAMPLES,
            base_url=spot_base_url,
            seed=hunt_seed,
        )
        mismatch_hunt_samples = hunted
        mismatch_hunt_summary = hunted_summary
        warnings.extend(hunt_warnings)

    summary: Dict[str, object] = {
        "files_found": len(md_files),
        "verses_checked": checked_verses,
        "skipped_commentary": audit_summary.get("skipped_commentary", -1),
        "skipped_preface": audit_summary.get("skipped_preface", -1),
        "joined_continuations": audit_summary.get("joined_continuations", -1),
        "spotcheck_sampled": spot_summary.get("sampled", 0),
        "spotcheck_exact_matched": spot_summary.get("exact_matched", 0),
        "spotcheck_exact_match_percent": spot_summary.get("exact_match_percent", 0.0),
        "spotcheck_near_matched": spot_summary.get("near_matched", 0),
        "spotcheck_matched": spot_summary.get("matched", 0),
        "spotcheck_near_plus_exact_percent": spot_summary.get("near_plus_exact_percent", 0.0),
        "spotcheck_mismatched": spot_summary.get("mismatched", 0),
        "spotcheck_unavailable": spot_summary.get("unavailable", 0),
        "spotcheck_seed": spot_summary.get("seed", spot_seed),
        "spotcheck_near_match_threshold": spot_summary.get("near_match_threshold", NEAR_MATCH_THRESHOLD),
        "mismatch_hunt_sampled": mismatch_hunt_summary.get("sampled", 0),
        "mismatch_hunt_true_mismatches": mismatch_hunt_summary.get("true_mismatches", 0),
        "mismatch_hunt_stopped_because": mismatch_hunt_summary.get("stopped_because", ""),
        "mismatch_hunt_seed": mismatch_hunt_summary.get("seed", hunt_seed),
    }
    report_path = _write_validation_report(
        IntegrityResult(ok=(len(errors) == 0), errors=errors, warnings=warnings, summary=summary),
        spot_samples=spot_samples,
        spot_summary=spot_summary,
        mismatch_hunt_samples=mismatch_hunt_samples,
        mismatch_hunt_summary=mismatch_hunt_summary,
        report_timestamp=report_timestamp,
    )
    summary["report_path"] = report_path
    return IntegrityResult(ok=(len(errors) == 0), errors=errors, warnings=warnings, summary=summary)

