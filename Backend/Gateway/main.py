"""
arXiv RAG Gateway — FastAPI backend
Swagger UI: /docs  (works behind Nuvolos proxy via ROOT_PATH env var)
"""

import ast
import os
import sys
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Make Backend/core importable
sys.path.insert(0, str(Path(__file__).parent.parent))
from core import embedder, retriever, generator, pdf


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------
class SearchRequest(BaseModel):
    query:   str = Field(..., min_length=1, max_length=1000)
    top_k:   int = Field(default=10, ge=1, le=50)
    sort_by: str = Field(default="relevance")


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
    paper_ids: List[str] = Field(..., min_length=1, max_length=20)
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


class ChatResponse(BaseModel):
    session_id: str
    answer:     str
    papers:     List[Paper]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _to_paper(entry: dict) -> Paper:
    published = entry.get("published", "")
    year = None
    if published:
        try:
            year = int(str(published)[:4])
        except (ValueError, IndexError):
            pass

    authors_raw = entry.get("authors", "")
    authors = []
    if authors_raw:
        try:
            parsed = ast.literal_eval(str(authors_raw))
            if isinstance(parsed, list):
                authors = [str(a) for a in parsed]
        except Exception:
            authors = [str(authors_raw)]

    return Paper(
        id=str(entry.get("idx", "")),
        title=entry.get("title", ""),
        abstract=entry.get("abstract", ""),
        authors=authors or None,
        year=year,
        terms=retriever._parse_terms(entry.get("categories", "")),
        abs_url=entry.get("entry_id") or None,
        pdf_url=entry.get("pdf_url") or None,
    )


def _format_citation(paper: Paper, style: str) -> str:
    title   = paper.title or "Unknown Title"
    authors = " and ".join(paper.authors) if paper.authors else "Unknown Author"
    year    = paper.year or "n.d."
    pid     = paper.id or "unknown"

    if style == "bibtex":
        first = (paper.authors[0].split()[-1] if paper.authors else "unknown").lower()
        return (
            f"@article{{{first}{year}{pid},\n"
            f"  title  = {{{title}}},\n"
            f"  author = {{{authors}}},\n"
            f"  year   = {{{year}}},\n"
            f"  url    = {{https://arxiv.org/abs/{pid}}}\n}}"
        )
    if style == "apa":
        return f"{authors} ({year}). {title}. arXiv. https://arxiv.org/abs/{pid}"
    if style == "mla":
        return f'{authors}. "{title}." arXiv, {year}, arxiv.org/abs/{pid}.'
    if style == "chicago":
        return f'{authors}. "{title}." arXiv ({year}). https://arxiv.org/abs/{pid}.'
    return f"{authors}. {title}. arXiv [{year}]. https://arxiv.org/abs/{pid}"


# ---------------------------------------------------------------------------
# Session store (in-process, resets on restart)
# ---------------------------------------------------------------------------
SESSIONS: dict = {}


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    embedder.load()
    retriever.load()
    yield
    print("Shutting down.")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="arXiv Semantic Research Assistant API",
    description="RAG-based API for semantic search and Q&A over arXiv academic papers.",
    version="0.2.0",
    lifespan=lifespan,
    root_path=os.environ.get("ROOT_PATH", ""),
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r"https://.*\.app\.az\.nuvolos\.cloud",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok", "index_size": retriever.index_size(), "meta_size": retriever.meta_size()}


@app.post("/search", response_model=SearchResponse)
def search_papers(req: SearchRequest):
    results_raw = retriever.search(req.query, req.top_k)

    if req.sort_by == "year":
        results_raw.sort(key=lambda r: r.get("year", 0), reverse=True)

    results = [
        SearchResult(paper=_to_paper(r), score=r["score"], rank=i + 1)
        for i, r in enumerate(results_raw)
    ]
    return SearchResponse(query=req.query, results=results, total=len(results))


@app.post("/search/upload", response_model=SearchResponse)
async def search_by_pdf(
    file:    UploadFile = File(...),
    top_k:   int        = Form(default=10),
    sort_by: str        = Form(default="relevance"),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    query = pdf.to_query(await file.read())
    if not query:
        raise HTTPException(status_code=400, detail="Could not extract text from the PDF.")

    results_raw = retriever.search(query, top_k)
    results = [
        SearchResult(
            paper=_to_paper(r),
            score=r["score"],
            rank=i + 1,
            justification=f"Semantically similar to the uploaded document (score: {r['score']:.3f}).",
        )
        for i, r in enumerate(results_raw)
    ]
    return SearchResponse(query="[PDF upload]", results=results, total=len(results))


@app.post("/qa", response_model=QAResponse)
def ask_question(req: QARequest):
    if not generator.load():
        raise HTTPException(status_code=503, detail="LLM not available.")

    retrieved = retriever.search(req.question, top_k=max(len(req.paper_ids), 5))
    prompt    = generator.build_prompt(req.question, retrieved)
    answer    = generator.generate(prompt)

    sources = [
        PassageCitation(paper=_to_paper(r), passage=r.get("summary", "")[:300], score=r["score"])
        for r in retrieved
    ]
    return QAResponse(question=req.question, answer=answer, sources=sources, model=req.model)


@app.get("/papers/{arxiv_id}", response_model=PaperDetail)
def get_paper(arxiv_id: str, citation_style: Optional[str] = Query(default=None)):
    try:
        entry = retriever.get_by_index(int(arxiv_id))
    except (ValueError, IndexError):
        raise HTTPException(status_code=404, detail=f"Paper '{arxiv_id}' not found.")

    paper    = _to_paper(entry)
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
    top_k:    int = Query(default=5, ge=1, le=20),
    sort_by:  str = Query(default="relevance"),
):
    try:
        entry = retriever.get_by_index(int(arxiv_id))
    except (ValueError, IndexError):
        raise HTTPException(status_code=404, detail=f"Paper '{arxiv_id}' not found.")

    idx_val     = entry["idx"]
    query       = f"{entry['title']} {entry.get('summary', '')[:500]}"
    results_raw = [r for r in retriever.search(query, top_k + 1) if r.get("idx") != idx_val][:top_k]

    results = [
        SearchResult(paper=_to_paper(r), score=r["score"], rank=i + 1)
        for i, r in enumerate(results_raw)
    ]
    return SearchResponse(query=query[:100], results=results, total=len(results))


@app.post("/chat", response_model=ChatResponse)
async def chat(
    message:    str                   = Form(...),
    top_k:      int                   = Form(5),
    session_id: Optional[str]         = Form(None),
    file:       Optional[UploadFile]  = File(None),
):
    """
    Multi-turn chat with session memory.
    Omit session_id (or send null) on the first turn; include the returned
    session_id on every subsequent turn to keep conversation context.
    An optional PDF attached here is injected as context for that turn only.
    """
    if not generator.load():
        raise HTTPException(status_code=503, detail="LLM not available.")

    sid = session_id or str(uuid.uuid4())
    if sid not in SESSIONS:
        SESSIONS[sid] = []
    history = SESSIONS[sid]

    pdf_context = ""
    if file is not None:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are accepted.")
        pdf_context = pdf.to_query(await file.read(), max_chars=3000)

    last_assistant = history[-1]["content"] if len(history) >= 2 else ""
    retrieval_query = f"{last_assistant} {message}".strip() if last_assistant else message

    retrieved = retriever.search(retrieval_query, top_k)

    context_blocks = []
    for i, r in enumerate(retrieved, 1):
        abstract = r.get("summary", r.get("abstract", ""))[:500]
        context_blocks.append(
            f"[Paper {i}] {r['title']}\n"
            f"Authors  : {r.get('authors', 'N/A')}\n"
            f"Published: {r.get('published', 'N/A')}\n"
            f"Category : {r.get('terms', r.get('categories', 'N/A'))}\n"
            f"Abstract : {abstract}"
        )
    if pdf_context:
        context_blocks.append(f"[Attached PDF]\n{pdf_context[:2000]}")

    system_content = (
        "You are a helpful scientific assistant. "
        "Answer the user's question using the retrieved papers below. "
        "Reference ALL retrieved papers in your answer, citing each as [Paper N]."
        + (" Refer to the attached PDF as [Attached PDF]." if pdf_context else "")
        + "\n\n=== RETRIEVED PAPERS ===\n"
        + "\n\n".join(context_blocks)
    )

    user_content = (
        f"[PDF attached — {len(pdf_context)} chars]\n\n{message}" if pdf_context else message
    )

    messages = [{"role": "system", "content": system_content}]
    messages += history
    messages.append({"role": "user", "content": user_content})

    answer = generator.generate_chat(messages)

    history.append({"role": "user",      "content": user_content})
    history.append({"role": "assistant", "content": answer})
    SESSIONS[sid] = history[-20:]

    papers = [_to_paper(r) for r in retrieved]
    return ChatResponse(session_id=sid, answer=answer, papers=papers)


@app.delete("/chat/{session_id}")
def clear_session(session_id: str):
    """Clear the conversation history for a given session."""
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found.")
    del SESSIONS[session_id]
    return {"status": "cleared", "session_id": session_id}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
