# Douay-Rheims Bible Extraction

This directory contains the extraction script for the Douay-Rheims Bible (1899 American Edition).

## Overview

The script downloads the Bible directly from `bible-api.com`, which provides structured access to Bible texts. The API sources its text from `ebible.org`, a standard for public domain Bible data. This ensures:

- **Data Integrity**: Official API source with structured JSON responses
- **Canon Accuracy**: Automatically fetches all books for Catholic translation (66 books in API, though Catholic canon has 73)
- **Clean Formatting**: Outputs standard Markdown ready for NotebookLM
- **Structured Data**: Three-level API (books → chapters → verses) provides granular access

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

- `dra` - Douay-Rheims 1899 American Edition (Catholic, 73 books)

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

