import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("API_KEY")
# STORE_NAME = os.getenv("FILE_SEARCH_STORE_NAME", "").strip()
STORE_NAME = 'fileSearchStores/ukulelefilesearchstore-xacvz396r7kw'

if not API_KEY:
    raise ValueError("Missing API_KEY in .env")

client = genai.Client(api_key=API_KEY)


def ask(SYSTEM_PROMPT, QUESTION):
    print(f"Store: {STORE_NAME}")
    print(f"Question: {QUESTION}\n")

    interaction = client.interactions.create(
    model="gemini-3.5-flash",
    input=SYSTEM_PROMPT + "\n\nUser question: " + QUESTION,
    tools=[{
        "type": "file_search",
        "file_search_store_names": [STORE_NAME]
        }]
    )

    for step in interaction.steps:
        if step.type == "model_output":
            for block in step.content:
                if block.type == "text":
                    print(block.text)
                    if block.annotations:
                        print("\n--- Sources ---")
                        for ann in block.annotations:
                            if ann.type == "file_citation":
                                print(f"  {ann.file_name}")

SYSTEM_PROMPT = """\
You are a helpful, factual, and concise OptiSigns support assistant.
Answer ONLY based on the provided documents.
- Use at most 5 bullet points.
- If more detail is needed, cite the article URL.
- Always include up to 3 "Article URL" citations at the end.
"""

QUESTION = "How do I add a YouTube video?"

ask(SYSTEM_PROMPT, QUESTION)