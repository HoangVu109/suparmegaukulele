import os
import glob
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env")

STORE_NAME = os.getenv("FILE_SEARCH_STORE_NAME", "").strip()

client = genai.Client(api_key=GEMINI_API_KEY)


def get_or_create_store():
    """Get existing FileSearchStore or create a new one."""
    if STORE_NAME:
        print(f"Using existing store: {STORE_NAME}")
        return STORE_NAME

    print("Creating new FileSearchStore...")
    store = client.file_search_stores.create(
        config=types.CreateFileSearchStoreConfig(
            display_name="ukulelefilesearchstore"
        )
    )
    print(f"  -> {store.name}")
    print(f"  (FILE_SEARCH_STORE_NAME={store.name})")
    return store.name


def upload_all(markdown_dir: str = "articles"):
    """Upload all .md files to the File Search Store with chunking config."""
    store_name = get_or_create_store()
    files = glob.glob(f"{markdown_dir}/*.md")
    print(f"\nFound {len(files)} files\n")

    uploaded = 0
    for filepath in files:
        filename = os.path.basename(filepath)
        try:
            print(f"  [{uploaded+1}/{len(files)}] Uploading {filename}...")

            operation = client.file_search_stores.upload_to_file_search_store(
                file_search_store_name=store_name,
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

            print(f"         -> Done")
            uploaded += 1

        except Exception as e:
            print(f"         -> Error: {e}")

    print(f"\nDone: {uploaded}/{len(files)} files uploaded to {store_name}")



upload_all()

