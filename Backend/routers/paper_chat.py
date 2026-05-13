"""
POST  /paper/start          → create session + auto-generated opening message
POST  /paper/chat           → subsequent turns about that paper
DELETE /paper/chat/{id}     → clear session
"""

import sys
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent))
from core import retriever, generator, pdf

router = APIRouter(tags=["Paper Chat"])

PAPER_SESSIONS: dict[str, dict] = {}


# ── Schemas ───────────────────────────────────────────────────────────────────

class PaperStartResponse(BaseModel):
    session_id     : str
    opening_message: str
    paper          : dict


class PaperChatResponse(BaseModel):
    session_id: str
    answer    : str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _find_paper(entry_id: str) -> Optional[dict]:
    try:
        return retriever.get_by_index(int(entry_id))
    except (ValueError, IndexError):
        return None


def _build_paper_system_prompt(paper: dict, pdf_context: str = "") -> str:
    arxiv_url = paper.get("entry_id", "")
    if arxiv_url and "arxiv.org" not in arxiv_url:
        arxiv_url = f"https://arxiv.org/abs/{arxiv_url}"

    lines = [
        "You are a helpful scientific assistant specialising in a single paper.",
        "Answer ONLY based on the information about this paper provided below.",
        "If the user asks about something not covered by the abstract, say so honestly.",
        "Always be specific and cite the paper by its title.",
        "",
        "=== PAPER ===",
        f"Title    : {paper.get('title', 'N/A')}",
        f"Authors  : {paper.get('authors', 'N/A')}",
        f"Published: {paper.get('published', 'N/A')}",
        f"Category : {paper.get('primary_category', paper.get('terms', 'N/A'))}",
        f"URL      : {arxiv_url}",
        f"Abstract : {paper.get('abstract', paper.get('summary', 'N/A'))}",
    ]

    if pdf_context:
        lines += ["", "=== FULL TEXT EXCERPT (from uploaded PDF) ===", pdf_context]

    return "\n".join(lines)


def _generate_opening_message(paper: dict) -> str:
    arxiv_url = paper.get("entry_id", "")
    if arxiv_url and "arxiv.org" not in arxiv_url:
        arxiv_url = f"https://arxiv.org/abs/{arxiv_url}"

    system = _build_paper_system_prompt(paper)

    intro_prompt = (
        "Please introduce this paper to the user in 3-4 sentences. Cover: "
        "(1) what problem it addresses, (2) the core method or contribution, "
        "(3) the main result or finding. "
        f"End with: 'You can read the full paper here: {arxiv_url}' "
        "Then invite the user to ask questions."
    )

    messages = [
        {"role": "system", "content": system},
        {"role": "user",   "content": intro_prompt},
    ]
    return generator.generate_chat(messages)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/paper/start", response_model=PaperStartResponse)
async def paper_start(
    entry_id: str                    = Form(..., description="Numeric row ID of the paper from search results"),
    pdf      : Optional[UploadFile]  = File(None, description="Optional PDF for richer context"),
):
    paper = _find_paper(entry_id)
    if paper is None:
        raise HTTPException(status_code=404, detail=f"Paper '{entry_id}' not found.")

    pdf_context = ""
    if pdf is not None:
        raw         = await pdf.read()
        pdf_context = pdf.extract_pdf_text(raw, max_chars=4000)

    opening = _generate_opening_message(paper)

    sid = str(uuid.uuid4())
    PAPER_SESSIONS[sid] = {
        "paper"      : paper,
        "pdf_context": pdf_context,
        "history"    : [{"role": "assistant", "content": opening}],
    }

    return PaperStartResponse(session_id=sid, opening_message=opening, paper=paper)


@router.post("/paper/chat", response_model=PaperChatResponse)
async def paper_chat(
    session_id: str                   = Form(...),
    message   : str                   = Form(...),
    pdf       : Optional[UploadFile]  = File(None),
):
    if session_id not in PAPER_SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found. Call /paper/start first.")

    session = PAPER_SESSIONS[session_id]
    paper   = session["paper"]
    history = session["history"]

    pdf_context = session.get("pdf_context", "")
    if pdf is not None:
        raw         = await pdf.read()
        pdf_context = pdf.extract_pdf_text(raw, max_chars=4000)
        session["pdf_context"] = pdf_context

    system = _build_paper_system_prompt(paper, pdf_context=pdf_context)

    messages = [{"role": "system", "content": system}]
    messages += history[-18:]
    messages.append({"role": "user", "content": message})

    answer = generator.generate_chat(messages)

    history.append({"role": "user",      "content": message})
    history.append({"role": "assistant", "content": answer})
    session["history"] = history[-20:]

    return PaperChatResponse(session_id=session_id, answer=answer)


@router.delete("/paper/chat/{session_id}")
async def clear_paper_session(session_id: str):
    if session_id not in PAPER_SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found.")
    del PAPER_SESSIONS[session_id]
    return {"status": "cleared", "session_id": session_id}