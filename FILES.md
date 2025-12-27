# Complete File Listing

This document provides a complete listing of all files in The Depositum repository.

## Root Level Files

| File | Description |
|------|-------------|
| `README.md` | Main project documentation with overview, quick start, and usage instructions |
| `FILES.md` | This file - complete file listing and organization guide |
| `LICENSE` | MIT License |
| `pyproject.toml` | Python project configuration, dependencies, and build system |
| `.gitignore` | Git ignore rules for Python, data files, logs, and IDE files |
| `uv.lock` | Lock file for uv package manager (generated, not typically version controlled) |

## Scripts

| File | Description |
|------|-------------|
| `scripts/security_check.sh` | Security scanning script for local development (Bandit + pip-audit) |

## Configuration & Development Files

### Cursor IDE Rules (`.cursor/rules/`)
| File | Description | Applies To |
|------|-------------|------------|
| `error-handling.mdc` | Critical error handling rules - always let errors float to the top | All `*.py` files |
| `data-engineering.mdc` | Complete data engineering standards and best practices | `data_engineering/**/*.py` |

### GitHub Configuration (`.github/`)
| File | Description |
|------|-------------|
| `CODEOWNERS` | Code review assignments for different parts of the repository |
| `workflows/security-audit.yml` | Automated security scanning workflow (Bandit + pip-audit) |

## Data Engineering Files

### Main Documentation
| File | Description |
|------|-------------|
| `data_engineering/README.md` | Complete technical documentation for the data engineering pipeline |

### Configuration
| File | Description |
|------|-------------|
| `data_engineering/config/pipeline_config.yaml` | Central configuration file for API endpoints, file paths, output formatting, and validation rules |

### Pipeline Orchestration
| File | Description |
|------|-------------|
| `data_engineering/scripts/run_pipeline.py` | Main pipeline orchestrator with command-line interface supporting individual sources, validation, and output copying |

### Data Sources

#### Douay-Rheims Bible
| File | Description |
|------|-------------|
| `data_engineering/data_sources/bible_douay_rheims/extract_bible.py` | Extraction script that downloads from bible-api.com and converts to Markdown |
| `data_engineering/data_sources/bible_douay_rheims/README.md` | Extraction guide with API details and configuration |

#### Haydock Commentary
| File | Description |
|------|-------------|
| `data_engineering/data_sources/bible_commentary_haydock/extract_commentary.py` | Extraction script that processes EPUB files and extracts commentary to Markdown |
| `data_engineering/data_sources/bible_commentary_haydock/README.md` | Extraction guide with EPUB structure notes and customization instructions |

#### Roman Catechism
| File | Description |
|------|-------------|
| `data_engineering/data_sources/catholic_catechism_trent/extract_catechism.py` | Extraction script that converts PDF files to Markdown with comprehensive header detection and italic formatting |
| `data_engineering/data_sources/catholic_catechism_trent/README.md` | Extraction guide with PDF parsing details, header detection methods, and content preservation rules |
| `data_engineering/data_sources/catholic_catechism_trent/EXTRACTION_ANALYSIS.md` | Analysis document tracking the iterative improvement process for header detection accuracy |
| `data_engineering/data_sources/catholic_catechism_trent/cleaned_table_of_contents.csv` | Reference table of contents used for validating header hierarchy accuracy |
| `data_engineering/data_sources/catholic_catechism_trent/The Roman Catechism.pdf` | Source PDF file (not version controlled, must be downloaded separately) |

#### Data Sources Overview
| File | Description |
|------|-------------|
| `data_engineering/data_sources/README.md` | Overview of all data sources with usage instructions |

## Output Documentation

| File | Description |
|------|-------------|
| `data_final/00_Project_Prompt_and_Sources.md` | Project constitution and source documentation defining the three pillars (Scripture, Tradition, Magisterium) and operational guidelines for AI tools |
| `data_final/bible_commentary_haydock/.gitkeep` | Placeholder to ensure directory is tracked in git |

## Generated Directories (Not Version Controlled)

These directories are created by the pipeline and contain generated files:

- `data_engineering/processed_data/` - Intermediate processed files
  - `bible_douay_rheims/` - Intermediate Bible files
  - `bible_commentary_haydock/` - Intermediate commentary files
  - `catholic_catechism_trent/` - Intermediate catechism file

- `data_final/` - Final output directories
  - `bible_douay_rheims/` - 66 Markdown files (Bible_Book_01_Genesis.md through Bible_Book_73_Revelation.md - currently missing 7 deuterocanonical books)
  - `bible_commentary_haydock/` - Commentary Markdown files
  - `catholic_catechism_trent/` - 000_Catholic_Catechism_Trent_McHugh_Callan.md
  - `00_Project_Prompt_and_Sources.md` - Project constitution and source documentation for AI tools

- `data_engineering/logs/` - Execution logs (bible_extraction.log, catechism_extraction.log)

- `.venv/` - Virtual environment (created by `uv venv`)

## File Count Summary

### Source Files (Version Controlled)
- **Python scripts**: 4 files (3 extraction scripts + 1 pipeline orchestrator)
- **Configuration files**: 2 files (pipeline_config.yaml, pyproject.toml)
- **Documentation files**: 12 files (9 README.md files + 1 FILES.md + 1 EXTRACTION_ANALYSIS.md + 1 00_Project_Prompt_and_Sources.md)
- **Data files**: 1 CSV file (cleaned_table_of_contents.csv)
- **Scripts**: 1 shell script (security_check.sh)
- **Cursor rules**: 2 .mdc files (if .cursor/rules/ directory exists)
- **GitHub workflows**: 1 workflow file (if .github/workflows/ directory exists)
- **Other**: LICENSE, .gitignore

### Generated Files (Not Version Controlled)
- **Bible output**: 66 Markdown files (currently missing 7 deuterocanonical books: Tobit, Judith, Wisdom, Sirach, Baruch, 1 Maccabees, 2 Maccabees - see bible_douay_rheims/README.md for details)
- **Commentary output**: 73 Markdown files (one per book of the Catholic canon)
- **Catechism output**: 1 Markdown file (after running pipeline)

## File Naming Conventions

- **Extraction scripts**: `extract_{source}.py`
- **Bible files**: `Bible_Book_{number}_{book_name}.md` (e.g., `Bible_Book_01_Genesis.md`, `Bible_Book_47_Matthew.md`, `Bible_Book_73_Revelation.md`)
- **Commentary files**: `Bible_Book_{number}_{book_name}_Commentary.md` (e.g., `Bible_Book_01_Genesis_Commentary.md`, `Bible_Book_50_John_Commentary.md`, `Bible_Book_73_Revelation_Commentary.md`)
- **Catechism file**: `000_Catholic_Catechism_Trent_McHugh_Callan.md` (the "000" prefix ensures it appears second in sorted lists)
- **Documentation**: `README.md` in each directory
- **Configuration**: `pipeline_config.yaml`, `pyproject.toml`
- **Rules**: `{category}.mdc` in `.cursor/rules/`

## File Organization Principles

1. **Separation of Concerns**: Technical files in `data_engineering/`, final output in `data_final/`
2. **Documentation at Every Level**: README.md files provide context at each directory level
3. **Configuration Centralized**: All configuration in `data_engineering/config/`
4. **Standards Enforced**: Cursor rules ensure consistent code quality
5. **Security Automated**: GitHub workflows scan on every change
6. **Version Control**: Only source code and documentation are versioned, not generated data

