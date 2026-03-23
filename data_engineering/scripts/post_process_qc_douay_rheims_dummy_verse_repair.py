#!/usr/bin/env python3
"""
QC for Douay-Rheims dummy-verse repair.

This script:
1) Reads the repair log to determine which book/chapter blocks were replaced.
2) For each repaired chapter, parses the current Markdown and verifies:
   - no dummy placeholders remain
   - no verse-numbering gaps remain
   - verse set and verse text exactly match the alternate source:
     xxruyle/Bible-DouayRheims -> EntireBible-DR.json
3) Writes a markdown QC summary with a result table and sample comparisons.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
from urllib.parse import quote

import requests
import yaml


DUMMY_PHRASE_RE = re.compile(r"dummy verses inserted by amos", re.IGNORECASE)
CHAPTER_HEADER_RE = re.compile(r"^## Chapter\s+(\d+)\s*$")
VERSE_LINE_RE = re.compile(r"^\*\*(\d+)\*\*\s+(.*)$")

REPAIR_LOG_PATH = Path(
    "data_engineering/data_sources/bible_douay_rheims/bible_api_dummy_verse_repair_log.md"
)

DATA_FINAL_DIR = Path("data_final/bible_douay_rheims")
ENTIRE_BIBLE_URL = (
    "https://raw.githubusercontent.com/xxruyle/Bible-DouayRheims/main/Douay-Rheims/EntireBible-DR.json"
)


def _normalize_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _load_yaml_frontmatter(md_text: str) -> Dict[str, Any]:
    if not md_text.startswith("---"):
        return {}
    end_marker = md_text.find("\n---\n")
    if end_marker == -1:
        return {}
    fm_text = md_text[len("---\n") : end_marker].strip("\n")
    parsed = yaml.safe_load(fm_text) or {}
    return parsed if isinstance(parsed, dict) else {}


def _parse_chapter_verses(markdown_text: str, chapter_num: int) -> Dict[int, str]:
    # Extract verses by scanning chapter blocks in the current Markdown.
    lines = markdown_text.splitlines()
    in_chapter = False
    verses: Dict[int, str] = {}
    for line in lines:
        m = CHAPTER_HEADER_RE.match(line)
        if m:
            in_chapter = int(m.group(1)) == chapter_num
            continue
        if not in_chapter:
            continue
        vm = VERSE_LINE_RE.match(line)
        if not vm:
            continue
        vnum = int(vm.group(1))
        text = vm.group(2).strip()
        verses[vnum] = text
    return verses


def _has_gap(verse_nums: Sequence[int]) -> Tuple[int, int]:
    uniq = sorted(set(verse_nums))
    gap_events = 0
    missing_total = 0
    for a, b in zip(uniq, uniq[1:]):
        if b - a > 1:
            gap_events += 1
            missing_total += b - a - 1
    return gap_events, missing_total


def _fetch_entire_bible(timeout_s: int = 30) -> Dict[str, Any]:
    resp = requests.get(ENTIRE_BIBLE_URL, timeout=timeout_s)
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, dict):
        raise ValueError("EntireBible-DR.json did not parse into a mapping.")
    return data


def _resolve_entire_bible_key(
    book_title: str,
    entire_bible: Dict[str, Any],
    alternate_keys_norm: Dict[str, str],
) -> str:
    manual: Dict[str, str] = {
        "1samuel": "1 Kings",
        "2samuel": "2 Kings",
        "1chronicles": "1 Paralipomenon",
        "2chronicles": "2 Paralipomenon",
        "isaiah": "Isaias",
        "ezekiel": "Ezechiel",
        "micah": "Micheas",
        "jonah": "Jona",
        "revelation": "Apocalypse",
        "tobit": "Tobias",
        "sirach": "Ecclesiasticus",
        "songofsolomon": "Canticles",
        "1maccabees": "1 Machabees",
        "2maccabees": "2 Machabees",
    }

    norm = _normalize_name(book_title)
    if norm in manual and manual[norm] in entire_bible:
        return manual[norm]

    if norm in alternate_keys_norm:
        return alternate_keys_norm[norm]

    # Last resort: fuzzy by close normalized match
    keys = list(alternate_keys_norm.keys())
    best: Optional[str] = None
    best_score = 0.0
    for k in keys:
        # Simple score: intersection proportion in normalized strings.
        inter = set(k) & set(norm)
        score = len(inter) / max(1, len(set(norm)))
        if score > best_score:
            best_score = score
            best = k
    if best and best in alternate_keys_norm:
        return alternate_keys_norm[best]

    raise KeyError(f"Could not resolve EntireBible key for book_title={book_title!r}")


@dataclass(frozen=True)
class RepairedChapterRef:
    file_name: str
    book_id: str
    book_title: str
    chapter_num: int
    reasons: str


def _parse_repair_log_repaired_chapters(log_text: str) -> List[RepairedChapterRef]:
    # Matches lines like:
    # - `Bible_Book_10_2_Samuel.md`: `2SA` / *2 Samuel* / Chapter 5 — ...
    entry_re = re.compile(
        r"^- `(?P<file>Bible_Book_[^`]+\.md)`: `(?P<book_id>[^`]+)` / \*(?P<title>[^*]+)\* / Chapter (?P<ch>\d+)\s*— (?P<reasons>.+)$"
    )

    # Also allow entries without explicit "— ..." (less likely but safe).
    entry_re2 = re.compile(
        r"^- `(?P<file>Bible_Book_[^`]+\.md)`: `(?P<book_id>[^`]+)` / \*(?P<title>[^*]+)\* / Chapter (?P<ch>\d+)\s*$"
    )

    out: List[RepairedChapterRef] = []
    for line in log_text.splitlines():
        m = entry_re.match(line.strip())
        if m:
            out.append(
                RepairedChapterRef(
                    file_name=m.group("file"),
                    book_id=m.group("book_id"),
                    book_title=m.group("title"),
                    chapter_num=int(m.group("ch")),
                    reasons=m.group("reasons").strip(),
                )
            )
            continue
        m2 = entry_re2.match(line.strip())
        if m2:
            out.append(
                RepairedChapterRef(
                    file_name=m2.group("file"),
                    book_id=m2.group("book_id"),
                    book_title=m2.group("title"),
                    chapter_num=int(m2.group("ch")),
                    reasons="(no reasons recorded)",
                )
            )
    # De-dupe by (file, chapter)
    dedup: Dict[Tuple[str, int], RepairedChapterRef] = {}
    for ref in out:
        dedup[(ref.file_name, ref.chapter_num)] = ref
    return [dedup[k] for k in sorted(dedup.keys(), key=lambda x: (x[0], x[1]))]


def _format_bool(b: bool) -> str:
    return "✅" if b else "❌"


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    log_path = repo_root / REPAIR_LOG_PATH
    if not log_path.exists():
        print(f"Repair log not found: {log_path}", file=sys.stderr)
        return 1

    md_text = log_path.read_text(encoding="utf-8", errors="replace")
    repaired_refs = _parse_repair_log_repaired_chapters(md_text)

    if not repaired_refs:
        print("No repaired chapter entries found in repair log.", file=sys.stderr)
        return 1

    # Fetch alternate entire bible once.
    entire_bible = _fetch_entire_bible(timeout_s=30)
    alternate_keys_norm = {_normalize_name(k): k for k in entire_bible.keys() if isinstance(k, str)}

    # QC per chapter
    rows: List[Dict[str, Any]] = []
    mismatched_samples: List[str] = []

    for ref in repaired_refs:
        md_path = repo_root / DATA_FINAL_DIR / ref.file_name
        if not md_path.exists():
            rows.append(
                {
                    "file": ref.file_name,
                    "book_title": ref.book_title,
                    "chapter": ref.chapter_num,
                    "dummy_present": None,
                    "gap_events": None,
                    "verse_count": None,
                    "expected_verse_count": None,
                    "exact_match": False,
                    "mismatch_details": f"Missing file: {md_path}",
                }
            )
            continue

        current_text = md_path.read_text(encoding="utf-8", errors="replace")
        current_verses = _parse_chapter_verses(current_text, ref.chapter_num)
        dummy_present = bool(DUMMY_PHRASE_RE.search(current_text))
        gap_events, missing_total = _has_gap(current_verses.keys())

        entire_key = _resolve_entire_bible_key(
            book_title=ref.book_title,
            entire_bible=entire_bible,
            alternate_keys_norm=alternate_keys_norm,
        )

        expected_chapter = entire_bible.get(entire_key, {}).get(str(ref.chapter_num), None)
        if not isinstance(expected_chapter, dict):
            rows.append(
                {
                    "file": ref.file_name,
                    "book_title": ref.book_title,
                    "chapter": ref.chapter_num,
                    "dummy_present": dummy_present,
                    "gap_events": gap_events,
                    "verse_count": len(current_verses),
                    "expected_verse_count": None,
                    "exact_match": False,
                    "mismatch_details": f"Expected chapter missing: entire_key={entire_key!r}",
                }
            )
            continue

        expected_verses: Dict[int, str] = {int(k): str(v).strip() for k, v in expected_chapter.items()}

        # Compare sets and text.
        current_keys = set(current_verses.keys())
        expected_keys = set(expected_verses.keys())

        missing_in_current = sorted(expected_keys - current_keys)
        extra_in_current = sorted(current_keys - expected_keys)

        mismatched = 0
        mismatched_verse_nums: List[int] = []
        for vnum in sorted(current_keys & expected_keys):
            if current_verses[vnum].strip() != expected_verses[vnum].strip():
                mismatched += 1
                mismatched_verse_nums.append(vnum)

        exact_match = (
            dummy_present is False
            and gap_events == 0
            and not missing_in_current
            and not extra_in_current
            and mismatched == 0
        )

        mismatch_details = ""
        if not exact_match:
            parts: List[str] = []
            if dummy_present:
                parts.append("dummy_present")
            if gap_events:
                parts.append(f"gaps={gap_events} missing_total={missing_total}")
            if missing_in_current:
                parts.append(f"missing_in_current={missing_in_current[:10]}")
            if extra_in_current:
                parts.append(f"extra_in_current={extra_in_current[:10]}")
            if mismatched:
                parts.append(f"mismatched_verses={mismatched} e.g. {mismatched_verse_nums[:5]}")
            mismatch_details = "; ".join(parts) if parts else "unknown mismatch"

            if len(mismatched_samples) < 10:
                mismatched_samples.append(
                    f"{ref.file_name} ch {ref.chapter_num} mismatch: {mismatch_details}"
                )

        rows.append(
            {
                "file": ref.file_name,
                "book_title": ref.book_title,
                "book_id": ref.book_id,
                "chapter": ref.chapter_num,
                "dummy_present": dummy_present,
                "gap_events": gap_events,
                "verse_count": len(current_verses),
                "expected_verse_count": len(expected_verses),
                "exact_match": exact_match,
                "mismatch_details": mismatch_details,
            }
        )

    total = len(rows)
    exact = sum(1 for r in rows if r["exact_match"])
    non_exact = total - exact

    # Sample comparisons (pick deterministic verses we know were dummy-prone historically)
    samples_to_show: List[Tuple[str, int, int]] = [
        ("Bible_Book_01_Genesis.md", 17, 26),
        ("Bible_Book_01_Genesis.md", 20, 15),  # was previously dummy-adjacent in earlier snapshot
        ("Bible_Book_22_Job.md", 32, 19),  # known dummy verse previously
        ("Bible_Book_10_2_Samuel.md", 5, 11),  # known dummy verse previously (2 Sam 5:11)
        ("Bible_Book_23_Psalm.md", 11, 6),  # known dummy verse previously (from earlier scan)
    ]

    sample_blocks: List[str] = []
    for file_name, chapter, verse in samples_to_show:
        md_path = repo_root / DATA_FINAL_DIR / file_name
        if not md_path.exists():
            continue
        current_text = md_path.read_text(encoding="utf-8", errors="replace")
        current_verses = _parse_chapter_verses(current_text, chapter)

        # Resolve expected via book title from YAML frontmatter.
        front = _load_yaml_frontmatter(current_text)
        book_title = str(front.get("title", "")).strip()
        if not book_title:
            continue
        entire_key = _resolve_entire_bible_key(
            book_title=book_title,
            entire_bible=entire_bible,
            alternate_keys_norm=alternate_keys_norm,
        )
        expected_chapter = entire_bible[entire_key].get(str(chapter), {})
        expected_verse_text = str(expected_chapter.get(str(verse), "")).strip()
        current_verse_text = current_verses.get(verse, "").strip()

        match = current_verse_text == expected_verse_text and current_verse_text != ""
        sample_blocks.append(
            "\n".join(
                [
                    f"### Sample: `{file_name}` Chapter {chapter} Verse {verse}",
                    f"- Current matches expected: {_format_bool(match)}",
                    "",
                    "Current:",
                    f"> {current_verse_text[:240]}{'...' if len(current_verse_text)>240 else ''}",
                    "",
                    "Expected (EntireBible-DR):",
                    f"> {expected_verse_text[:240]}{'...' if len(expected_verse_text)>240 else ''}",
                ]
            )
        )

    # Write markdown QC report.
    out_lines: List[str] = []
    out_lines.append("# Douay-Rheims Dummy Verse Repair - QC Results")
    out_lines.append("")
    out_lines.append(f"- Repaired chapters checked: {total}")
    out_lines.append(f"- Exact matches to EntireBible-DR: {exact}/{total}")
    out_lines.append("")

    out_lines.append("## Summary Table")
    out_lines.append("")
    out_lines.append(
        "| File | Book | Chapter | Dummy present? | Gap events | Verse count (current) | Verse count (expected) | Exact match |"
    )
    out_lines.append(
        "|---|---|---:|---|---:|---:|---:|---|"
    )

    # Stable sort: by filename then chapter
    for r in sorted(rows, key=lambda x: (x["file"], x["chapter"])):
        out_lines.append(
            f"| `{r['file']}` | {r['book_title']} | {r['chapter']} | "
            f"{_format_bool(bool(r['dummy_present']))} | {r['gap_events'] if r['gap_events'] is not None else 'n/a'} | "
            f"{r['verse_count'] if r['verse_count'] is not None else 'n/a'} | {r['expected_verse_count'] if r['expected_verse_count'] is not None else 'n/a'} | "
            f"{_format_bool(bool(r['exact_match']))} |"
        )

    if mismatched_samples:
        out_lines.append("")
        out_lines.append("## Mismatch Samples (if any)")
        out_lines.append("")
        out_lines.extend([f"- {s}" for s in mismatched_samples])

    out_lines.append("")
    out_lines.append("## Sample Verse Comparisons")
    out_lines.append("")
    out_lines.extend(sample_blocks if sample_blocks else ["(No sample blocks generated.)"])

    out_text = "\n".join(out_lines) + "\n"

    # Also update the shared repair log by embedding the QC results table.
    updated_log = md_text
    qc_marker = "<!-- QC_SECTION_START -->"
    if qc_marker in updated_log:
        insert_at = updated_log.index(qc_marker) + len(qc_marker)
        qc_plan_idx = updated_log.find("## QC Plan", insert_at)
        if qc_plan_idx == -1:
            # Fallback: just insert.
            updated_log = updated_log[:insert_at] + "\n\n" + out_text + updated_log[insert_at:]
        else:
            # Replace the previous QC results content to keep idempotent.
            updated_log = updated_log[:insert_at] + "\n\n" + out_text + "\n\n" + updated_log[qc_plan_idx:]

        log_path.write_text(updated_log, encoding="utf-8")

    print(f"QC complete: {exact}/{total} exact matches. Report embedded in: {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

