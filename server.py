"""
Step 3: FastAPI Server
------------------------
Wraps ingest.py and ask.py logic into a web server with two endpoints:
  POST /upload  -> upload a PDF, it gets chunked + embedded + stored
  POST /ask     -> ask a question, get an answer based on uploaded PDFs

Run: uvicorn server:app --reload
Then open: http://127.0.0.1:8000/docs  (auto-generated test UI)
"""

import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pypdf import PdfReader
import chromadb
from google import genai

# --- CONFIG ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
EMBEDDING_MODEL = "gemini-embedding-001"
GENERATION_MODEL = "gemini-2.5-flash"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "documents"
TOP_K = 3
UPLOAD_DIR = "./data"

app = FastAPI(title="RAG Document Q&A")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_genai_client():
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not set on server")
    return genai.Client(api_key=GEMINI_API_KEY)


def get_collection():
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    return chroma_client.get_or_create_collection(name=COLLECTION_NAME)


def extract_text_from_pdf(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def chunk_text(text: str, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end].strip())
        start += chunk_size - overlap
    return [c for c in chunks if len(c) > 30]


def embed_texts(client, texts):
    return [
        client.models.embed_content(model=EMBEDDING_MODEL, contents=t).embeddings[0].values
        for t in texts
    ]


def embed_query(client, question: str):
    result = client.models.embed_content(model=EMBEDDING_MODEL, contents=question)
    return result.embeddings[0].values


def retrieve_chunks(collection, query_embedding, top_k=TOP_K, source_filter=None):
    query_kwargs = {"query_embeddings": [query_embedding], "n_results": top_k}
    if source_filter:
        query_kwargs["where"] = {"source": source_filter}
    results = collection.query(**query_kwargs)
    return list(zip(results["documents"][0], results["metadatas"][0]))


def generate_answer(client, question: str, retrieved_chunks):
    context = "\n\n---\n\n".join(
        f"[Source: {meta['source']}]\n{text}" for text, meta in retrieved_chunks
    )
    prompt = f"""You are a helpful assistant answering questions based ONLY on the provided context.
If the answer isn't in the context, say so clearly instead of guessing.

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:"""
    response = client.models.generate_content(model=GENERATION_MODEL, contents=prompt)
    return response.text


class AskRequest(BaseModel):
    question: str
    source: str | None = None


@app.get("/")
def root():
    return {"status": "ok", "message": "RAG Q&A server is running"}


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    save_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    client = get_genai_client()
    raw_text = extract_text_from_pdf(save_path)
    chunks = chunk_text(raw_text)

    if not chunks:
        raise HTTPException(status_code=400, detail="Could not extract any text from this PDF")

    embeddings = embed_texts(client, chunks)

    collection = get_collection()
    ids = [f"{file.filename}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"source": file.filename, "chunk_index": i} for i in range(len(chunks))]
    collection.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)

    return {
        "filename": file.filename,
        "chunks_created": len(chunks),
        "total_chunks_in_db": collection.count(),
    }


@app.post("/ask")
async def ask_question(request: AskRequest):
    client = get_genai_client()
    collection = get_collection()

    if collection.count() == 0:
        raise HTTPException(status_code=400, detail="No documents uploaded yet")

    query_embedding = embed_query(client, request.question)
    retrieved = retrieve_chunks(collection, query_embedding, source_filter=request.source)

    if not retrieved:
        raise HTTPException(
            status_code=400,
            detail=f"No chunks found for source '{request.source}'. Check the filename matches exactly."
        )

    answer = generate_answer(client, request.question, retrieved)

    sources = list({meta["source"] for _, meta in retrieved})

    return {"question": request.question, "answer": answer, "sources": sources}