# Douay-Rheims Bible Extraction

This directory contains the extraction script for the Douay-Rheims Bible (1899 American Edition).

## Overview

The script downloads the Bible directly from `bible-api.com`, which provides structured access to Bible texts. The API sources its text from `ebible.org`, a standard for public domain Bible data. This ensures:

- **Data Integrity**: Official API source with structured JSON responses
- **Canon Accuracy**: Automatically fetches all available books from the API
- **Clean Formatting**: Outputs standard Markdown ready for NotebookLM
- **Structured Data**: Three-level API (books → chapters → verses) provides granular access

## Extraction Approach: Patchwork Solution (MVP)

This directory uses a **patchwork approach** to extract the complete 73-book Catholic canon:

### Two-Source Strategy

1. **Primary Source (66 books)**: `bible-api.com` API
   - Provides the Protestant canon (66 books)
   - Free, reliable, well-structured API
   - Extracted via `extract_bible.py`

2. **Secondary Source (7 books)**: GitHub Repository
   - Provides the 7 missing Deuterocanonical books
   - Free, publicly available JSON files
   - Extracted via `extract_deuterocanonical.py`

### Why This Approach?

**Advantages:**
- ✅ **No API subscription costs** - Both sources are free
- ✅ **Complete Catholic canon** - All 73 books available
- ✅ **MVP-ready** - Good enough for initial deployment
- ✅ **Consistent format** - Both scripts output identical Markdown structure

**Limitations:**
- ⚠️ **Not a unified source** - Requires running two separate scripts
- ⚠️ **GitHub dependency** - Relies on external repository availability
- ⚠️ **Less robust** - Not as production-ready as a single API source
- ⚠️ **Manual coordination** - Both scripts must be run to get complete canon

**Future Improvement:**
This is an MVP solution. For production use, consider migrating to a unified API source (e.g., IQ Bible API) that provides all 73 books from a single, reliable endpoint. The current patchwork approach works well for development and initial deployment but may be improved with a better source in the future.

## Deuterocanonical Books Extraction

A separate script (`extract_deuterocanonical.py`) extracts the 7 missing Deuterocanonical books from the GitHub repository [xxruyle/Bible-DouayRheims](https://github.com/xxruyle/Bible-DouayRheims/tree/main/Douay-Rheims).

### Usage

```bash
python extract_deuterocanonical.py
```

This script:
- Downloads JSON files for the 7 Deuterocanonical books from GitHub
- Converts them to the same Markdown format as the main extraction script
- Saves them to the same output directory (`data_final/bible_douay_rheims/`)
- Handles different JSON structures automatically
- Includes retry logic, rate limiting, and SSL fallback
- Sorts verses numerically to ensure correct order

### Books Extracted

- Tobit (TOB) - Position 17 (14 chapters)
- Judith (JDT) - Position 18 (11 chapters)
- Wisdom (WIS) - Position 27 (19 chapters)
- Sirach (SIR) - Position 28 (48 chapters)
- Baruch (BAR) - Position 32 (6 chapters)
- 1 Maccabees (1MA) - Position 20 (16 chapters)
- 2 Maccabees (2MA) - Position 21 (14 chapters)

### Complete Extraction Workflow

To extract all 73 books of the Catholic canon:

1. **Extract 66 books from bible-api.com:**
   ```bash
   python extract_bible.py
   ```

2. **Extract 7 Deuterocanonical books from GitHub:**
   ```bash
   python extract_deuterocanonical.py
   ```

Both scripts output to the same directory (`data_final/bible_douay_rheims/`) and use the same Markdown format, ensuring consistency. The Deuterocanonical books are automatically placed in their correct canonical positions (17, 18, 20, 21, 27, 28, 32).

## Current Status: Complete 73-Book Catholic Canon ✅

**Status:** The complete 73-book Catholic canon is now available through the patchwork approach:
- ✅ 66 books from bible-api.com
- ✅ 7 Deuterocanonical books from GitHub
- ✅ All books in correct canonical positions
- ✅ Consistent Markdown formatting across all books

## Future Improvements

### Potential Migration to Unified API

While the current patchwork approach works well for MVP, future improvements could include:

**Option 1: IQ Bible API**
- Provides all 73 books from a single API
- Well-documented with dedicated endpoints for Deuterocanonical books
- Requires API subscription (freemium model available)
- Documentation: [https://iqbible.com/api-docs/](https://iqbible.com/api-docs/)

**Option 2: Other Unified Sources**
- Various Bible APIs and services may provide complete Catholic canon
- Would eliminate need for two separate extraction scripts
- Would provide more robust, production-ready solution

**Current Approach:**
The patchwork solution (API + GitHub) is sufficient for MVP and development. Migration to a unified source can be considered when:
- Project proves valuable and warrants investment
- Production deployment requires more robust solution
- Single-source reliability becomes a priority

## Usage

### Main Bible Extraction (66 books)

```bash
python extract_bible.py
```

### Deuterocanonical Books Extraction (7 books)

```bash
python extract_deuterocanonical.py
```

## Output

The script generates Markdown files (one per book) directly in `data_final/bible_douay_rheims/` (final output location).

Each file contains:
- Frontmatter with title and tags
- Book title as H1 header
- Chapters as H2 headers
- Verses formatted as `**verse_number** verse_text`

## API Documentation

The script uses the `bible-api.com` API, which provides structured access to Bible texts. The API structure is:

### Endpoints

1. **Get Book List**: `GET https://bible-api.com/data/{translation_id}`
   - Returns: Translation metadata and list of all books
   - Response structure:
     ```json
     {
       "translation": {
         "identifier": "dra",
         "name": "Douay-Rheims 1899 American Edition",
         "language": "English",
         "language_code": "eng",
         "license": "Public Domain"
       },
       "books": [
         {
           "id": "GEN",
           "name": "Genesis",
           "url": "https://bible-api.com/data/dra/GEN"
         }
       ]
     }
     ```

2. **Get Book Chapters**: `GET https://bible-api.com/data/{translation_id}/{book_id}`
   - Returns: Translation metadata and list of chapters for the book
   - Response structure:
     ```json
     {
       "translation": {...},
       "chapters": [
         {
           "book_id": "GEN",
           "book": "Genesis",
           "chapter": 1,
           "url": "https://bible-api.com/data/dra/GEN/1"
         }
       ]
     }
     ```

3. **Get Chapter Verses**: `GET https://bible-api.com/data/{translation_id}/{book_id}/{chapter}`
   - Returns: Translation metadata and list of verses for the chapter
   - Response structure:
     ```json
     {
       "translation": {...},
       "verses": [
         {
           "book_id": "GEN",
           "book": "Genesis",
           "chapter": 1,
           "verse": 1,
           "text": "In the beginning God created heaven, and earth."
         }
       ]
     }
     ```

### Translation IDs

- `dra` - Douay-Rheims 1899 American Edition (Note: API only provides 66 books, not the full 73-book Catholic canon)

### Rate Limiting

The API is rate-limited. The script includes a configurable delay (default: 0.5 seconds) between requests to respect API limits.

## Configuration

The script uses settings from `data_engineering/config/pipeline_config.yaml`:
- API base URL: `https://bible-api.com/data/dra`
- Translation ID: `dra` (Douay-Rheims 1899 American Edition)
- Rate limiting: 0.5 second delay between requests

## Requirements

- Internet connection
- `requests` library
- Python 3.10+

## Notes

- The API is rate-limited, so the script includes delays between requests
- All books are automatically detected and downloaded from the API
- Files are saved with safe filenames (spaces replaced with underscores)
- The API requires three requests per book: one for book list, one for chapter list, and one per chapter for verses
- Network timeouts are set to 30 seconds per request

## API Source

- **API**: [bible-api.com](https://bible-api.com)
- **Data Source**: ebible.org (public domain Bible data)
- **License**: Public Domain
- **No API Key Required**: The API is free and open to use

