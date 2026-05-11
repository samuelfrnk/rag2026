"""
POST  /paper/start          → create session + auto-generated opening message
POST  /paper/chat           → subsequent turns about that paper
DELETE /paper/chat/{id}     → clear session
"""

import uuid
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from models import APP_STATE
from pipeline import generate_chat_answer
from pdf import extract_pdf_text
from config import CFG

router = APIRouter(tags = ["Paper Chat"])

PAPER_SESSION: dict[str, dict] = {}

class PaperStartResponse(BaseModel):
    session_id: str
    opening_message: str
    paper: dict
    
class PaperChatResponse(BaseModel):
    session_id: str
    answer: str
    
def _find_paper(entry_id):
    meta = APP_STATE["metadata"]
    for paper in meta:
        if paper.get("entry_id", "") == entry_id:
            return paper
    
    for paper in meta:
        if entry_id in paper.get("entry_id", "") or paper.get("entry_id", "") in entry_id:
            return paper
    return None

def _build_paper_system_prompt(paper, pdf_context = ""):
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
        f"Category : {paper.get('primary_category', paper.get('categories', 'N/A'))}",
        f"URL      : {arxiv_url}",
        f"Abstract : {paper.get('abstract', 'N/A')}",
    ]

    if pdf_context:
        lines += ["", "=== FULL TEXT EXCERPT (from uploaded PDF) ===", pdf_context]

    return "\n".join(lines)

def _generate_opening_message(paper: dict) -> str:
    """
    Ask the LLM to introduce the paper in a friendly, informative way.
    This becomes the first message the user sees in the chatbot.
    """
    arxiv_url = paper.get("entry_id", "")
    if arxiv_url and "arxiv.org" not in arxiv_url:
        arxiv_url = f"https://arxiv.org/abs/{arxiv_url}"

    system = _build_paper_system_prompt(paper)

    intro_prompt = (
        f"Please introduce this paper to the user in 3–4 sentences. Cover: "
        f"(1) what problem it addresses, (2) the core method or contribution, "
        f"(3) the main result or finding. "
        f"End with: 'You can read the full paper here: {arxiv_url}' "
        f"Then invite the user to ask questions."
    )

    messages = [
        {"role": "system",    "content": system},
        {"role": "user",      "content": intro_prompt},
    ]
    return generate_chat_answer(messages)

@router.post("/paper/start", response_model=PaperStartResponse)
async def paper_start(
    entry_id = Form(..., description="The arXiv ID or URL of the paper to discuss"),
    pdf = File(None, description="Optional PDF file of the paper to extract additional context from")
):
    paper = _find_paper(entry_id)
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found in metadata")
    
    pdf_context = ""
    if pdf is not None:
        raw = await pdf.read()
        pdf_context = extract_pdf_text(raw, max_chars=4000)
        
    opening = _generate_opening_message(paper)
    
    sid = str(uuid.uuid4())
    PAPER_SESSION[sid] = {
        "paper": paper,
        "pdf_context": pdf_context,
        "history": [{"role": "assistant", "content": opening}]
    }
    
    return PaperStartResponse(session_id=sid, opening_message=opening, paper=paper)

@router.post("/paper/chat", response_model=PaperChatResponse)
async def paper_chat(
    session_id = Form(...),
    message = Form(...),
    pdf = File(None, description="Optional PDF file of the paper to extract additional context from")
):
    if session_id not in PAPER_SESSION:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = PAPER_SESSION[session_id]
    paper = session["paper"]
    history = session["history"]
    
    pdf_context = session.get("pdf_context", "")
    if pdf is not None:
        raw = await pdf.read()
        pdf_context = extract_pdf_text(raw, max_chars=4000)
        session["pdf_context"] = pdf_context
        
    system = _build_paper_system_prompt(paper, pdf_context=pdf_context)
    
    messages = [{"role": "system", "content": system}]
    messages += history[-18:]
    
    messages.append({"role": "user", "content": message})
    answer = generate_chat_answer(messages)
    
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": answer})
    session["history"] = history[-20:]
    
    return PaperChatResponse(session_id=session_id, answer=answer)

@router.delete("/paper/chat/{session_id}")
async def paper_chat_delete(session_id: str):
    if session_id not in PAPER_SESSION:
        raise HTTPException(status_code=404, detail="Session not found.")
    del PAPER_SESSION[session_id]
    return {"status": "cleared", "session_id": session_id}
