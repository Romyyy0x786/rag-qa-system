"""
Step 2: Ask Questions (Retrieval + Generation)
------------------------------------------------
Takes a question -> finds the most relevant chunks from ChromaDB ->
sends those chunks + the question to Gemini -> prints the answer.

Run: python ask.py "What is the required experience for this role?"
"""

import sys
import os
import chromadb
from google import genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
EMBEDDING_MODEL = "gemini-embedding-001"
GENERATION_MODEL = "gemini-2.5-flash"
CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "documents"
TOP_K = 3  # how many chunks to retrieve


def embed_query(client, question: str):
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=question,
    )
    return result.embeddings[0].values


def retrieve_chunks(collection, query_embedding, top_k=TOP_K):
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    return list(zip(documents, metadatas))


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

    response = client.models.generate_content(
        model=GENERATION_MODEL,
        contents=prompt,
    )
    return response.text


def ask(question: str):
    if not GEMINI_API_KEY:
        raise RuntimeError("Set the GEMINI_API_KEY environment variable before running.")

    client = genai.Client(api_key=GEMINI_API_KEY)
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)

    if collection.count() == 0:
        print("No documents found. Run ingest.py on a PDF first.")
        return

    print(f"[1/3] Embedding question: {question}")
    query_embedding = embed_query(client, question)

    print(f"[2/3] Retrieving top {TOP_K} relevant chunks")
    retrieved = retrieve_chunks(collection, query_embedding)
    for i, (text, meta) in enumerate(retrieved):
        print(f"      Chunk {i+1} from {meta['source']}: {text[:60]}...")

    print(f"[3/3] Generating answer with {GENERATION_MODEL}\n")
    answer = generate_answer(client, question, retrieved)

    print("=" * 50)
    print("ANSWER:")
    print(answer)
    print("=" * 50)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python ask.py "Your question here"')
        sys.exit(1)
    ask(sys.argv[1])