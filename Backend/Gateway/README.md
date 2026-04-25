# arXiv RAG — Backend Gateway

FastAPI backend for the arXiv Semantic Research Assistant.
Exposes a REST API for semantic search and Q&A over arXiv papers, backed by FAISS + sentence-transformers + a local LLM.

Swagger UI is available at `/docs` once the server is running.

---

## Prerequisites

- Python 3.10+
- The FAISS index and metadata must exist at `Backend/arxiv.faiss` and `Backend/arxiv_meta.json`

Install dependencies into the virtual environment (only needed once):

```bash
cd Backend/Gateway
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## Running locally

```bash
cd Backend/Gateway
./start.sh
```

Swagger UI → [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Running on Nuvolos

Nuvolos proxies container ports through a public URL.
Port `8000` inside the container is reachable at `/proxy/8000/` on your instance URL.

### 1. Start the backend

```bash
cd Backend/Gateway
ROOT_PATH=/proxy/8000 ./start.sh
```

> `ROOT_PATH` tells FastAPI it is mounted at `/proxy/8000/` rather than `/`.
> This is required for Swagger UI to generate correct API call URLs through the proxy.

Swagger UI → `https://<backend-hash>.app.az.nuvolos.cloud/proxy/8000/docs`

### 2. Build and serve the frontend

The frontend must be rebuilt with the backend URL hardcoded into the bundle.
Replace `<backend-hash>` with your actual Nuvolos backend instance hash.

```bash
cd Frontend/RAG-frontend

VITE_API_URL=https://<backend-hash>.app.az.nuvolos.cloud/proxy/8000 \
  npm run build -- --base=/proxy/3000/

python3 -m http.server 3000 --directory dist
```

Frontend → `https://<frontend-hash>.app.az.nuvolos.cloud/proxy/3000/`

> The frontend and backend run on **separate Nuvolos instances** with different hashes.
> CORS is open on the backend so cross-origin requests from the frontend work out of the box.

---

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check — returns index size |
| `POST` | `/search` | Semantic paper search via FAISS |
| `POST` | `/search/upload` | Search by PDF upload |
| `POST` | `/qa` | Question answering with local LLM |
| `GET` | `/papers/{id}` | Paper metadata + citation export |
| `GET` | `/papers/{id}/similar` | Find similar papers |

Full schema available in `../API/openapi.yaml` and interactively at `/docs`.

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ROOT_PATH` | *(empty)* | Proxy prefix, e.g. `/proxy/8000` on Nuvolos |
| `PORT` | `8000` | Port to listen on |
| `HOST` | `0.0.0.0` | Host to bind to |
