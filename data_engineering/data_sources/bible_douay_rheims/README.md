# Douay-Rheims Bible extraction (Project Gutenberg #8300)

Single offline source: **HTML source** of [The Bible, Douay-Rheims, Complete](https://www.gutenberg.org/ebooks/8300) (Challoner revision). The committed file is:

`raw/pg8300.html`

## What `extract_bible.py` does

1. Trims Project Gutenberg license boilerplate (START/END markers).
2. Splits on the 73 in-file book title lines (PG order differs from Catholic filename order for Job vs Maccabees; the script maps correctly to `Bible_Book_XX_Name.md`).
3. Parses `BookName Chapter N` headings and verse lines `chapter:verse.` (with line-wrap and commentary heuristics).
4. Strips bracketed notes and editorial asterisk emphasis for audio-friendly text.
5. Writes Markdown under `data_final/bible_douay_rheims/` (see `pipeline_config.yaml`).

Output shape matches the previous pipeline: YAML frontmatter, `# Title`, `## Table of Contents`, `## Chapter n`, `**verse** text  \n`, `---` between chapters.

## Prerequisites

- `raw/pg8300.html` present (UTF-8 from Gutenberg #8300; rename e.g. `8300-0.txt` → `pg8300.html` if needed).

## Usage

From the **repository root**:

```bash
python data_engineering/data_sources/bible_douay_rheims/extract_bible.py
```

Test mode (first four books, three chapters each):

```bash
python data_engineering/data_sources/bible_douay_rheims/extract_bible.py --test
```

Override paths:

```bash
python data_engineering/data_sources/bible_douay_rheims/extract_bible.py --raw path/to/pg8300.html --output path/to/out/
```

Pipeline:

```bash
python data_engineering/scripts/run_pipeline.py --source bible
python data_engineering/scripts/run_pipeline.py --validate
```

## Configuration

- Raw path: `paths.raw_data.douay_rheims` in `data_engineering/config/pipeline_config.yaml`
- Output: `paths.final_output.douay_rheims` (default `data_final/bible_douay_rheims`)

## See also

- [`New_Sourcing_Strategy.md`](New_Sourcing_Strategy.md) — sourcing rationale (73-book canon, no #1581).
