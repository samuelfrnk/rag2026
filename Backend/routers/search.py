from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from index import retrieve
from pdf import extract_pdf_text
from schemas import Paper, SearchResponse

router = APIRouter(tags=["Search"])

@router.post("/search", response_model=SearchResponse)
async def search(
    keywords = Form(..., description="Search keywords or query string"),
    context_text = Form(None, description="Optional context text to enhance search relevance"),
    top_k = Form(5, description="Number of top relevant papers to retrieve"),
    pdf = File(None, description="Optional PDF file to extract text and enhance search relevance")
):
    parts = [keywords.strip()]
    
    if context_text and context_text.strip():
        parts.append(context_text.strip())
        
    pdf_context = ""
    if pdf is not None:
        raw = await pdf.read()
        pdf_context = extract_pdf_text(raw, max_chars = 3000)
        parts.append(pdf_context[:500])
        
    retrieval_query = " ".join(parts)
    
    
    retrieved = retrieve(retrieval_query, top_k = top_k)
    if not retrieved:
        raise HTTPException(status_code=404, detail="No relevant papers found.")
    
    prompt = build_prompt(retrieval_query, retrieved, pdf_context = pdf_context)
    answer = generate_answer(prompt)
    
    papers = [
        Paper(
            title = r['title'],
            abstract = r.get('abstract'),
            categories = r.get('categories'),
            primary_category = r.get('primary_category'),
            authors = r.get('authors'),
            pdf_url = r.get('pdf_url'),
            published = r.get('published'),
            entry_id = r.get('entry_id'),
            score = r.get('score')
        )
        for r in retrieved
    ]
    
    return SearchResponse(query=retrieval_query, answer=answer, papers=papers)