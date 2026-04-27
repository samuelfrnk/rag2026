from typing import Optional
from pydantic import BaseModel, Field

class Paper(BaseModel):
    title: str
    abstract : str
    categories : str
    primary_category : str
    authors : str
    pdf_url : str
    published : str
    entry_id : str
    score : float
    
class SearchResponse(BaseModel):
    query : str
    answer : str
    papers : list[Paper]
    
class ChatRequest(BaseModel):
    session_id : Optional[str] = Field(default = None, description="Unique identifier for the chat session")
    message : str
    top_k : int = Field(default=5, description="Number of top relevant papers to retrieve")
    
class ChatResponse(BaseModel):
    session_id : str
    answer : str
    papers : list[Paper]