# OptiSigns Help Center RAG Pipeline

End-to-end RAG pipeline that scrapes OptiSigns Help Center articles, converts to Markdown, uploads to **Google Gemini File Search Store**, and serves an AI assistant that answers only from the uploaded documents.

## Architecture

```
Zendesk API ──► scrape.py ──► articles/*.md ──► main.py ──► Gemini File Search Store
                                                      │
                                              hashes.json (SHA256 delta detection)
                                                      │
                                              test.py (chat assistant)
```

```
project/
├── main.py              # Pipeline orchestration
├── scrape.py            # Zendesk scraper + markdown converter
├── upload.py            # Upload all .md to File Search Store
├── test.py              # Interactive chat with the store
├── articles/            # Generated markdown files
├── hashes.json          # SHA256 + doc_name tracking
├── logs/                # Pipeline logs
├── requirements.txt     # Python dependencies
├── Dockerfile           # Containerization
└── .env.sample          # Environment variables template
```

## Setup

### 1. Clone & create `.env`

```bash
git clone <repo-url>
cd <project-dir>
cp .env.sample .env
```

Fill in `.env`:

```env
ZENDESK_API_URL = url
GEMINI_API_KEY = your_gemini_api_key
FILE_SEARCH_STORE_NAME = fileSearchStores/your-store-name-xxxxxxxxxxxx
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create File Search Store (one time)

```bash
python upload.py
```

This creates a new store and prints the name. Save it to `.env` as `FILE_SEARCH_STORE_NAME`.

## How to Run

### Full pipeline (scrape → detect → upload → save hashes)

```bash
python main.py
```

Output:
```
[1/4] Scraping articles...
  Fetched 31 articles
  Saved 31 markdown files
[2/4] Detecting changes...
  2 added, 5 updated, 24 skipped
[3/4] Uploading 7 files to fileSearchStores/...
  [1/7] new-article.md
    -> Done (fileSearchStores/.../documents/...)
[4/4] Saving hashes...
  Saved 31 records to hashes.json
Pipeline complete: 7 files uploaded
```

### Interactive chat

```bash
python test.py
```

## Chunk Strategy

| Parameter | Value |
|---|---|
| Method | White-space chunking (`WhiteSpaceConfig`) |
| Tokens per chunk | 500 (API max: 512) |
| Overlap tokens | 100 (~20%) |

Gemini splits documents by white-space boundaries with 100-token overlap to preserve context across chunk boundaries.


## Delta Sync

`hashes.json` tracks each file:

```json
{
  "article-slug.md": {
    "hash": "sha256...",
    "doc_name": "fileSearchStores/.../documents/..."
  }
}
```

| State | Action |
|---|---|
| New file | Upload |
| Hash changed | Delete old doc → upload new |
| Unchanged | Skip |
| Deleted locally | (handled by temp.py) |

