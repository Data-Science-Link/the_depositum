# Douay-Rheims Bible Extraction

This directory contains the extraction script for the Douay-Rheims Bible (1899 American Edition).

## Overview

The script downloads the Bible directly from `bible-api.com`, which provides structured access to Bible texts. The API sources its text from `ebible.org`, a standard for public domain Bible data. This ensures:

- **Data Integrity**: Official API source with structured JSON responses
- **Canon Accuracy**: Automatically fetches all available books from the API
- **Clean Formatting**: Outputs standard Markdown ready for NotebookLM
- **Structured Data**: Three-level API (books → chapters → verses) provides granular access

## Important Note: Missing Deuterocanonical Books

⚠️ **The `bible-api.com` service only provides 66 books (Protestant canon), not the full 73-book Catholic canon.**

The script will detect and attempt to fetch the 7 missing deuterocanonical books:
- Tobit (TOB)
- Judith (JDT)
- Wisdom (WIS)
- Sirach/Ecclesiasticus (SIR)
- Baruch (BAR)
- 1 Maccabees (1MA)
- 2 Maccabees (2MA)

However, these books are **not available** from the `bible-api.com` API. The script will:
- Log a clear warning about missing books
- Continue processing the 66 available books
- Return an error exit code (1) to indicate incomplete extraction

**Current Status:** The extraction is functional for the 66 books available from `bible-api.com`. The missing 7 deuterocanonical books are not included in the current output.

## Future Plans: Transition to IQ Bible API

**Planned Migration:** Once the NotebookLM project proves worthwhile with the current data sources (Catechism and Commentary), we plan to transition to the [IQ Bible API](https://iqbible.com/api-docs/) to obtain the complete 73-book Catholic canon.

### Why IQ Bible API?

The IQ Bible API provides:
- ✅ **Complete Catholic Canon**: All 73 books including the 7 deuterocanonical books (Tobit, Judith, Wisdom, Sirach, Baruch, 1 Maccabees, 2 Maccabees)
- ✅ **Douay-Rheims Translation**: Full support for the Douay-Rheims 1899 American Edition
- ✅ **Well-Documented**: Comprehensive API documentation with clear endpoints
- ✅ **Extra-Biblical Endpoints**: Dedicated endpoints for deuterocanonical books (`GetBooksExtraBiblical`, `GetChapterExtraBiblical`)

### Implementation Timeline

The migration to IQ Bible API will be implemented **after**:
1. ✅ Completion of Catechism extraction
2. ✅ Completion of Commentary extraction
3. ✅ Validation that the NotebookLM project provides value with the current 66-book dataset

This approach allows us to:
- Focus on completing other data sources first
- Validate the project's usefulness before investing in API subscriptions
- Ensure a smooth transition when ready

### IQ Bible API Details

- **Documentation**: [https://iqbible.com/api-docs/](https://iqbible.com/api-docs/)
- **Access**: Available via RapidAPI (requires API key subscription)
- **Pricing**: Freemium model with free tier available for testing
- **Endpoints**: Uses `GetChapterExtraBiblical` endpoint for deuterocanonical books

## Usage

```bash
python extract_bible.py
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

