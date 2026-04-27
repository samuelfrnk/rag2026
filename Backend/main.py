from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import lifespan
from routers import chat, search
from config import DEVICE


app = FastAPI(
    title = "arXiv RAG",
    version = "1.0.0",
    description = "A Retrieval-Augmented Generation (RAG) system for arXiv papers.",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router)
app.include_router(chat.router)

@app.get("/health", tags=["Meta"])
def health():
    return {"status": "ok", "device": DEVICE}