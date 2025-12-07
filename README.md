# The Depositum: Catholic Catechist Data Pipeline

A reproducible data engineering pipeline for extracting, processing, and formatting public domain Catholic texts for use with NotebookLM and other AI tools.

## Why "The Depositum"?

This project is named "The Depositum" (Latin: "deposit") in reference to the Catholic concept of the **Deposit of Faith** (depositum fidei) - the body of revealed truth entrusted by Christ to the Apostles and their successors. The Deposit of Faith consists of:

1. **Sacred Scripture** - The written Word of God
2. **Sacred Tradition** - The living transmission of the Word of God through the Church
3. **Magisterium** - The teaching authority of the Church that interprets and safeguards both Scripture and Tradition

The three datasets in this project directly correspond to these three components:
- **Douay-Rheims Bible** = Sacred Scripture
- **Haydock Commentary** = Sacred Tradition (Church Fathers' interpretation)
- **Catechism of Trent** = Magisterium (official Church teaching)

Together, they create a digital "depositum" - a repository that preserves and makes accessible the Deposit of Faith in a format suitable for AI-powered study, ensuring responses draw from Scripture, Tradition, and Magisterium as an integrated whole.

## Why Markdown Format?

This pipeline produces Markdown files specifically optimized for AI tools and NotebookLM:

- **Structured Format**: Markdown's hierarchical structure (headers, lists, formatting) is easily parsed by AI systems while remaining human-readable
- **Clean Text**: Minimal markup ensures AI models can focus on content rather than complex formatting
- **Metadata Support**: YAML frontmatter provides structured metadata (titles, tags) that AI tools can leverage for organization and search
- **NotebookLM Compatibility**: Markdown is the preferred format for NotebookLM, ensuring optimal ingestion, querying, and analysis
- **Semantic Structure**: Clear chapter, verse, and section markers enable precise referencing and context-aware responses
- **Universal Compatibility**: Markdown works seamlessly across AI platforms, text editors, and documentation systems

## 🎯 What This Project Provides

- **📖 Douay-Rheims Bible**: 73 books extracted from bible-api.com and converted to Markdown
- **📚 Haydock Bible Commentary**: Full commentary extracted from EPUB format
- **✝️ Roman Catechism (McHugh & Callan)**: Catechism of the Council of Trent converted from RTF to Markdown
- **🔄 Reproducible Pipeline**: Complete automation for data extraction and transformation
- **📁 NotebookLM-Ready Output**: Clean, formatted Markdown files optimized for AI tools

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- **uv** (fast Python package manager) - See installation instructions below
- Internet connection (for API downloads)
- EPUB file for Haydock Commentary (download separately)
- RTF file for Catechism (download separately)

### Installation

**Step 1: Install uv** (if you don't have it):
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Step 2: Set up the project**:
```bash
# Clone the repository
git clone https://github.com/your-username/the_depositum.git
cd the_depositum

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .

# Or install with dev dependencies for testing
uv pip install -e ".[dev]"
```

**Step 3: Download Source Files** (if needed):

**Bible**: ✅ No download needed - The script downloads directly from the API

**Haydock Commentary**:
1. Download EPUB from Isidore E-Book Library or JohnBlood GitLab
2. Place in: `data_engineering/data_sources/bible_commentary_haydock/raw/Haydock Catholic Bible Commentary.epub`

**Catechism**:
1. Download RTF from SaintsBooks.net
2. **Important**: Ensure it's the McHugh & Callan translation (1923)
3. Place in: `data_engineering/data_sources/catholic_catechism_trent/raw/Catechism of the Council of Trent.rtf`

**Step 4: Run the Pipeline**:

```bash
# Run everything
python data_engineering/scripts/run_pipeline.py

# Or run individual sources
python data_engineering/scripts/run_pipeline.py --source bible
python data_engineering/scripts/run_pipeline.py --source commentary
python data_engineering/scripts/run_pipeline.py --source catechism

# Run and copy to final output
python data_engineering/scripts/run_pipeline.py --copy-output
```

**Step 5: Verify Output**:

```bash
# Bible (should have 73 files)
ls data_final/bible_douay_rheims/ | wc -l

# Commentary
ls data_final/bible_commentary_haydock/

# Catechism
ls data_final/catholic_catechism_trent/
```

## 📊 Data Sources: The Three Pillars of the Deposit of Faith

This pipeline extracts and processes three foundational Catholic texts that together represent the complete Deposit of Faith - Scripture, Tradition, and Magisterium. Each source has been carefully selected for its historical significance, doctrinal authority, and public domain status. Together, they ensure that AI responses are grounded in authoritative Catholic teaching.

### Pillar A: Douay-Rheims Bible (1899 American Edition)
- **Source**: bible-api.com (ebible.org data)
- **Format**: API → JSON → Markdown
- **Output**: 73 individual Markdown files (Genesis.md through Apocalypse.md)
- **Script**: `data_engineering/data_sources/bible_douay_rheims/extract_bible.py`
- **No prerequisites**: Downloads directly from API
- **Historical Significance**: First officially authorized Catholic Bible in English, translated from the Latin Vulgate. The 1899 American Edition represents the Challoner revision, which became the standard English Catholic Bible for centuries.
- **Role in Deposit of Faith**: Represents **Sacred Scripture** - the written Word of God

### Pillar B: Haydock Catholic Bible Commentary (1859 Edition)
- **Source**: EPUB file (from Isidore E-Book Library or JohnBlood GitLab)
- **Format**: EPUB → HTML → Markdown
- **Output**: Commentary files organized by book/chapter
- **Script**: `data_engineering/data_sources/bible_commentary_haydock/extract_commentary.py`
- **Prerequisite**: Download EPUB file separately
- **Historical Significance**: Comprehensive Catholic Bible commentary compiled by Father George Leo Haydock, drawing extensively from Church Fathers (Augustine, Jerome, Chrysostom) and traditional Catholic exegesis. The 1859 edition represents the mature form of this influential commentary.
- **Role in Deposit of Faith**: Represents **Sacred Tradition** - the living transmission of how the Church has understood Scripture through the ages, preserving the interpretive insights of the Church Fathers

### Pillar C: Catechism of the Council of Trent (McHugh & Callan Translation, 1923)
- **Source**: RTF file from SaintsBooks.net
- **Format**: RTF → Plain Text → Markdown
- **Output**: Single Markdown file with proper headers
- **Script**: `data_engineering/data_sources/catholic_catechism_trent/extract_catechism.py`
- **Prerequisite**: Download RTF file separately (McHugh & Callan translation, 1923)
- **Historical Significance**: Official catechism commissioned by the Council of Trent (1545-1563) and published in 1566. The McHugh & Callan translation (1923) is considered one of the most accurate English translations, produced by Dominican scholars. This catechism represents authoritative post-Tridentine Catholic doctrine.
- **Role in Deposit of Faith**: Represents **Magisterium** - the teaching authority of the Church providing official interpretation and explanation of the faith

## 🔄 Pipeline Workflow

```
Raw Sources → Extraction Scripts → Processed Data → NotebookLM
     ↓              ↓                    ↓
  API/EPUB/RTF   Python Scripts    Clean Markdown
```

1. **Extraction**: Download and parse source materials
2. **Transformation**: Convert to clean Markdown format
3. **Validation**: Verify data quality and completeness
4. **Output**: Generate final files in `data_final/`

## 📁 Project Structure

```
the_depositum/
├── README.md                    # Main project documentation
├── LICENSE                      # MIT License
├── pyproject.toml               # Python project config & dependencies
├── .gitignore                   # Git ignore rules
│
├── .cursor/                     # Cursor IDE rules (2025 format)
│   └── rules/
│       ├── error-handling.mdc   # Critical error handling rules
│       └── data-engineering.mdc # Data engineering standards
│
├── .github/                     # GitHub configuration
│   ├── CODEOWNERS              # Code review assignments
│   └── workflows/
│       └── security-audit.yml   # Automated security scanning
│
├── data_final/                  # Final output (ready for NotebookLM)
│   ├── README.md               # Output documentation with historical context
│   ├── bible_douay_rheims/     # 73 Bible books (.md files)
│   ├── bible_commentary_haydock/ # Commentary files (.md files)
│   └── catholic_catechism_trent/ # Catechism file (.md file)
│
└── data_engineering/            # All technical components
    ├── README.md                # Technical documentation
    ├── config/
    │   └── pipeline_config.yaml # Pipeline configuration
    ├── scripts/
    │   └── run_pipeline.py      # Main pipeline orchestrator
    ├── data_sources/            # Extraction scripts
    │   ├── README.md           # Data sources overview
    │   ├── douay_rheims/
    │   │   ├── extract_bible.py
    │   │   └── README.md
    │   ├── haydock/
    │   │   ├── extract_commentary.py
    │   │   └── README.md
    │   └── catechism/
    │       ├── extract_catechism.py
    │       └── README.md
    └── processed_data/         # Intermediate processed files
```

## 📋 Complete File Listing

### Root Level Files
- `README.md` - Main project documentation
- `LICENSE` - MIT License
- `pyproject.toml` - Python project configuration and dependencies
- `.gitignore` - Git ignore rules

### Configuration & Rules
- `.cursor/rules/error-handling.mdc` - Error handling standards (applies to all `*.py`)
- `.cursor/rules/data-engineering.mdc` - Data engineering standards (applies to `data_engineering/**/*.py`)
- `.github/CODEOWNERS` - Code review assignments
- `.github/workflows/security-audit.yml` - Security scanning workflow

### Data Engineering Files
- `data_engineering/README.md` - Technical documentation
- `data_engineering/config/pipeline_config.yaml` - Pipeline configuration
- `data_engineering/scripts/run_pipeline.py` - Main pipeline orchestrator
- `data_engineering/data_sources/README.md` - Data sources overview
- `data_engineering/data_sources/bible_douay_rheims/extract_bible.py` - Bible extraction script
- `data_engineering/data_sources/bible_douay_rheims/README.md` - Bible extraction guide
- `data_engineering/data_sources/bible_commentary_haydock/extract_commentary.py` - Commentary extraction script
- `data_engineering/data_sources/bible_commentary_haydock/README.md` - Commentary extraction guide
- `data_engineering/data_sources/catholic_catechism_trent/extract_catechism.py` - Catechism extraction script
- `data_engineering/data_sources/catholic_catechism_trent/README.md` - Catechism extraction guide

### Output Documentation
- `data_final/README.md` - Final output documentation with historical context for all three sources

### Generated Directories (not in version control)
- `data_engineering/processed_data/` - Intermediate processed files
- `data_final/bible_douay_rheims/` - Final Bible output (73 .md files)
- `data_final/bible_commentary_haydock/` - Final commentary output (.md files)
- `data_final/catholic_catechism_trent/` - Final catechism output (.md file)
- `logs/` - Execution logs

## 🎓 Use Case: NotebookLM Integration

This pipeline prepares texts for use with Google's NotebookLM:

1. **Run the pipeline** to generate clean Markdown files
2. **Upload to NotebookLM**: Import the files from `data_final/`
3. **Query the Deposit of Faith**: Ask questions that draw from Scripture, Tradition, and Magisterium
4. **Generate Audio Overviews**: Create podcasts discussing theological topics

### Example Queries

- "Explain the Biblical roots of Confession using only the Gospel of John and the Council of Trent."
- "What do the Psalms and the Church Fathers say about trusting God in times of anxiety?"
- "Explain the Real Presence of the Eucharist using John 6 and the Haydock Commentary."

## 🔒 Data Quality & Validation

- **Completeness Checks**: Verify all expected books/files are present
- **Format Validation**: Ensure proper Markdown structure
- **Content Verification**: Check for missing verses or chapters
- **Encoding Validation**: Ensure UTF-8 encoding throughout

## ⚙️ Configuration

Edit `data_engineering/config/pipeline_config.yaml` to customize:
- API endpoints and rate limits
- File paths
- Output formatting
- Validation rules

## 🤝 Contributing

### Development Setup

1. **Fork and clone the repository**
2. **Set up environment**:
   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -e ".[dev]"
   ```
3. **Run tests**:
   ```bash
   python data_engineering/scripts/run_pipeline.py --test
   ```

### Contribution Guidelines

- **Data Quality**: All extractions must pass validation checks
- **Documentation**: Update README and code comments as needed
- **Testing**: Add tests for new extraction methods
- **Format Consistency**: Maintain consistent Markdown formatting

## 📚 Technical Documentation

For detailed technical information, see:
- **[data_engineering/README.md](data_engineering/README.md)**: Complete technical documentation
- **[data_engineering/data_sources/README.md](data_engineering/data_sources/README.md)**: Data sources overview
- **[data_final/README.md](data_final/README.md)**: Final output documentation with historical context
- **[FILES.md](FILES.md)**: Complete file listing and organization guide
- Individual source READMEs in each `data_sources/{source}/` directory

## 🔍 Troubleshooting

### "File not found" errors
- Ensure source files (EPUB/RTF) are in the correct `raw/` directories
- Check file names match exactly (case-sensitive)

### API timeout errors
- Increase `API_RATE_LIMIT_DELAY` in `data_engineering/config/pipeline_config.yaml`
- Check internet connection

### Parsing errors
- For Haydock: Inspect EPUB structure and adjust parsing logic in extraction script
- For Catechism: Check RTF encoding (script tries UTF-8 and latin-1)

### Import errors
- Ensure virtual environment is activated
- Reinstall dependencies: `uv pip install -e .`

## 🔒 Security

This project implements automated security scanning:

- **Code Security**: Bandit scans Python code for security vulnerabilities
- **Dependency Scanning**: pip-audit checks for known vulnerabilities in dependencies
- **Automated Workflows**: Security audits run on every push and pull request
- **Weekly Scans**: Scheduled security audits run every Monday

Security scans are automatically performed via GitHub Actions. See [`.github/workflows/security-audit.yml`](.github/workflows/security-audit.yml) for details.

To run security scans locally:
```bash
# Install security tools
uv pip install -e ".[dev]"

# Run Bandit code scan
bandit -r data_engineering/

# Run pip-audit dependency scan
pip-audit
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

All source texts (Douay-Rheims, Haydock Commentary, Roman Catechism) are in the public domain and free of copyright restrictions.

## 🙏 Acknowledgments

- **bible-api.com**: For providing structured Bible data
- **ebible.org**: For maintaining public domain Bible texts
- **Isidore E-Book Library / JohnBlood GitLab**: For Haydock Commentary EPUB
- **SaintsBooks.net**: For McHugh & Callan Catechism RTF

---

**Note**: This pipeline is designed for educational and faith formation purposes. The texts are authoritative Catholic sources, but users should consult official Church documents for canonical matters.
