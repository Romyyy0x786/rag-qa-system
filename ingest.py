"""
Step 1: Document Ingestion Pipeline
------------------------------------
Takes a PDF -> extracts text -> splits into chunks -> embeds each chunk
with Gemini -> stores embeddings + text in ChromaDB (a local vector database).

Run: python ingest.py data/sample.pdf
"""

import sys
import os
from pypdf import PdfReader
import chromadb
from google import genai

# --- CONFIG ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
EMBEDDING_MODEL = "gemini-embedding-001"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "documents"


def extract_text_from_pdf(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    full_text = []
    for page in reader.pages:
        text = page.extract_text() or ""
        full_text.append(text)
    return "\n".join(full_text)


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk.strip())
        start += chunk_size - overlap
    return [c for c in chunks if len(c) > 30]


def embed_texts(client, texts):
    embeddings = []
    for text in texts:
        result = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
        )
        embeddings.append(result.embeddings[0].values)
    return embeddings


def ingest_pdf(pdf_path: str):
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "Set the GEMINI_API_KEY environment variable before running.\n"
            "Get a free key at: https://aistudio.google.com/apikey"
        )

    print(f"[1/4] Reading PDF: {pdf_path}")
    raw_text = extract_text_from_pdf(pdf_path)
    print(f"      Extracted {len(raw_text)} characters")

    print(f"[2/4] Chunking text (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    chunks = chunk_text(raw_text)
    print(f"      Created {len(chunks)} chunks")

    print(f"[3/4] Embedding {len(chunks)} chunks with Gemini ({EMBEDDING_MODEL})")
    client = genai.Client(api_key=GEMINI_API_KEY)
    embeddings = embed_texts(client, chunks)

    print(f"[4/4] Storing in ChromaDB at {CHROMA_PATH}")
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)

    doc_name = os.path.basename(pdf_path)
    ids = [f"{doc_name}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"source": doc_name, "chunk_index": i} for i in range(len(chunks))]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
    )

    print(f"\nDone. {len(chunks)} chunks from '{doc_name}' are now searchable.")
    print(f"Total documents in collection: {collection.count()}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ingest.py data/your.pdf")
        sys.exit(1)
    ingest_pdf(sys.argv[1])