# Bible sourcing: offline Gutenberg (#8300) instead of Bible API

## Summary

This branch **changes where the Douay-Rheims text comes from**, while keeping the **same translation lineage** (Douay-Rheims with Challoner revision style as represented in sources). Extraction is now anchored on a **single, offline, inspectable artifact**—Project Gutenberg **[#8300 HTML](https://www.gutenberg.org/ebooks/8300)**—with a **deterministic BeautifulSoup pipeline**, **full 73-book Catholic canon**, and **validation you can rerun and diff**. Follow-on work improves parser fidelity (Challoner marginal notes), adds DRBO-backed QC, and documents the audit story.

---

## Why leave the Bible API path

- **Incomplete or uneven coverage** for some canonical books versus what we need for a complete Catholic Bible output.
- **Quality and consistency**: responses were not always reliable or fully populated; repairing gaps ad hoc was brittle.
- **Auditability**: an HTTP API plus opaque behavior is harder to reproduce, bisect, and defend than **one pinned HTML file + open code**.

The goal was not to change theology or “switch translations” in the doctrinal sense, but to **switch the ingestion channel** so the corpus is **complete, reproducible, and attributable** to a public-domain file we control end-to-end.

---

## What we switched to

| Aspect | Direction |
| --- | --- |
| **Source text** | PG #8300 Douay-Rheims (Challoner revision per Gutenberg edition), **offline HTML** under `data_engineering/data_sources/bible_douay_rheims/raw/`. |
| **Canon** | **73 books** aligned with the project’s Catholic canon ordering (including PG’s Job/Maccabees ordering quirks via explicit mapping). |
| **Processing** | Trim book boundaries from HTML → parse chapters/verses → sanitize (`extract_bible.py`) → Markdown under `data_final/bible_douay_rheims/`. |
| **Integrity** | Structural checks vs the **same HTML** source; extraction audit log; optional **DRBO** spot-check / extended mismatch hunt for external sanity checks. |

---

## Parser and QC enhancements (later commits)

- **Challoner marginal notes**: In PG HTML, glosses often appear as **separate `<p>` blocks** after a verse (sometimes after a comma-ended line). Continuation logic no longer merges those paragraphs into scripture when they match Challoner’s **keyword + `...`** lead-in pattern (global heuristic).
- **Validation**: `validate_bible_integrity` compares output to parsed source text, logs trends, runs DRBO sampling (100 verses), then an extended hunt (stop at **20** strict mismatches **or** **400** comparisons). Markdown report lists **problem rows only** in the hunt table; aggregates still report exact/near/mismatch totals.
- **Pipeline**: `run_pipeline.py --source bible` wires extraction → validation; tests cover trim/split/sanitize and canon emission.

---

## Audit / artifacts (what to read)

| Artifact | Role |
| --- | --- |
| **`data_engineering/logs/bible_extraction_audit.log`** | Structured trace of skips, continuations, and recoveries during parsing. |
| **`data_engineering/logs/bible_integrity_history.jsonl`** | Rolling counters for drift alerts (e.g. skipped commentary vs previous runs). |
| **`accuracy_reports/bible_parsing_accuracy_report.{md,json}`** | Latest DRBO comparison summary + mismatch hunt detail. |

---

## Commits on this branch (`main..HEAD`)

Ten commits from planning through validation (subjects only; see `git log main..HEAD` for hashes):

1. Planning changes + Bible txt download  
2. File and script changes for new method  
3. Regeneration of books of Bible  
4. Changing Bible source  
5. Using HTML to parse Bible  
6. Further improvements  
7. Creating QC process  
8. Tweaks to account for comment  
9. Running and saving changes  
10. Further enhancements + validation  

*(Branch name: `refactor/new-bible-sourcing-strategy`.)*

---

## How to verify locally

```bash
uv run pytest data_engineering/tests/test_gutenberg_bible_extract.py -v
uv run python data_engineering/scripts/run_pipeline.py --source bible
```

Confirm **`data_final/bible_douay_rheims/`** (73 `Bible_Book_*.md` files) and review **`accuracy_reports/bible_parsing_accuracy_report.md`**.

---

## Risks / follow-ups

- Challoner notes **without** the leading `...` pattern may still need manual or heuristic handling if they appear after comma-ended verses.
- **DRBO** is an external reference; “mismatches” can reflect DRBO HTML quirks or spelling variants, not only parser bugs.
- Trend warnings when **`joined_continuations`** drops sharply vs historical runs are **expected** after fixing false merges.
