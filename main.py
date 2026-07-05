"""
main.py - End-to-end RAG pipeline
1. Scrape articles -> markdown
2. Detect changes via SHA256 (hashes.json)
3. Upload only delta to File Search Store
4. Save updated hashes
"""
import os
import json
import hashlib
import glob
import logging
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from scrape import getDemoArticles, saveArticle

load_dotenv()

# --- Config ---
MARKDOWN_DIR = "articles"
HASHES_FILE = "hashes.json"
LOG_FILE = "logs/pipeline.log"
API_KEY = os.getenv("API_KEY")
STORE_NAME = "fileSearchStores/ukulelefilesearchstore-xacvz396r7kw"

if not API_KEY:
    raise ValueError("API_KEY not found in .env")

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logging.getLogger("google.genai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

client = genai.Client(api_key=API_KEY)


def compute_hash(filepath: str) -> str:
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha.update(chunk)
    return sha.hexdigest()


def load_hashes() -> dict:
    if os.path.exists(HASHES_FILE):
        with open(HASHES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_hashes(hashes: dict):
    with open(HASHES_FILE, "w", encoding="utf-8") as f:
        json.dump(hashes, f, indent=2)


def main():
    logger.info("=" * 50)
    logger.info("Pipeline - Starting")

    # Step 1: Scrape
    logger.info("[1/4] Scraping articles...")
    articles = getDemoArticles()
    logger.info(f"  Fetched {len(articles)} articles")
    for article in articles:
        saveArticle(article)
    logger.info(f"  Saved {len(articles)} markdown files")

    # Step 2: Detect changes
    logger.info("[2/4] Detecting changes...")
    old_records = load_hashes()
    current_files = glob.glob(f"{MARKDOWN_DIR}/*.md")
    added, updated, skipped = [], [], []
    new_records = {}

    for filepath in current_files:
        file_hash = compute_hash(filepath)
        filename = os.path.basename(filepath)

        old_record = old_records.get(filename)
        old_hash = old_record["hash"] if isinstance(old_record, dict) else old_record

        if filename not in old_records:
            added.append(filepath)
        elif old_hash != file_hash:
            # Delete old document from store before re-upload
            old_doc_name = old_record.get("doc_name") if isinstance(old_record, dict) else None
            if old_doc_name:
                try:
                    client.file_search_stores.documents.delete(
                        name=old_doc_name, config={"force": True}
                    )
                    logger.info(f"    Deleted old: {old_doc_name}")
                except Exception as e:
                    logger.warning(f"    Could not delete old doc: {e}")
            updated.append(filepath)
        else:
            skipped.append(filepath)
            new_records[filename] = old_record if isinstance(old_record, dict) else {"hash": file_hash}
            continue

        new_records[filename] = {"hash": file_hash}

    logger.info(f"  {len(added)} added, {len(updated)} updated, {len(skipped)} skipped")

    # Step 3: Upload delta
    to_upload = added + updated
    logger.info(f"[3/4] Uploading {len(to_upload)} files to {STORE_NAME}...")

    uploaded = 0
    for filepath in to_upload:
        filename = os.path.basename(filepath)
        try:
            logger.info(f"  [{uploaded+1}/{len(to_upload)}] {filename}")
            operation = client.file_search_stores.upload_to_file_search_store(
                file_search_store_name=STORE_NAME,
                file=filepath,
                config=types.UploadToFileSearchStoreConfig(
                    display_name=filename,
                    chunking_config=types.ChunkingConfig(
                        white_space_config=types.WhiteSpaceConfig(
                            max_tokens_per_chunk=500,
                            max_overlap_tokens=100
                        )
                    )
                )
            )
            while not operation.done:
                time.sleep(3)
                operation = client.operations.get(operation)
            # Extract doc name from operation metadata
            doc_name = None
            if hasattr(operation, 'response') and operation.response:
                doc_name = getattr(operation.response, 'name', None)
            # Fallback: list docs to find the newly created one
            if not doc_name:
                for d in client.file_search_stores.documents.list(parent=STORE_NAME):
                    if d.display_name == filename:
                        doc_name = d.name
                        break
            new_records[filename] = {"hash": compute_hash(filepath), "doc_name": doc_name}
            logger.info(f"    -> Done ({doc_name})")
            uploaded += 1
        except Exception as e:
            logger.error(f"  Failed {filename}: {e}")

    # Step 4: Save hashes
    logger.info("[4/4] Saving hashes...")
    save_hashes(new_records)
    logger.info(f"  Saved {len(new_records)} records to {HASHES_FILE}")

    logger.info(f"Pipeline complete: {uploaded} files uploaded")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()