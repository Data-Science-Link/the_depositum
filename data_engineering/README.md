# Data Engineering Pipeline

This folder contains all the technical components for extracting, processing, and transforming Catholic texts from their source formats into clean Markdown files optimized for NotebookLM.

## Why Markdown?

Markdown format is specifically chosen for AI compatibility:
- **Structured yet simple**: Hierarchical headers and formatting that AI systems parse easily
- **NotebookLM optimized**: Preferred format for optimal ingestion and querying
- **Metadata support**: YAML frontmatter enables structured organization
- **Universal compatibility**: Works across AI platforms and text editors
- **Clean text focus**: Minimal markup lets AI models focus on content

The three datasets (Bible, Commentary, Catechism) represent the Deposit of Faith - Scripture, Tradition, and Magisterium - ensuring AI responses draw from authoritative Catholic sources as an integrated whole.

## 📁 Contents

### Data Sources
- `data_sources/bible_douay_rheims/` - Douay-Rheims Bible extraction from bible-api.com
  - `extract_bible.py` - Main extraction script
  - `README.md` - Extraction guide and documentation
- `data_sources/bible_commentary_haydock/` - Haydock Commentary extraction from EPUB
  - `extract_commentary.py` - Main extraction script
  - `README.md` - Extraction guide and documentation
- `data_sources/catholic_catechism_trent/` - Roman Catechism extraction from PDF
  - `extract_catechism.py` - Main extraction script
  - `README.md` - Extraction guide and documentation
- `data_sources/README.md` - Overview of all data sources

### Configuration
- `config/pipeline_config.yaml` - Central pipeline configuration file

### Scripts
- `scripts/run_pipeline.py` - Main pipeline orchestrator with command-line interface

### Processed Data
- `processed_data/` - Intermediate processed files before final formatting (generated, not version controlled)

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- **uv** (fast Python package manager) - [Installation instructions below](#installing-uv)
- Internet connection (for Bible API)
- EPUB file for Haydock Commentary (download separately)
- PDF file for Catechism (download separately)

### Installing uv

This project uses `uv` for dependency management. Install it first:

```bash
# macOS (recommended)
brew install uv

# Linux/Windows (alternative)
curl -LsSf https://astral.sh/uv/install.sh | sh
# Or: pip install uv
```

**Why uv?**
- **10-100x faster** than pip
- Automatic virtual environment management
- Better dependency resolution
- Modern Python packaging standard
- Uses `pyproject.toml` for dependency management

### Installation

1. **Set up virtual environment and install dependencies**:
   ```bash
   # From project root
   cd /path/to/the_depositum

   # Create virtual environment in project root (.venv/)
   # This creates .venv/ directory in the project root
   uv venv

   # Install all dependencies from pyproject.toml
   # Automatically installs project in editable mode
   uv sync

   # Optional: Install with dev dependencies for testing
   uv sync --extra dev
   ```

   **Note**:
   - The virtual environment is created at `.venv/` in the project root
   - `uv sync` reads `pyproject.toml` and installs all dependencies automatically
   - The project is installed in editable mode, so code changes are immediately available
   - You can use `uv run <command>` to run commands without activating the venv manually

2. **Activate virtual environment** (optional):
   ```bash
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

   **Alternative**: Use `uv run` to execute commands in the venv without activation:
   ```bash
   uv run python data_engineering/scripts/run_pipeline.py
   ```

2. **Set up environment variables** (optional):
   ```bash
   cp ../.env.example ../.env
   # Edit .env with any custom configuration
   ```

3. **Download source files** (⚠️ **REQUIRED - files not included in repo**):
   - **Haydock Commentary**:
     - **Direct Download**: [Haydock Catholic Bible Commentary - Haydock, George Leo.epub](https://isidore.co/CalibreLibrary/Haydock,%20George%20Leo/Haydock%20Catholic%20Bible%20Commentary%20(3948)/Haydock%20Catholic%20Bible%20Commentary%20-%20Haydock,%20George%20Leo.epub) (~4.6MB)
     - Place in `data_sources/bible_commentary_haydock/`
     - See [bible_commentary_haydock/README.md](data_sources/bible_commentary_haydock/README.md) for detailed instructions
   - **Catechism**:
     - **Direct Download**: [The Roman Catechism.pdf](https://www.saintsbooks.net/books/The%20Roman%20Catechism.pdf) (~1.6MB)
     - Place `The Roman Catechism.pdf` in `data_sources/catholic_catechism_trent/`
     - See [catholic_catechism_trent/README.md](data_sources/catholic_catechism_trent/README.md) for detailed instructions

   **Note**: Source files (EPUB, PDF) are excluded from git via `.gitignore` to keep repository size small. Users must download them separately.

## 🔧 Running Individual Extractors

### Douay-Rheims Bible

```bash
cd data_sources/bible_douay_rheims
python extract_bible.py
```

**Output**: 73 Markdown files in `processed_data/bible_douay_rheims/`

**Configuration**:
- API endpoint: `https://bible-api.com/data/dra`
- Translation ID: `dra` (Douay-Rheims 1899 American Edition)
- Rate limiting: 0.5 second delay between requests

### Haydock Commentary

```bash
cd data_sources/bible_commentary_haydock
python extract_commentary.py
```

**Prerequisites**: EPUB file must be in `bible_commentary_haydock/` directory (the script looks for files matching the pattern `Haydock Catholic Bible Comment*.epub`)

**Output**: Commentary files in `processed_data/bible_commentary_haydock/`

**Note**: You may need to inspect the EPUB structure and adjust parsing logic based on the specific EPUB version you download.

### Roman Catechism

```bash
cd data_sources/catholic_catechism_trent
python extract_catechism.py
```

**Prerequisites**: PDF file (`The Roman Catechism.pdf`) must be in the `catholic_catechism_trent/` directory

**Output**: Single Markdown file (`Catholic_Catechism_Trent_McHugh_Callan.md`) in `data_final/catholic_catechism_trent/`

## 🔄 Running the Full Pipeline

From the project root:

```bash
python data_engineering/scripts/run_pipeline.py
```

This will:
1. Extract all three data sources
2. Validate the output
3. Copy final files to `data_final/` at project root

## 📊 Data Quality Checks

### Validation Scripts

```bash
# Validate outputs (built into pipeline)
python data_engineering/scripts/run_pipeline.py --validate
```

### Expected Outputs

**Douay-Rheims Bible**:
- 66 files (Bible_Book_01_Genesis.md through Bible_Book_73_Revelation.md - currently missing 7 deuterocanonical books)
- Each file contains frontmatter, book title, chapters, and verses
- Format: `**verse_number** verse_text`

**Haydock Commentary**:
- Files organized by book/chapter
- Commentary notes separated from verse text
- Proper Markdown headers

**Roman Catechism**:
- Single file: `Catholic_Catechism_Trent_McHugh_Callan.md`
- Headers: `# PART`, `## ARTICLE`, `##` for major sections, `###` for subsections, `####` for italicized section titles
- Clean text with proper formatting
- All content preserved from PDF (only formatting artifacts removed)

## 🧪 Testing

### Unit Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test suite
python -m pytest tests/test_bible_extraction.py
python -m pytest tests/test_commentary_extraction.py
python -m pytest tests/test_catechism_extraction.py
```

### Integration Tests

```bash
# Test full pipeline
python data_engineering/scripts/run_pipeline.py --test
```

## ⚙️ Configuration

### Pipeline Configuration

Edit `data_engineering/config/pipeline_config.yaml` to customize:
- Output directories
- File naming conventions
- Markdown formatting options
- API endpoints and rate limits

### Environment Variables

Create `.env` file at project root (optional):

```bash
# API Configuration
BIBLE_API_BASE_URL=https://bible-api.com/data/dra
API_RATE_LIMIT_DELAY=0.5

# File Paths
HAYDOCK_EPUB_PATH=data_engineering/data_sources/bible_commentary_haydock/Haydock Catholic Bible Comment - Haydock, George Leo_3948.epub
CATECHISM_PDF_PATH=data_engineering/data_sources/catholic_catechism_trent/The Roman Catechism.pdf

# Output Directories
OUTPUT_DIR=data_final
LOG_DIR=logs
```

## 🔍 Troubleshooting

### Installation Issues

- **uv not found**: Install uv using the commands above, or add it to your PATH
- **Virtual environment not activating**: Ensure you're in the project root and `.venv/` exists
- **Import errors**: Make sure virtual environment is activated and run `uv sync` again

### Bible Extraction Issues

- **API Timeouts**: Increase delay between requests in config
- **Missing Books**: Verify API endpoint is accessible
- **Encoding Errors**: Ensure UTF-8 encoding throughout

### Commentary Extraction Issues

- **EPUB Structure**: Inspect EPUB HTML to find correct class names
- **Missing Content**: Adjust BeautifulSoup selectors based on EPUB version
- **File Not Found**: Verify EPUB is in `bible_commentary_haydock/` directory and filename matches the pattern expected by the script

### Catechism Extraction Issues

- **PDF Parsing Errors**: Check PDF structure and header detection patterns
- **Header Detection**: Adjust regex patterns for header detection
- **Footnotes**: May require manual cleanup after extraction

### uv-Specific Tips

- **Update dependencies**: `uv sync --upgrade`
- **Check installed packages**: `uv pip list`
- **Recreate virtual environment**: Delete `.venv/` and run `uv venv` then `uv sync`
- **Install specific version**: Edit `pyproject.toml` and run `uv sync`

## 📈 Data Flow

```
Raw Sources → Extraction Scripts → Validation → Processed Data
     ↓              ↓                  ↓              ↓
  API/EPUB/PDF   Python Scripts    Quality Checks  Markdown Files
```

## 🔒 Security & Privacy

- **No API Keys Required**: Bible API is public
- **No PII**: All texts are public domain
- **Local Processing**: All extraction happens locally
- **Source Verification**: Scripts verify data integrity

## 🤝 Contributing

### Development Setup

1. **Fork and clone the repository**
2. **Set up development environment**:
   ```bash
   uv venv
   uv sync --extra dev  # Installs with dev dependencies
   source .venv/bin/activate  # Optional: activate venv
   ```
3. **Make your changes**
4. **Test your changes**:
   ```bash
   python data_engineering/scripts/run_pipeline.py --test
   ```

### Adding New Extraction Methods

When adding new extraction methods:

1. Create new subdirectory in `data_sources/`
2. Include extraction script and README
3. Add validation script
4. Update pipeline runner
5. Add tests
6. Update `pyproject.toml` if new dependencies are needed
7. Update this README

## 📞 Support

For technical issues:
- Check logs in `data_engineering/logs/` directory
- Review extraction method guides in project root
- Open GitHub issue with specific error details

