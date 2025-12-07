# Data Sources

This directory contains all data extraction scripts for The Depositum pipeline.

## Available Sources

### 1. Douay-Rheims Bible (`douay_rheims/`)
**Status**: ✅ Ready - No prerequisites

**Overview**: Downloads the complete Douay-Rheims Bible (1899 American Edition) from bible-api.com.

**Key Features**:
- Automatic detection of all 73 books
- Clean Markdown output
- Rate-limited API calls
- No manual downloads required

**See**: [douay_rheims/README.md](douay_rheims/README.md) for details

### 2. Haydock Commentary (`haydock/`)
**Status**: ⚠️ Requires EPUB download

**Overview**: Extracts commentary from EPUB format.

**Prerequisites**:
- Download EPUB from Isidore E-Book Library or JohnBlood GitLab
- Place in `haydock/raw/` directory

**See**: [haydock/README.md](haydock/README.md) for details

### 3. Roman Catechism (`catechism/`)
**Status**: ⚠️ Requires RTF download

**Overview**: Extracts catechism from RTF format.

**Prerequisites**:
- Download RTF from SaintsBooks.net
- Ensure it's the McHugh & Callan translation (1923)
- Place in `catechism/raw/` directory

**See**: [catechism/README.md](catechism/README.md) for details

## Running Individual Extractors

Each source has its own extraction script:

```bash
# Bible (no prerequisites)
cd douay_rheims
python extract_bible.py

# Commentary (requires EPUB)
cd haydock
python extract_commentary.py

# Catechism (requires RTF)
cd catechism
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

All extractors save to:
- `data_engineering/processed_data/{source_name}/`

Final output (after pipeline completion) is in:
- `data_final/{source_name}/`

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

