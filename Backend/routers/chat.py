import uuid
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile

from index    import retrieve
from pdf      import extract_pdf_text
from pipeline import generate_chat_answer
from schemas  import ChatRequest, ChatResponse, Paper

router = APIRouter(tags=["Chat"])
SESSIONS: dict[str, list[dict]] = {}


@router.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    pdf: Optional[UploadFile] = File(None, description="Optional PDF to attach to this turn"),
):
    """
    Send session_id=null on the first turn.
    Pass the returned session_id on every subsequent turn to keep context.
    A PDF attached here is injected as context for this turn only.
    """
    sid = req.session_id or str(uuid.uuid4())
    if sid not in SESSIONS:
        SESSIONS[sid] = []
    history = SESSIONS[sid]

    pdf_context = ""
    if pdf is not None:
        raw         = await pdf.read()
        pdf_context = extract_pdf_text(raw, max_chars=3000)

    retrieval_query = (
        f"{pdf_context[:500]} {req.message}".strip() if pdf_context else req.message
    )
    retrieved = retrieve(retrieval_query, top_k=req.top_k)

    context_blocks = []
    for i, r in enumerate(retrieved, 1):
        context_blocks.append(
            f"[Paper {i}] {r['title']}\n"
            f"Authors  : {r.get('authors', 'N/A')}\n"
            f"Published: {r.get('published', 'N/A')}\n"
            f"Category : {r.get('primary_category', r.get('categories', 'N/A'))}\n"
            f"Abstract : {r.get('abstract', '')[:500]}"
        )
    if pdf_context:
        context_blocks.append(f"[Attached PDF]\n{pdf_context[:2000]}")

    system_content = (
        "You are a helpful scientific assistant. "
        "Answer the user's question using the retrieved papers below. "
        "Cite papers by number, e.g. [Paper 1]."
        + (" Refer to the attached PDF as [Attached PDF]." if pdf_context else "")
        + "\n\n=== RETRIEVED PAPERS ===\n"
        + "\n\n".join(context_blocks)
    )

    user_content = (
        f"[PDF attached — {len(pdf_context)} chars]\n\n{req.message}"
        if pdf_context else req.message
    )

    messages = [{"role": "system", "content": system_content}]
    messages += history
    messages.append({"role": "user", "content": user_content})

    answer = generate_chat_answer(messages)

    history.append({"role": "user",      "content": user_content})
    history.append({"role": "assistant", "content": answer})
    SESSIONS[sid] = history[-20:]

    papers = [
        Paper(
            title            = r["title"],
            abstract         = r.get("abstract", ""),
            categories       = r.get("categories", ""),
            primary_category = r.get("primary_category", ""),
            authors          = r.get("authors", ""),
            pdf_url          = r.get("pdf_url", ""),
            published        = r.get("published", ""),
            entry_id         = r.get("entry_id", ""),
            score            = r["score"],
        )
        for r in retrieved
    ]

    return ChatResponse(session_id=sid, answer=answer, papers=papers)


@router.delete("/chat/{session_id}")
def clear_session(session_id: str):
    """Clear the conversation history for a given session."""
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found.")
    del SESSIONS[session_id]
    return {"status": "cleared", "session_id": session_id}