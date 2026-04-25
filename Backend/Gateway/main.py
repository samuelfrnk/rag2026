"""
arXiv RAG Gateway — FastAPI backend
Swagger UI: /docs  (works behind Nuvolos proxy via ROOT_PATH env var)
"""

import ast
import io
import json
import os
import re
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional

import numpy as np
import faiss
import pymupdf as fitz
import torch
from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# Paths (relative to this file)
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.parent          # /Backend/
INDEX_PATH = BASE_DIR / "arxiv.faiss"
META_PATH  = BASE_DIR / "arxiv_meta.json"
EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL_NAME   = "Qwen/Qwen2.5-3B-Instruct"   # loaded lazily

# ---------------------------------------------------------------------------
# Globals populated on startup
# ---------------------------------------------------------------------------
index: Optional[faiss.Index] = None
meta:  Optional[list]        = None
embed_model: Optional[SentenceTransformer] = None
llm_tokenizer = None
llm_model_obj = None


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------
class SearchFilters(BaseModel):
    year_from: Optional[int] = None
    year_to:   Optional[int] = None
    categories: Optional[List[str]] = None


class SearchRequest(BaseModel):
    query:   str          = Field(..., min_length=1, max_length=1000)
    top_k:   int          = Field(default=10, ge=1, le=50)
    sort_by: str          = Field(default="relevance")
    filters: Optional[SearchFilters] = None


class Paper(BaseModel):
    id:       Optional[str]       = None
    title:    str
    abstract: Optional[str]       = None
    authors:  Optional[List[str]] = None
    year:     Optional[int]       = None
    terms:    Optional[List[str]] = None
    abs_url:  Optional[str]       = None
    pdf_url:  Optional[str]       = None


class SearchResult(BaseModel):
    paper:            Paper
    score:            float
    rank:             int
    abstract_summary: Optional[str] = None
    justification:    Optional[str] = None


class SearchResponse(BaseModel):
    query:   str
    results: List[SearchResult]
    total:   int


class QARequest(BaseModel):
    question:  str       = Field(..., min_length=1, max_length=2000)
    paper_ids: List[str] = Field(..., min_items=1, max_items=20)
    model:     str       = Field(default="qwen-4b")


class PassageCitation(BaseModel):
    paper:   Paper
    section: Optional[str] = None
    passage: str
    score:   float


class QAResponse(BaseModel):
    question: str
    answer:   str
    sources:  List[PassageCitation]
    model:    str


class PaperDetail(Paper):
    citation: Optional[dict] = None


class ErrorResponse(BaseModel):
    error:  str
    detail: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _parse_terms(raw: str) -> List[str]:
    """Turn the stored string "['cs.CV', 'cs.LG']" into a Python list."""
    if not raw:
        return []
    try:
        parsed = ast.literal_eval(raw)
        if isinstance(parsed, list):
            return [str(t) for t in parsed]
    except Exception:
        pass
    # Fallback: strip brackets and split on commas
    cleaned = re.sub(r"[\[\]'\"]", "", raw)
    return [t.strip() for t in cleaned.split(",") if t.strip()]


def _meta_to_paper(entry: dict) -> Paper:
    return Paper(
        id=str(entry.get("idx", "")),
        title=entry.get("title", ""),
        abstract=entry.get("summary", ""),
        terms=_parse_terms(entry.get("terms", "")),
    )


def _embed_query(query: str) -> np.ndarray:
    emb = embed_model.encode([query], convert_to_numpy=True)
    emb = emb / (np.linalg.norm(emb, axis=1, keepdims=True) + 1e-10)
    return emb.astype(np.float32)


def _retrieve(query: str, top_k: int, filters: Optional[SearchFilters] = None) -> List[dict]:
    """Embed query, search FAISS, apply optional category filter, return results."""
    q_emb = _embed_query(query)
    # Over-fetch to account for category filtering
    fetch_k = min(top_k * 10 if filters and filters.categories else top_k, index.ntotal)
    scores, ids = index.search(q_emb, fetch_k)

    results = []
    for score, idx_val in zip(scores[0], ids[0]):
        if idx_val == -1:
            continue
        entry = meta[idx_val].copy()
        entry["score"] = float(score)

        # Category filter
        if filters and filters.categories:
            terms = _parse_terms(entry.get("terms", ""))
            if not any(cat in terms for cat in filters.categories):
                continue

        results.append(entry)
        if len(results) >= top_k:
            break

    return results


def _format_citation(paper: Paper, style: str) -> str:
    title   = paper.title or "Unknown Title"
    authors = " and ".join(paper.authors) if paper.authors else "Unknown Author"
    year    = paper.year or "n.d."
    pid     = paper.id or "unknown"

    if style == "bibtex":
        first_author = (paper.authors[0].split()[-1] if paper.authors else "Unknown").lower()
        key = f"{first_author}{year}{pid}"
        return (
            f"@article{{{key},\n"
            f"  title  = {{{title}}},\n"
            f"  author = {{{authors}}},\n"
            f"  year   = {{{year}}},\n"
            f"  url    = {{https://arxiv.org/abs/{pid}}}\n"
            f"}}"
        )
    if style == "apa":
        return f"{authors} ({year}). {title}. arXiv. https://arxiv.org/abs/{pid}"
    if style == "mla":
        return f'{authors}. "{title}." arXiv, {year}, arxiv.org/abs/{pid}.'
    if style == "chicago":
        return f'{authors}. "{title}." arXiv ({year}). https://arxiv.org/abs/{pid}.'
    # vancouver
    return f"{authors}. {title}. arXiv [{year}]. Available from: https://arxiv.org/abs/{pid}"


def _load_llm():
    global llm_tokenizer, llm_model_obj
    if llm_model_obj is not None:
        return True
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        print(f"Loading LLM {LLM_MODEL_NAME} ...")
        device = (
            "mps" if torch.backends.mps.is_available()
            else "cuda" if torch.cuda.is_available()
            else "cpu"
        )
        llm_tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL_NAME)
        llm_model_obj = AutoModelForCausalLM.from_pretrained(
            LLM_MODEL_NAME,
            dtype=torch.float16 if device != "cpu" else torch.float32,
            device_map="auto" if device != "cpu" else None,
        )
        if device == "cpu":
            llm_model_obj = llm_model_obj.to(device)
        llm_model_obj.eval()
        print("LLM loaded.")
        return True
    except Exception as exc:
        print(f"LLM load failed: {exc}")
        return False


def _generate(prompt: str, max_new_tokens: int = 512, temperature: float = 0.7) -> str:
    device = next(llm_model_obj.parameters()).device
    try:
        messages  = [{"role": "user", "content": prompt}]
        input_ids = llm_tokenizer.apply_chat_template(
            messages, return_tensors="pt", add_generation_prompt=True
        ).to(device)
    except Exception:
        input_ids = llm_tokenizer(prompt, return_tensors="pt").input_ids.to(device)

    with torch.no_grad():
        out = llm_model_obj.generate(
            input_ids,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=temperature > 0,
            pad_token_id=llm_tokenizer.eos_token_id,
        )
    new_tokens = out[0][input_ids.shape[-1]:]
    return llm_tokenizer.decode(new_tokens, skip_special_tokens=True).strip()


# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global index, meta, embed_model
    print("Loading FAISS index and metadata...")
    index = faiss.read_index(str(INDEX_PATH))
    with open(META_PATH, "r") as f:
        meta = json.load(f)
    print(f"Index loaded: {index.ntotal} vectors | {len(meta)} papers in metadata")

    print(f"Loading embedding model: {EMBED_MODEL_NAME} ...")
    embed_model = SentenceTransformer(EMBED_MODEL_NAME)
    print("Embedding model ready.")
    yield
    print("Shutting down.")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
ROOT_PATH = os.environ.get("ROOT_PATH", "")

app = FastAPI(
    title="arXiv Semantic Research Assistant API",
    description="RAG-based API for semantic search and Q&A over arXiv academic papers.",
    version="0.2.0",
    lifespan=lifespan,
    root_path=ROOT_PATH,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "index_size": index.ntotal if index else 0,
        "meta_size": len(meta) if meta else 0,
    }


@app.post("/search", response_model=SearchResponse)
def search_papers(req: SearchRequest):
    results_raw = _retrieve(req.query, req.top_k, req.filters)

    if req.sort_by == "year":
        results_raw.sort(key=lambda r: r.get("year", 0), reverse=True)

    results = [
        SearchResult(
            paper=_meta_to_paper(r),
            score=r["score"],
            rank=i + 1,
        )
        for i, r in enumerate(results_raw)
    ]
    return SearchResponse(query=req.query, results=results, total=len(results))


@app.post("/search/upload", response_model=SearchResponse)
async def search_by_pdf(
    file: UploadFile = File(...),
    top_k: int = Form(default=10),
    sort_by: str = Form(default="relevance"),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    content = await file.read()
    doc   = fitz.open(stream=io.BytesIO(content), filetype="pdf")
    pages = [page.get_text("text") for page in doc]
    doc.close()

    text = "\n".join(pages)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    query = text[:2000].strip()

    if not query:
        raise HTTPException(status_code=400, detail="Could not extract text from the PDF.")

    results_raw = _retrieve(query, top_k)
    results = [
        SearchResult(
            paper=_meta_to_paper(r),
            score=r["score"],
            rank=i + 1,
            justification=f"Semantically similar to the uploaded document (score: {r['score']:.3f}).",
        )
        for i, r in enumerate(results_raw)
    ]
    return SearchResponse(query="[PDF upload]", results=results, total=len(results))


@app.post("/qa", response_model=QAResponse)
def ask_question(req: QARequest):
    # Retrieve by question first (ignore paper_ids for retrieval since no real arXiv IDs)
    retrieved = _retrieve(req.question, top_k=len(req.paper_ids) or 5)

    if not _load_llm():
        raise HTTPException(
            status_code=503,
            detail="LLM not available. Ensure transformers and the model are installed.",
        )

    # Build prompt
    context_blocks = []
    for i, r in enumerate(retrieved, 1):
        abstract = r.get("summary", "")[:600]
        context_blocks.append(
            f"[Paper {i}]\nTitle: {r['title']}\nTerms: {r.get('terms','N/A')}\nAbstract: {abstract}"
        )
    context = "\n\n".join(context_blocks)

    prompt = (
        "You are a helpful scientific assistant. "
        "Use ONLY the papers below to answer the question. "
        "Cite papers by number, e.g. [Paper 1]. "
        "If the answer cannot be found, say so.\n\n"
        f"=== RETRIEVED PAPERS ===\n{context}\n\n"
        f"=== QUESTION ===\n{req.question}\n\n"
        "=== ANSWER ===\n"
    )

    answer = _generate(prompt)

    sources = [
        PassageCitation(
            paper=_meta_to_paper(r),
            passage=r.get("summary", "")[:300],
            score=r["score"],
        )
        for r in retrieved
    ]

    return QAResponse(question=req.question, answer=answer, sources=sources, model=req.model)


@app.get("/papers/{arxiv_id}", response_model=PaperDetail)
def get_paper(
    arxiv_id: str,
    citation_style: Optional[str] = Query(default=None),
):
    try:
        idx_val = int(arxiv_id)
    except ValueError:
        # Try matching by partial title or just report not found
        raise HTTPException(status_code=404, detail=f"Paper '{arxiv_id}' not found.")

    if idx_val < 0 or idx_val >= len(meta):
        raise HTTPException(status_code=404, detail=f"Paper index {arxiv_id} out of range.")

    entry  = meta[idx_val]
    paper  = _meta_to_paper(entry)

    citation = None
    if citation_style:
        style = citation_style.lower()
        if style not in ("bibtex", "apa", "mla", "chicago", "vancouver"):
            raise HTTPException(status_code=422, detail=f"Unknown citation style: {style}")
        citation = {"style": style, "formatted": _format_citation(paper, style)}

    return PaperDetail(**paper.model_dump(), citation=citation)


@app.get("/papers/{arxiv_id}/similar", response_model=SearchResponse)
def get_similar_papers(
    arxiv_id: str,
    top_k: int = Query(default=5, ge=1, le=20),
    sort_by: str = Query(default="relevance"),
):
    try:
        idx_val = int(arxiv_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Paper '{arxiv_id}' not found.")

    if idx_val < 0 or idx_val >= len(meta):
        raise HTTPException(status_code=404, detail=f"Paper index {arxiv_id} out of range.")

    entry = meta[idx_val]
    query = f"{entry['title']} {entry.get('summary', '')[:500]}"

    results_raw = _retrieve(query, top_k + 1)  # +1 to exclude the paper itself
    results_raw = [r for r in results_raw if r.get("idx") != idx_val][:top_k]

    results = [
        SearchResult(paper=_meta_to_paper(r), score=r["score"], rank=i + 1)
        for i, r in enumerate(results_raw)
    ]
    return SearchResponse(query=query[:100], results=results, total=len(results))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
