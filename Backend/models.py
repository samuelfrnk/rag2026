import torch
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForCausalLM
from config import CFG, DEVICE

APP_STATE = {}

def load_embed_model():
    print("Loading embedding model...")
    model = SentenceTransformer(CFG['embed_model'], device=DEVICE)
    print(f"[startup] Embedding model loaded on {DEVICE}")
    print(f"[startup] Embedding dim: {model.get_sentence_embedding_dimension()}")
    return model

def load_llm():
    model_id = CFG['llm_model']
    print(f"Loading LLM model {model_id}...")
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    load_kwargs: dict = {
        "torch_dtype": torch.float16 if DEVICE in ("mps", "cuda") else torch.float32
    }
    
    if DEVICE in ("mps", "cuda"):
        load_kwargs["device_map"] = "auto"
    if CFG.get("llm_load_in_4bit") and DEVICE in ("mps", "cuda"):
        
        from transformers import BitsAndBytesConfig
        load_kwargs["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True)
        load_kwargs.pop("torch_dtype", None)
        
    model = AutoModelForCausalLM.from_pretrained(model_id, **load_kwargs)
    if DEVICE == "cpu":
        model = model.to(DEVICE)
        
    model.eval()
    print(f"[startup] LLM model loaded on {DEVICE}")
    return tokenizer, model


@asynccontextmanager
async def lifespan(app: FastAPI):
    from index import load_index
    
    APP_STATE['embed_model'] = load_embed_model()
    APP_STATE["index"], APP_STATE["meta"] = load_index()
    APP_STATE['tokenizer'], APP_STATE['llm'] = load_llm()
    
    print(f"[startup] Application startup complete. Ready to serve requests.")
    yield
    APP_STATE.clear()
    print(f"[shutdown] Application shutdown complete. Resources cleared.")