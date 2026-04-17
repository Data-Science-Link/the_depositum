# Data Sources

This directory contains all data extraction scripts for The Depositum pipeline.

## Available Sources

### 1. Douay-Rheims Bible (`bible_douay_rheims/`)
**Status**: ✅ Complete — 73 books (Project Gutenberg #8300, Challoner revision)

**Overview**: Parses committed UTF-8 text `raw/pg8300.html` into `data_final/bible_douay_rheims/`.

**Extraction script**: `extract_bible.py` (single script, no network).

**See**: [bible_douay_rheims/README.md](bible_douay_rheims/README.md)

### 2. Haydock Commentary (`bible_commentary_haydock/`)
**Status**: ⚠️ Requires EPUB download

**Overview**: Extracts commentary from EPUB format.

**Prerequisites**:
- Download EPUB from Isidore E-Book Library or JohnBlood GitLab
- Place in `bible_commentary_haydock/` directory (the script looks for files matching the pattern `Haydock Catholic Bible Comment*.epub`)

**See**: [bible_commentary_haydock/README.md](bible_commentary_haydock/README.md) for details

### 3. Roman Catechism (`catholic_catechism_trent/`)
**Status**: ⚠️ Requires PDF download

**Overview**: Extracts catechism from PDF format with advanced header detection and italic formatting.

**Prerequisites**:
- Download PDF from SaintsBooks.net
- Ensure it's the McHugh & Callan translation (1923)
- Place `The Roman Catechism.pdf` in `catholic_catechism_trent/` directory

**Key Features**:
- Advanced header detection (PART, ARTICLE, major sections, italicized subsections)
- Italic text detection using `pdfplumber` font analysis
- Pattern-based fallback for known section titles
- Content preservation (never removes actual text, only formatting artifacts)

**See**: [catholic_catechism_trent/README.md](catholic_catechism_trent/README.md) for details

## Running Individual Extractors

Each source has its own extraction script:

```bash
# Bible (requires raw/pg8300.html)
cd bible_douay_rheims
python extract_bible.py

# Commentary (requires EPUB)
cd bible_commentary_haydock
python extract_commentary.py

# Catechism (requires PDF)
cd catholic_catechism_trent
python extract_catechism.py
```

## Running All Extractors

Use the main pipeline runner from the project root:

```bash
python data_engineering/scripts/run_pipeline.py
```

Or run specific sources:

```bash
python data_engineering/scripts/run_pipeline.py --source bible
python data_engineering/scripts/run_pipeline.py --source commentary
python data_engineering/scripts/run_pipeline.py --source catechism
```

## Output Locations

Commentary and catechism save intermediate files to:
- `data_engineering/processed_data/bible_commentary_haydock/` (Commentary)
- `data_engineering/processed_data/catholic_catechism_trent/` (Catechism)

The Bible extractor writes **directly** to `data_final/bible_douay_rheims/`. Final outputs:
- `data_final/bible_douay_rheims/` (73 Bible books)
- `data_final/bible_commentary_haydock/` (73 Commentary files, named like `Bible_Book_01_Genesis_Commentary.md`, `Bible_Book_73_Revelation_Commentary.md`)
- `data_final/catholic_catechism_trent/` (Catechism file)

## Data Flow

```
Raw Sources → Extraction Scripts → Processed / Final Output
     ↓              ↓                    ↓
  Gutenberg/EPUB/PDF   Python Scripts    Markdown in data_final/
```

**Bible:** `raw/pg8300.html` → `extract_bible.py` → `data_final/bible_douay_rheims/`

## Troubleshooting

### Common Issues

1. **Missing source files**: Ensure EPUB/PDF files are in the correct directories
2. **Bible source missing**: Ensure `bible_douay_rheims/raw/pg8300.html` exists
3. **Parsing errors**: Check EPUB/PDF structure and adjust parsing logic
4. **Encoding issues**: Scripts handle UTF-8 and latin-1 automatically
5. **Italic detection**: Catechism script uses font analysis; some italicized sections may use pattern-based fallback

### Getting Help

- Check individual README files for source-specific issues
- Review logs in `data_engineering/logs/` directory
- See main [data_engineering README](../README.md) for technical details

