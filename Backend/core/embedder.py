"""
Embedding model — loads sentence-transformers and embeds text into vectors.
Source: proof_of_concept.ipynb → load_embed_model(), embed_texts()
"""

import numpy as np


def load() -> None:
    """Load the sentence-transformer model into memory."""
    raise NotImplementedError


def embed(text: str) -> np.ndarray:
    """Embed a single string, return a normalised float32 vector (shape: [1, 384])."""
    raise NotImplementedError
