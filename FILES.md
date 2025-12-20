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
| `data_engineering/data_sources/catholic_catechism_trent/extract_catechism.py` | Extraction script that converts RTF files to Markdown with proper header detection |
| `data_engineering/data_sources/catholic_catechism_trent/README.md` | Extraction guide with RTF parsing details and header detection patterns |

#### Data Sources Overview
| File | Description |
|------|-------------|
| `data_engineering/data_sources/README.md` | Overview of all data sources with usage instructions |

## Output Documentation

| File | Description |
|------|-------------|
| `data_final/README.md` | Complete documentation of final output with historical context for all three sources, Deposit of Faith explanation, and Markdown format rationale |
| `data_final/bible_douay_rheims/.gitkeep` | Placeholder to ensure directory is tracked in git |
| `data_final/bible_commentary_haydock/.gitkeep` | Placeholder to ensure directory is tracked in git |
| `data_final/catholic_catechism_trent/.gitkeep` | Placeholder to ensure directory is tracked in git |

## Generated Directories (Not Version Controlled)

These directories are created by the pipeline and contain generated files:

- `data_engineering/processed_data/` - Intermediate processed files
  - `bible_douay_rheims/` - Intermediate Bible files
  - `bible_commentary_haydock/` - Intermediate commentary files
  - `catholic_catechism_trent/` - Intermediate catechism file

- `data_final/` - Final output directories
  - `bible_douay_rheims/` - 73 Markdown files (Genesis.md through Apocalypse.md)
  - `bible_commentary_haydock/` - Commentary Markdown files
  - `catholic_catechism_trent/` - Catholic_Catechism_Trent_McHugh_Callan.md

- `logs/` - Execution logs (pipeline.log)

- `.venv/` - Virtual environment (created by `uv venv`)

## File Count Summary

### Source Files (Version Controlled)
- **Python scripts**: 4 files (3 extraction scripts + 1 pipeline orchestrator)
- **Configuration files**: 2 files (pipeline_config.yaml, pyproject.toml)
- **Documentation files**: 10 files (9 README.md files + 1 FILES.md)
- **Cursor rules**: 2 .mdc files
- **GitHub workflows**: 1 workflow file
- **Other**: LICENSE, .gitignore, CODEOWNERS

### Generated Files (Not Version Controlled)
- **Bible output**: 73 Markdown files (after running pipeline)
- **Commentary output**: Variable number of Markdown files (after running pipeline)
- **Catechism output**: 1 Markdown file (after running pipeline)

## File Naming Conventions

- **Extraction scripts**: `extract_{source}.py`
- **Bible files**: `{BookName}.md` (e.g., `Genesis.md`, `Apocalypse.md`)
- **Commentary files**: `{book_name}_commentary.md` (structure depends on EPUB)
- **Catechism file**: `Catholic_Catechism_Trent_McHugh_Callan.md`
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

