\# RAG Document Q\&A System



A full-stack Retrieval-Augmented Generation (RAG) application that lets you upload PDF documents and ask natural-language questions about them. The system retrieves the most relevant chunks of text using vector similarity search and generates accurate, grounded answers using Google's Gemini API.



\*\*Live demo:\*\* https://rag-qa-system-tau.vercel.app/



\## What it does



1\. Upload one or more PDF documents through the web interface

2\. The system extracts text, splits it into overlapping chunks, and embeds each chunk into a vector representation

3\. Ask a question — the system finds the most relevant chunks (optionally filtered to a specific document) and passes them to Gemini to generate a grounded answer

4\. Answers include the source document(s) used to generate them



\## Tech stack



\*\*Backend\*\*

\- FastAPI — REST API serving upload and query endpoints

\- ChromaDB — local vector database for storing document embeddings

\- Google Gemini API — `gemini-embedding-001` for embeddings, `gemini-2.5-flash` for answer generation

\- pypdf — PDF text extraction



\*\*Frontend\*\*

\- React (Vite)

\- Vanilla CSS with a custom design system



\*\*Deployment\*\*

\- Backend hosted on Render

\- Frontend hosted on Vercel



\## Architecture

