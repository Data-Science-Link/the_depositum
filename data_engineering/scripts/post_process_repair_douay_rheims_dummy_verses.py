#!/usr/bin/env python3
"""
Post-process repair for Douay-Rheims Bible extraction.

Problem:
Some chapters returned by bible-api.com (Douay-Rheims 1899 American Edition / "dra")
contain placeholder text like "dummy verses inserted by amos" and/or exhibit
verse-numbering gaps. This leads to missing/incorrect verse content in the
generated Markdown.

Solution:
Detect damaged chapters in the extracted Markdown and replace the entire chapter
with a full verse listing taken from the alternate source:
xxruyle/Bible-DouayRheims (consolidated `EntireBible-DR.json`).
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import time
from dataclasses import dataclass
from difflib import get_close_matches
from pathlib import Path
from urllib.parse import quote
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import requests
import yaml


DUMMY_PHRASE_RE = re.compile(r"dummy verses inserted by amos", re.IGNORECASE)
CHAPTER_HEADER_RE = re.compile(r"^## Chapter\s+(\d+)\s*$")
VERSE_LINE_RE = re.compile(r"^\*\*(\d+)\*\*\s+(.*)$")

GITHUB_RAW_BASE = "https://raw.githubusercontent.com/xxruyle/Bible-DouayRheims/main/Douay-Rheims"
ENTIRE_BIBLE_URL = (
    "https://raw.githubusercontent.com/xxruyle/Bible-DouayRheims/main/Douay-Rheims/EntireBible-DR.json"
)


def _setup_logger(log_file: Path) -> logging.Logger:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    log_file.parent.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger


def _normalize_name(name: str) -> str:
    # Normalize for matching filenames/keys across sources.
    # Keep digits; remove everything else.
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _load_config(config_path: Path) -> Dict[str, Any]:
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if not isinstance(cfg, dict):
        raise ValueError(f"Config at {config_path} did not parse into a mapping.")
    return cfg


def _parse_frontmatter(md_text: str) -> Tuple[Dict[str, Any], str]:
    if not md_text.startswith("---"):
        raise ValueError("Markdown file missing YAML frontmatter start marker.")

    end_marker = md_text.find("\n---\n")
    if end_marker == -1:
        raise ValueError("Markdown file missing YAML frontmatter end marker.")

    fm_text = md_text[len("---\n") : end_marker].strip("\n")
    remainder = md_text[end_marker + len("\n---\n") :]

    frontmatter = yaml.safe_load(fm_text) or {}
    if not isinstance(frontmatter, dict):
        raise ValueError("YAML frontmatter did not parse into a mapping.")
    return frontmatter, remainder


def _iter_chapter_spans(lines: Sequence[str]) -> Iterable[Tuple[int, int, int]]:
    """
    Yield (start_idx, end_idx_exclusive, chapter_num).

    end_idx_exclusive is the index of the next `## Chapter N` header line, or len(lines).
    """
    starts: List[int] = []
    chapter_nums: Dict[int, int] = {}

    for idx, line in enumerate(lines):
        m = CHAPTER_HEADER_RE.match(line)
        if not m:
            continue
        ch = int(m.group(1))
        starts.append(idx)
        chapter_nums[idx] = ch

    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(lines)
        yield start, end, chapter_nums[start]


def _extract_verses_from_lines(lines: Sequence[str]) -> List[Tuple[int, str]]:
    verses: List[Tuple[int, str]] = []
    for line in lines:
        m = VERSE_LINE_RE.match(line)
        if not m:
            continue
        verse_num = int(m.group(1))
        text = m.group(2).rstrip("\n")
        verses.append((verse_num, text))
    return verses


def _chapter_needs_repair(verses: Sequence[Tuple[int, str]]) -> Tuple[bool, List[str]]:
    if not verses:
        return True, ["No verses parsed"]

    reasons: List[str] = []
    verse_nums = sorted(set(v for v, _ in verses))

    if any(DUMMY_PHRASE_RE.search(text) for _, text in verses):
        reasons.append("Contains dummy placeholder text")

    # Detect internal verse numbering gaps.
    gaps = 0
    for a, b in zip(verse_nums, verse_nums[1:]):
        if b - a > 1:
            gaps += 1
    if gaps > 0:
        reasons.append(f"Verse numbering gaps detected ({gaps} gap event(s))")

    return bool(reasons), reasons


@dataclass(frozen=True)
class RepairChapter:
    file_path: Path
    book_id: str
    book_title: str
    chapter_num: int
    reasons: List[str]


def _generate_candidate_alt_filenames(book_title: str) -> List[str]:
    """
    Generate candidate JSON filenames in the alternate source.

    We avoid relying on GitHub's directory listing (which may be blocked in some environments)
    and instead try common naming variants.
    """
    title = book_title.strip()
    norm = _normalize_name(title)

    # Manual overrides for known naming divergences.
    # (These reflect the alternate repository's file naming conventions.)
    manual: Dict[str, str] = {
        "isaiah": "Isaias",
        # Deuterocanonical / Latin naming used by xxruyle repo.
        "sirach": "Ecclesiasticus",
        "tobit": "Tobias",
        "1maccabees": "1 Machabees",
        "2maccabees": "2 Machabees",
        # Latin name for Canticle of Canticles.
        "songofsolomon": "Canticle of Canticles",
    }

    candidates: List[str] = []
    if norm in manual:
        candidates.append(f"{manual[norm]}.json")

    # Direct match.
    candidates.append(f"{title}.json")

    # Common spacing/underscore variants.
    candidates.append(f"{title.replace(' ', '_')}.json")
    candidates.append(f"{title.replace(' ', '')}.json")

    # Also try title lower/upper variants.
    candidates.append(f"{title.lower()}.json")
    candidates.append(f"{title.title()}.json")

    # De-dupe while preserving order.
    seen: set[str] = set()
    out: List[str] = []
    for c in candidates:
        if c not in seen:
            out.append(c)
            seen.add(c)
    return out


def _fetch_book_json_from_raw(
    book_title: str, logger: logging.Logger, timeout_s: int = 30
) -> Dict[str, Any]:
    """
    Fetch the alternate-source book JSON by trying candidate filenames on raw.githubusercontent.com.
    """
    candidates = _generate_candidate_alt_filenames(book_title)
    last_error: Optional[str] = None

    for filename in candidates:
        url = f"{GITHUB_RAW_BASE}/{quote(filename)}"
        try:
            resp = requests.get(url, timeout=timeout_s)
            if resp.status_code == 404:
                continue
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, dict):
                raise ValueError(f"Alternate book JSON for {book_title!r} was not a mapping.")
            logger.info(f"Fetched alternate JSON for {book_title!r} from {filename!r}")
            return data
        except requests.exceptions.RequestException as e:
            last_error = f"{type(e).__name__}: {e}"
            logger.warning(f"Alternate fetch attempt failed for {book_title!r} ({filename!r}): {e}")
            continue

    raise RuntimeError(
        f"Could not resolve alternate JSON for book_title={book_title!r}. "
        f"Candidates tried: {candidates}. Last error: {last_error}"
    )


def _fetch_book_json(download_url: str, logger: logging.Logger, timeout_s: int = 30) -> Dict[str, Any]:
    # Backwards-compat shim: accept either a raw URL or other URL.
    resp = requests.get(download_url, timeout=timeout_s)
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, dict):
        raise ValueError("Alternate book JSON did not parse into a mapping.")
    return data


def _replace_chapter_block(
    lines: List[str],
    start_idx: int,
    end_idx: int,
    chapter_num: int,
    alt_verses: Sequence[Tuple[int, str]],
) -> List[str]:
    verse_lines: List[str] = []
    for verse_num, text in alt_verses:
        text_clean = text.strip()
        verse_lines.append(f"**{verse_num}** {text_clean}  ")

    new_block = [f"## Chapter {chapter_num}", ""]
    new_block.extend(verse_lines)
    new_block.extend(["", "---", ""])

    return lines[:start_idx] + new_block + lines[end_idx:]


def _append_repair_run_to_report(
    report_path: Path,
    repaired: Sequence[RepairChapter],
    failed: Sequence[RepairChapter],
    notes: str,
) -> None:
    marker = "<!-- QC_SECTION_START -->"

    if not report_path.exists():
        raise FileNotFoundError(f"Report file not found: {report_path}")

    content = report_path.read_text(encoding="utf-8", errors="replace")
    if marker not in content:
        # Fallback: append.
        content += "\n\n" + notes + "\n"
        report_path.write_text(content, encoding="utf-8")
        return

    run_notes = "\n".join(notes.splitlines())
    insert_at = content.index(marker)
    updated = content[:insert_at].rstrip() + "\n\n" + run_notes + "\n\n" + content[insert_at:]
    report_path.write_text(updated, encoding="utf-8")


def _build_repair_notes(
    repaired: Sequence[RepairChapter],
    failed: Sequence[RepairChapter],
    repaired_summary: Dict[str, Any],
) -> str:
    # Insert with markdown headings. Script will place it before QC section marker.
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    lines: List[str] = []
    lines.append(f"## Repair Run: {ts}")
    lines.append("")
    lines.append(f"- Repaired chapters: {repaired_summary['repaired_count']}")
    lines.append(f"- Failed chapters: {repaired_summary['failed_count']}")
    if repaired_summary.get("dummy_removed_estimate") is not None:
        lines.append(f"- Dummy placeholder removals (pre-repair estimate): {repaired_summary['dummy_removed_estimate']}")
    lines.append("")

    if repaired:
        lines.append("### Repaired Chapters")
        lines.append("")
        for ch in repaired:
            reason_str = "; ".join(ch.reasons)
            lines.append(
                f"- `{ch.file_path.name}`: `{ch.book_id}` / *{ch.book_title}* / Chapter {ch.chapter_num} — {reason_str}"
            )
        lines.append("")
    else:
        lines.append("### Repaired Chapters")
        lines.append("")
        lines.append("- None")
        lines.append("")

    if failed:
        lines.append("### Repair Failures")
        lines.append("")
        for ch in failed:
            reason_str = "; ".join(ch.reasons)
            lines.append(
                f"- `{ch.file_path.name}`: `{ch.book_id}` / *{ch.book_title}* / Chapter {ch.chapter_num} — {reason_str}"
            )
        lines.append("")

    lines.append("### QC Status")
    lines.append("")
    lines.append("- Pending: run a chapter-by-chapter comparison against an internet Douay-Rheims source.")
    lines.append("- When completed, update the shared QC section in this document.")
    return "\n".join(lines)


def main() -> int:
    project_root = Path(__file__).resolve().parents[2]
    config_path = project_root / "data_engineering" / "config" / "pipeline_config.yaml"

    config = _load_config(config_path)

    input_dir = Path(config["paths"]["final_output"]["douay_rheims"])

    log_dir = project_root / "data_engineering" / "logs"
    log_file = log_dir / "bible_douay_rheims_dummy_verse_repair.log"
    logger = _setup_logger(log_file)

    report_path = (
        project_root
        / "data_engineering"
        / "data_sources"
        / "bible_douay_rheims"
        / "bible_api_dummy_verse_repair_log.md"
    )

    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        return 1

    if not report_path.exists():
        logger.error(f"Report template missing: {report_path}")
        return 1

    logger.info("=" * 70)
    logger.info("Scanning extracted Markdown for damaged chapters...")
    logger.info("=" * 70)

    logger.info("Fetching consolidated alternate source (EntireBible-DR.json)...")
    entire_bible = requests.get(ENTIRE_BIBLE_URL, timeout=30)
    entire_bible.raise_for_status()
    alternate_entire_bible = entire_bible.json()
    if not isinstance(alternate_entire_bible, dict):
        logger.error("Alternate EntireBible-DR.json did not parse into a mapping.")
        return 1

    alternate_keys: List[str] = sorted(str(k) for k in alternate_entire_bible.keys())
    alternate_keys_by_norm: Dict[str, str] = {
        _normalize_name(k): k for k in alternate_keys if isinstance(k, str)
    }

    # Map our Markdown book titles to the alternate JSON book keys.
    # These reflect naming/numbering differences between Vulgate labels and the source repo.
    manual_book_key_map: Dict[str, str] = {
        # Samuel/Vulgate kings mapping
        "1samuel": "1 Kings",
        "2samuel": "2 Kings",
        # Chronicles / Paralipomenon mapping
        "1chronicles": "1 Paralipomenon",
        "2chronicles": "2 Paralipomenon",
        # Latin/Vulgate spellings
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
        # If our extractor ever outputs these already.
        "apocalypse": "Apocalypse",
        "ezechiel": "Ezechiel",
        "micheas": "Micheas",
    }

    total_chapters_scanned = 0
    total_repair_candidates = 0
    repaired: List[RepairChapter] = []
    failed: List[RepairChapter] = []

    # Cache: markdown book_title -> alternate entire-bible book key.
    alternate_book_key_cache: Dict[str, str] = {}

    for md_path in sorted(input_dir.glob("Bible_Book_*.md")):
        md_text = md_path.read_text(encoding="utf-8", errors="replace")
        try:
            frontmatter, _ = _parse_frontmatter(md_text)
        except Exception as e:
            logger.error(f"Failed to parse YAML frontmatter in {md_path.name}: {e}", exc_info=True)
            continue

        book_id = str(frontmatter.get("book_id", "")).strip()
        book_title = str(frontmatter.get("title", "")).strip()

        if not book_id or not book_title:
            logger.warning(f"Skipping file missing book_id/title: {md_path.name}")
            continue

        lines = md_text.splitlines()

        candidates: List[Tuple[int, int, int, List[str]]] = []
        # Collect candidates first so we can replace bottom-to-top (avoids index shifting).
        for start_idx, end_idx, chapter_num in _iter_chapter_spans(lines):
            total_chapters_scanned += 1

            chapter_lines = lines[start_idx:end_idx]
            verses = _extract_verses_from_lines(chapter_lines)
            needs_repair, reasons = _chapter_needs_repair(verses)
            if not needs_repair:
                continue

            total_repair_candidates += 1
            candidates.append((start_idx, end_idx, chapter_num, reasons))

        if not candidates:
            continue

        # Resolve alternate key (cached once per file/book title).
        try:
            if book_title not in alternate_book_key_cache:
                norm = _normalize_name(book_title)
                if norm in manual_book_key_map:
                    alt_key = manual_book_key_map[norm]
                elif norm in alternate_keys_by_norm:
                    alt_key = alternate_keys_by_norm[norm]
                else:
                    # Fuzzy match normalized names.
                    candidates = list(alternate_keys_by_norm.keys())
                    close = get_close_matches(norm, candidates, n=1, cutoff=0.7)
                    if not close:
                        raise KeyError(f"Could not resolve alternate book key for {book_title!r}")
                    alt_key = alternate_keys_by_norm[close[0]]

                if alt_key not in alternate_entire_bible:
                    raise KeyError(f"Resolved alternate key {alt_key!r} missing from EntireBible-DR.json")

                alternate_book_key_cache[book_title] = alt_key

            alt_key = alternate_book_key_cache[book_title]
            alt_book = alternate_entire_bible[alt_key]
        except Exception as e:
            logger.error(f"Failed to fetch alternate JSON for {book_title}: {e}", exc_info=True)
            for _, _, chapter_num, reasons in candidates:
                failed.append(
                    RepairChapter(
                        file_path=md_path,
                        book_id=book_id,
                        book_title=book_title,
                        chapter_num=chapter_num,
                        reasons=reasons,
                    )
                )
            continue

        # Replace from bottom to top to keep indices valid.
        candidates_sorted = sorted(candidates, key=lambda x: x[0], reverse=True)
        file_modified = False

        for start_idx, end_idx, chapter_num, reasons in candidates_sorted:
            try:
                alt_chapter = alt_book.get(str(chapter_num))
                if not isinstance(alt_chapter, dict):
                    raise KeyError(
                        f"Alternate source missing chapter {chapter_num} for book {book_title!r}"
                    )

                alt_verses_unsorted: List[Tuple[int, str]] = []
                for v_num_str, v_text in alt_chapter.items():
                    alt_verses_unsorted.append((int(v_num_str), str(v_text)))

                alt_verses = sorted(alt_verses_unsorted, key=lambda x: x[0])

                lines = _replace_chapter_block(
                    lines=lines,
                    start_idx=start_idx,
                    end_idx=end_idx,
                    chapter_num=chapter_num,
                    alt_verses=alt_verses,
                )
                repaired.append(
                    RepairChapter(
                        file_path=md_path,
                        book_id=book_id,
                        book_title=book_title,
                        chapter_num=chapter_num,
                        reasons=reasons,
                    )
                )
                file_modified = True
            except Exception as e:
                logger.error(
                    f"Failed to repair {md_path.name} / {book_id} / {book_title} / Chapter {chapter_num}: {e}",
                    exc_info=True,
                )
                failed.append(
                    RepairChapter(
                        file_path=md_path,
                        book_id=book_id,
                        book_title=book_title,
                        chapter_num=chapter_num,
                        reasons=reasons,
                    )
                )

        if file_modified:
            md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Post-repair QC: ensure dummy placeholder removed.
    logger.info("=" * 70)
    logger.info("Post-repair QC: searching for dummy placeholder text...")
    logger.info("=" * 70)
    remaining_dummy_files = 0
    remaining_dummy_occurrences = 0

    for md_path in sorted(input_dir.glob("Bible_Book_*.md")):
        txt = md_path.read_text(encoding="utf-8", errors="replace")
        hits = len(DUMMY_PHRASE_RE.findall(txt))
        if hits > 0:
            remaining_dummy_files += 1
            remaining_dummy_occurrences += hits

    logger.info(f"Remaining dummy placeholder occurrences: {remaining_dummy_occurrences} across {remaining_dummy_files} files")

    repaired_summary = {
        "repaired_count": len(repaired),
        "failed_count": len(failed),
        "dummy_removed_estimate": None,  # Keep report purely factual.
    }

    report_notes = _build_repair_notes(repaired=repaired, failed=failed, repaired_summary=repaired_summary)
    _append_repair_run_to_report(
        report_path=report_path,
        repaired=repaired,
        failed=failed,
        notes=report_notes,
    )

    # If anything failed or placeholders remain, return non-zero.
    if failed or remaining_dummy_occurrences > 0:
        logger.warning("Repair completed with issues.")
        return 1

    logger.info("Repair completed successfully: no dummy placeholders remain.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Intentionally no args for now; script uses config paths to avoid footguns.
    _ = parser.parse_args()
    raise SystemExit(main())

