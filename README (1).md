# RAG Document Q&A System

A full-stack Retrieval-Augmented Generation (RAG) application that lets you upload PDF documents and ask natural-language questions about them. The system retrieves the most relevant chunks of text using vector similarity search and generates accurate, grounded answers using Google's Gemini API.

**Live demo:** https://rag-qa-system-tau.vercel.app/

## What it does

1. Upload one or more PDF documents through the web interface
2. The system extracts text, splits it into overlapping chunks, and embeds each chunk into a vector representation
3. Ask a question — the system finds the most relevant chunks (optionally filtered to a specific document) and passes them to Gemini to generate a grounded answer
4. Answers include the source document(s) used to generate them

## Tech stack

**Backend**
- FastAPI — REST API serving upload and query endpoints
- ChromaDB — local vector database for storing document embeddings
- Google Gemini API — `gemini-embedding-001` for embeddings, `gemini-2.5-flash` for answer generation
- pypdf — PDF text extraction

**Frontend**
- React (Vite)
- Vanilla CSS with a custom design system

**Deployment**
- Backend hosted on Render
- Frontend hosted on Vercel

## Architecture

```
+-------------+      +--------------+      +-------------+
|   React     |----->|   FastAPI    |----->|   ChromaDB  |
|  Frontend   |<-----|   Backend    |<-----| (vector DB) |
+-------------+      +------+-------+      +-------------+
                             |
                             v
                     +--------------+
                     |  Gemini API  |
                     | (embed + LLM)|
                     +--------------+
```

## Project structure

```
rag-qa-system/
├── server.py          # FastAPI backend (upload + ask endpoints)
├── ingest.py           # Standalone CLI script for PDF ingestion
├── ask.py               # Standalone CLI script for Q&A
├── requirements.txt
├── data/                # Uploaded PDFs (local dev only)
├── chroma_db/           # Vector database storage (local dev only)
└── frontend/
    ├── src/
    │   ├── App.jsx      # Main React component
    │   └── App.css      # Styling
    └── package.json
```

## Running locally

### Prerequisites
- Python 3.10+
- Node.js 18+
- A free Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)

### Backend

```bash
pip install -r requirements.txt
export GEMINI_API_KEY="your-key-here"   # Windows: set GEMINI_API_KEY=your-key-here
python -m uvicorn server:app --reload
```

The API will be live at `http://127.0.0.1:8000`. Interactive docs at `http://127.0.0.1:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the printed local URL (typically `http://localhost:5173`).

## API endpoints

| Method | Endpoint  | Description                                      |
|--------|-----------|---------------------------------------------------|
| POST   | `/upload` | Upload a PDF; returns chunk count and total chunks |
| POST   | `/ask`    | Ask a question; optional `source` field to filter to one document |

### Example request

```json
POST /ask
{
  "question": "What skills are required for this role?",
  "source": "JD - SDE Intern.pdf"
}
```

### Example response

```json
{
  "question": "What skills are required for this role?",
  "answer": "The required skills include...",
  "sources": ["JD - SDE Intern.pdf"]
}
```

## Known limitations

- The free-tier Render deployment does not persist local disk storage across cold starts — uploaded documents need to be re-uploaded after a period of inactivity. This is acceptable for demo purposes but would need object storage (e.g. S3) or a managed vector database for production use.
- Currently supports PDF files only.

## Future improvements

- Persistent storage via a managed vector database (e.g. Pinecone, Chroma Cloud)
- Support for additional file types (docx, txt)
- Streaming responses for faster perceived answer generation
- User authentication and per-user document isolation
