"""
Embedding model — loads sentence-transformers and embeds text into vectors.
Source: proof_of_concept.ipynb → load_embed_model(), embed_texts()
"""

import numpy as np
from sentence_transformers import SentenceTransformer
from config import CFG

MODEL_NAME = CFG["embed_model"]

_model: SentenceTransformer | None = None


def load() -> None:
    """Load the sentence-transformer model into memory."""
    global _model
    print(f"Loading embedding model: {MODEL_NAME} ...")
    _model = SentenceTransformer(MODEL_NAME)
    #print(f"Embedding model ready (dim={_model.get_sentence_embedding_dimension()}).")
    print(f"Embedding model ready (dim={_model.get_embedding_dimension()}).") #BAAI


def embed(text: str) -> np.ndarray:
    """Embed a single string, return a normalised float32 vector (shape: [1, 384])."""
    if _model is None:
        raise RuntimeError("Embedder not loaded. Call embedder.load() first.")
    emb = _model.encode([text], convert_to_numpy=True)
    emb = emb / (np.linalg.norm(emb, axis=1, keepdims=True) + 1e-10)
    return emb.astype(np.float32)
