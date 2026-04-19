# Douay-Rheims raw HTML (Project Gutenberg #8300)

## Files

| File | Role |
| --- | --- |
| `pg8300.html` | Unmodified UTF-8 HTML from [Project Gutenberg #8300](https://www.gutenberg.org/ebooks/8300). Keep this as an archival baseline. |
| `pg8300_adjusted.html` | Same structure as `pg8300.html`, plus **manual corrections** documented below. The extraction pipeline (`pipeline_config.yaml` → `paths.raw_data.douay_rheims`) points here so parsers emit faithful scripture text where PG is defective. |

If you add new fixes, edit **`pg8300_adjusted.html`** only; retain **`pg8300.html`** unchanged unless you intentionally refresh from Gutenberg.

---

## Change log

### 2026-04-19 — 2 Paralipomenon (2 Chronicles), Chapter 32

**Why:** In the stock `#8300` HTML, **Chapter 32 repeats Chapter 31’s verse text** (mis-labeled `32:1`–`32:21`), and the chapter argument mistakenly reused Chapter 31’s summary (“Idolatry is abolished…”). That is a **source transcription error**, not something the extractor can infer.

**What we did:**

1. Left **Chapter 31** unchanged (heading, argument, `31:1`–`31:21`).
2. Under **`2 Paralipomenon Chapter 32`**, removed the erroneous “Idolatry is abolished…” argument line (duplicate of Chapter 31).
3. Inserted the correct chapter argument and **33 verses** (`32:1`–`32:33`) for Douay-Rheims **2 Paralipomenon Chapter 32**, transcribed from [DRBO chapter 14032](https://www.drbo.org/chapter/14032.htm) (verse 30 uses **“all”** where DRBO’s page shows a typo **“ail”**, consistent with the printed sense).

**Verification:** Re-run extraction and open `data_final/bible_douay_rheims/Bible_Book_14_2_Chronicles.md`: Chapter 32 should begin with Sennacherib’s invasion (not the Chapter 31 tithe passage), through verse 33 and Manasses succeeding Ezechias.

---

## Policy

- Prefer **small, surgical edits** with a dated entry in this file.
- Cite an external witness (e.g. DRBO, printed Douay-Rheims) when repairing PG text.
- Never “fix” spelling or punctuation for style alone; stay aligned with the edition you intend to ship.
