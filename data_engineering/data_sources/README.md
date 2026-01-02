# Data Sources

This directory contains all data extraction scripts for The Depositum pipeline.

## Available Sources

### 1. Douay-Rheims Bible (`bible_douay_rheims/`)
**Status**: ✅ Complete - 73 books (full Catholic canon via patchwork approach)

**Overview**: Extracts the complete Douay-Rheims Bible (1899 American Edition) using a patchwork approach:
- **66 books** from `bible-api.com` (Protestant canon)
- **7 Deuterocanonical books** from GitHub repository (Catholic canon completion)

**Extraction Scripts**:
- `extract_bible.py` - Extracts 66 books from bible-api.com API
- `extract_deuterocanonical.py` - Extracts 7 Deuterocanonical books from GitHub JSON files

**Key Features**:
- Complete 73-book Catholic canon
- Clean Markdown output with consistent formatting
- Rate-limited API calls
- No manual downloads required
- Automatic verse sorting (numerical order)
- Handles multiple JSON structures from GitHub

**Approach Notes**:
- This is an **MVP patchwork solution** - functional and complete, but requires two separate scripts
- Works well for development and initial deployment
- Future improvements may include migration to a unified API source for better robustness
- Both scripts output to the same directory with identical formatting

**See**: [bible_douay_rheims/README.md](bible_douay_rheims/README.md) for detailed documentation

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
# Bible - Extract 66 books from API
cd bible_douay_rheims
python extract_bible.py

# Bible - Extract 7 Deuterocanonical books from GitHub
cd bible_douay_rheims
python extract_deuterocanonical.py

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

All extractors save intermediate files to:
- `data_engineering/processed_data/bible_douay_rheims/` (Bible)
- `data_engineering/processed_data/bible_commentary_haydock/` (Commentary)
- `data_engineering/processed_data/catholic_catechism_trent/` (Catechism)

Final output (after pipeline completion with `--copy-output`) is in:
- `data_final/bible_douay_rheims/` (73 Bible books - complete Catholic canon)
- `data_final/bible_commentary_haydock/` (73 Commentary files, named like `Bible_Book_01_Genesis_Commentary.md`, `Bible_Book_73_Revelation_Commentary.md`)
- `data_final/catholic_catechism_trent/` (Catechism file)

## Data Flow

```
Raw Sources → Extraction Scripts → Processed Data → Final Output
     ↓              ↓                    ↓              ↓
  API/EPUB/PDF   Python Scripts    Validation      Markdown Files
  GitHub/JSON
```

**Bible Extraction Flow:**
- 66 books: `bible-api.com` → `extract_bible.py` → Markdown
- 7 Deuterocanonical books: `GitHub JSON` → `extract_deuterocanonical.py` → Markdown
- Both output to same directory with consistent formatting

## Troubleshooting

### Common Issues

1. **Missing source files**: Ensure EPUB/PDF files are in the correct directories
2. **API timeouts**: Increase delay in config for Bible extraction
3. **Parsing errors**: Check EPUB/PDF structure and adjust parsing logic
4. **Encoding issues**: Scripts handle UTF-8 and latin-1 automatically
5. **Italic detection**: Catechism script uses font analysis; some italicized sections may use pattern-based fallback

### Getting Help

- Check individual README files for source-specific issues
- Review logs in `data_engineering/logs/` directory
- See main [data_engineering README](../README.md) for technical details

