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
- `data_sources/douay_rheims/` - Douay-Rheims Bible extraction from bible-api.com
- `data_sources/haydock/` - Haydock Commentary extraction from EPUB
- `data_sources/catechism/` - Roman Catechism extraction from RTF

### Processed Data
- `processed_data/` - Intermediate processed files before final formatting

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- **uv** (fast Python package manager) - [Installation instructions below](#installing-uv)
- Internet connection (for Bible API)
- EPUB file for Haydock Commentary (download separately)
- RTF file for Catechism (download separately)

### Installing uv

This project uses `uv` for dependency management. Install it first:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip (if you have it)
pip install uv
```

**Why uv?**
- **10-100x faster** than pip
- Automatic virtual environment management
- Better dependency resolution
- Modern Python packaging standard

### Installation

1. **Install Python dependencies with uv**:
   ```bash
   # From project root
   cd /path/to/the_depositum

   # Create virtual environment (creates .venv/)
   uv venv

   # Activate virtual environment
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate

   # Install project and dependencies
   uv pip install -e ..

   # Or install with dev dependencies for testing
   uv pip install -e "..[dev]"
   ```

   **Note**: The `-e` flag installs the project in "editable" mode, so changes to the code are immediately available.

2. **Set up environment variables** (optional):
   ```bash
   cp ../.env.example ../.env
   # Edit .env with any custom configuration
   ```

3. **Download source files**:
   - **Haydock Commentary**: Download EPUB from Isidore E-Book Library or JohnBlood GitLab
     - Place in `data_sources/haydock/raw/Haydock Catholic Bible Commentary.epub`
   - **Catechism**: Download RTF from SaintsBooks.net
     - Place in `data_sources/catechism/raw/Catechism of the Council of Trent.rtf`

## 🔧 Running Individual Extractors

### Douay-Rheims Bible

```bash
cd data_sources/douay_rheims
python extract_bible.py
```

**Output**: 73 Markdown files in `processed_data/douay_rheims/`

**Configuration**:
- API endpoint: `https://bible-api.com/data/dra`
- Translation ID: `dra` (Douay-Rheims 1899 American Edition)
- Rate limiting: 0.5 second delay between requests

### Haydock Commentary

```bash
cd data_sources/haydock
python extract_commentary.py
```

**Prerequisites**: EPUB file must be in `raw/` directory

**Output**: Commentary files in `processed_data/haydock/`

**Note**: You may need to inspect the EPUB structure and adjust parsing logic based on the specific EPUB version you download.

### Roman Catechism

```bash
cd data_sources/catechism
python extract_catechism.py
```

**Prerequisites**: RTF file must be in `raw/` directory

**Output**: Single Markdown file in `processed_data/catechism/`

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
- 73 files (Genesis.md through Apocalypse.md)
- Each file contains frontmatter, book title, chapters, and verses
- Format: `**verse_number** verse_text`

**Haydock Commentary**:
- Files organized by book/chapter
- Commentary notes separated from verse text
- Proper Markdown headers

**Roman Catechism**:
- Single file: `Catechism_McHugh_Callan.md`
- Headers: `# PART`, `## ARTICLE`, `### QUESTION`
- Clean text with proper formatting

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
HAYDOCK_EPUB_PATH=data_engineering/data_sources/haydock/raw/Haydock Catholic Bible Commentary.epub
CATECHISM_RTF_PATH=data_engineering/data_sources/catechism/raw/Catechism of the Council of Trent.rtf

# Output Directories
OUTPUT_DIR=data_final
LOG_DIR=logs
```

## 🔍 Troubleshooting

### Installation Issues

- **uv not found**: Install uv using the commands above, or add it to your PATH
- **Virtual environment not activating**: Ensure you're in the project root and `.venv/` exists
- **Import errors**: Make sure virtual environment is activated and run `uv pip install -e ..` again

### Bible Extraction Issues

- **API Timeouts**: Increase delay between requests in config
- **Missing Books**: Verify API endpoint is accessible
- **Encoding Errors**: Ensure UTF-8 encoding throughout

### Commentary Extraction Issues

- **EPUB Structure**: Inspect EPUB HTML to find correct class names
- **Missing Content**: Adjust BeautifulSoup selectors based on EPUB version
- **File Not Found**: Verify EPUB is in correct `raw/` directory

### Catechism Extraction Issues

- **RTF Parsing Errors**: Try different encoding (utf-8, latin-1)
- **Header Detection**: Adjust regex patterns for header detection
- **Footnotes**: May require manual cleanup after extraction

### uv-Specific Tips

- **Update dependencies**: `uv pip install -e .. --upgrade`
- **Check installed packages**: `uv pip list`
- **Recreate virtual environment**: Delete `.venv/` and run `uv venv` again
- **Install specific version**: `uv pip install package==version`

## 📈 Data Flow

```
Raw Sources → Extraction Scripts → Validation → Processed Data
     ↓              ↓                  ↓              ↓
  API/EPUB/RTF   Python Scripts    Quality Checks  Markdown Files
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
   source .venv/bin/activate
   uv pip install -e "..[dev]"  # Installs with dev dependencies
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
- Check logs in `logs/` directory
- Review extraction method guides in project root
- Open GitHub issue with specific error details

