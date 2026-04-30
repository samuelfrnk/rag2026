"""
Embedding model — loads sentence-transformers and embeds text into vectors.
Source: proof_of_concept.ipynb → load_embed_model(), embed_texts()
"""

import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_model: SentenceTransformer | None = None


def load() -> None:
    """Load the sentence-transformer model into memory."""
    global _model
    print(f"Loading embedding model: {MODEL_NAME} ...")
    _model = SentenceTransformer(MODEL_NAME)
    print(f"Embedding model ready (dim={_model.get_sentence_embedding_dimension()}).")


def embed(text: str) -> np.ndarray:
    """Embed a single string, return a normalised float32 vector (shape: [1, 384])."""
    if _model is None:
        raise RuntimeError("Embedder not loaded. Call embedder.load() first.")
    emb = _model.encode([text], convert_to_numpy=True)
    emb = emb / (np.linalg.norm(emb, axis=1, keepdims=True) + 1e-10)
    return emb.astype(np.float32)
