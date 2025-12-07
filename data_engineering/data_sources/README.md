# Data Sources

This directory contains all data extraction scripts for The Depositum pipeline.

## Available Sources

### 1. Douay-Rheims Bible (`bible_douay_rheims/`)
**Status**: ⚠️ Partial - 66 books (missing 7 deuterocanonical books)

**Overview**: Downloads the Douay-Rheims Bible (1899 American Edition) from bible-api.com.

**Current Limitation**:
- The `bible-api.com` service only provides 66 books (Protestant canon)
- Missing 7 deuterocanonical books: Tobit, Judith, Wisdom, Sirach, Baruch, 1 Maccabees, 2 Maccabees

**Key Features**:
- Automatic detection of available books (currently 66)
- Clean Markdown output
- Rate-limited API calls
- No manual downloads required
- Future plan: Transition to IQ Bible API for complete 73-book canon (see README for details)

**See**: [bible_douay_rheims/README.md](bible_douay_rheims/README.md) for details and future migration plans

### 2. Haydock Commentary (`bible_commentary_haydock/`)
**Status**: ⚠️ Requires EPUB download

**Overview**: Extracts commentary from EPUB format.

**Prerequisites**:
- Download EPUB from Isidore E-Book Library or JohnBlood GitLab
- Place in `bible_commentary_haydock/raw/` directory

**See**: [bible_commentary_haydock/README.md](bible_commentary_haydock/README.md) for details

### 3. Roman Catechism (`catholic_catechism_trent/`)
**Status**: ⚠️ Requires RTF download

**Overview**: Extracts catechism from RTF format.

**Prerequisites**:
- Download RTF from SaintsBooks.net
- Ensure it's the McHugh & Callan translation (1923)
- Place in `catholic_catechism_trent/raw/` directory

**See**: [catholic_catechism_trent/README.md](catholic_catechism_trent/README.md) for details

## Running Individual Extractors

Each source has its own extraction script:

```bash
# Bible (no prerequisites)
cd bible_douay_rheims
python extract_bible.py

# Commentary (requires EPUB)
cd bible_commentary_haydock
python extract_commentary.py

# Catechism (requires RTF)
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
- `data_final/bible_douay_rheims/` (66 Bible books - see note above about missing deuterocanonical books)
- `data_final/bible_commentary_haydock/` (Commentary files)
- `data_final/catholic_catechism_trent/` (Catechism file)

## Data Flow

```
Raw Sources → Extraction Scripts → Processed Data → Final Output
     ↓              ↓                    ↓              ↓
  API/EPUB/RTF   Python Scripts    Validation      Markdown Files
```

## Troubleshooting

### Common Issues

1. **Missing source files**: Ensure EPUB/RTF files are in the correct `raw/` directories
2. **API timeouts**: Increase delay in config for Bible extraction
3. **Parsing errors**: Check EPUB/RTF structure and adjust parsing logic
4. **Encoding issues**: Scripts handle UTF-8 and latin-1 automatically

### Getting Help

- Check individual README files for source-specific issues
- Review logs in `logs/` directory
- See main [data_engineering README](../README.md) for technical details

