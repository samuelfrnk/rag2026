# arXiv Semantic Research Assistant

A RAG-based (Retrieval-Augmented Generation) web application for semantic search and Q&A over arXiv academic papers.

Users can search for papers using keywords or free text, browse results ranked by semantic similarity, and chat with an LLM that answers questions grounded in the retrieved papers.

---

## Architecture

```
Frontend (React + Vite)
    └── served by FastAPI as static files
Backend (FastAPI)
    ├── core/embedder.py     — sentence-transformers (all-MiniLM-L6-v2)
    ├── core/retriever.py    — FAISS vector index + metadata
    └── core/generator.py    — local LLM (Qwen2.5)
```

The frontend and backend run on the same server instance. The frontend calls the API on the same origin — no CORS required.

---

## Project structure

```
rag2026/
├── Backend/
│   ├── core/
│   │   ├── embedder.py      — loads sentence-transformer, embeds queries
│   │   ├── retriever.py     — loads FAISS index, searches for similar papers
│   │   ├── generator.py     — loads LLM, builds prompts, generates answers
│   │   └── pdf.py           — PDF text extraction for upload-based search
│   ├── Gateway/
│   │   ├── main.py          — FastAPI app (all routes + static file serving)
│   │   ├── start.sh         — startup script
│   │   ├── requirements.txt
│   │   └── dist/            — built frontend (copied here before starting)
│   ├── build_index.py       — one-time script to build FAISS index from CSV
│   └── config.py            — paths, model names, dataset config
├── Frontend/
│   └── RAG-frontend/        — React + Vite app
│       └── src/
│           ├── pages/       — Home, Results, IndvPaper
│           ├── components/  — SearchForm, ResultCard, Chatbot, SideBar, ...
│           ├── services/
│           │   └── api.jsx  — fetch wrappers for /search and /chat
│           └── config/
│               └── config.js — API base URL (set via VITE_API_URL)
├── Data/
│   ├── scraper/             — arXiv scraping scripts
│   └── datasets/            — scraped CSV files by category
└── arxiv_data_30_04_sz_2000.csv — main dataset (tracked via Git LFS)
```

---

## Prerequisites

- Python 3.10+
- Node.js 20+
- A pre-built FAISS index (`arxiv.faiss` + `arxiv_meta.json`) — see below

---

## Building the FAISS index (once)

Before running the backend for the first time, build the vector index from the dataset:

```bash
cd Backend
python build_index.py
```

This reads the CSV defined in `config.py` (`data_path`) and writes the index to `index_path` and `meta_path`. On Nuvolos these default to `/files/tmp/`.

Only re-run if you change the dataset or the embedding model.

---

## Running locally

**1. Backend**

```bash
cd Backend/Gateway
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./start.sh
```

**2. Frontend (dev server)**

```bash
cd Frontend/RAG-frontend
npm install
npm run dev
```

Frontend dev server → [http://localhost:5173](http://localhost:5173)
API + Swagger UI → [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Running on Nuvolos

The frontend is built into a static bundle and served directly by FastAPI — both run on the **same backend instance** on port 8000.

### 1. Build the frontend

```bash
cd Frontend/RAG-frontend
VITE_API_URL=/proxy/8000 npm run build -- --base=/proxy/8000/
cp -r dist /files/rag2026/Backend/Gateway/dist
```

### 2. Start the backend

```bash
cd /files/rag2026/Backend/Gateway
ROOT_PATH=/proxy/8000 ./start.sh
```

| URL | Description |
|-----|-------------|
| `https://<hash>.app.az.nuvolos.cloud/proxy/8000/` | Frontend |
| `https://<hash>.app.az.nuvolos.cloud/proxy/8000/docs` | Swagger UI |

> `ROOT_PATH` tells FastAPI it is mounted at `/proxy/8000/` through the Nuvolos proxy.

---

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check — returns index and metadata size |
| `POST` | `/search` | Semantic paper search via FAISS |
| `POST` | `/search/upload` | Search by PDF upload |
| `POST` | `/qa` | Question answering with local LLM |
| `GET` | `/papers/{id}` | Paper metadata + optional citation export |
| `GET` | `/papers/{id}/similar` | Find semantically similar papers |
| `POST` | `/chat` | Multi-turn RAG chat with session memory |
| `DELETE` | `/chat/{session_id}` | Clear a chat session |

Full interactive schema at `/docs`.

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ROOT_PATH` | *(empty)* | Proxy prefix, e.g. `/proxy/8000` on Nuvolos |
| `PORT` | `8000` | Port to listen on |
| `HOST` | `0.0.0.0` | Host to bind to |
| `VITE_API_URL` | `http://localhost:8000` | Backend URL baked into the frontend bundle |
