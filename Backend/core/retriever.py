"""
FAISS retriever — loads the index + metadata and searches for similar papers.
Source: proof_of_concept.ipynb → load_index(), retrieve()
"""

from typing import Optional


def load() -> None:
    """Load arxiv.faiss and arxiv_meta.json into memory."""
    raise NotImplementedError


def search(query: str, top_k: int, categories: Optional[list[str]] = None) -> list[dict]:
    """
    Embed query, search FAISS, apply optional category filter.
    Returns a list of metadata dicts each with an added 'score' key.
    """
    raise NotImplementedError


def get_by_index(idx: int) -> dict:
    """Return the metadata entry for a given FAISS index position."""
    raise NotImplementedError


def index_size() -> int:
    """Return the total number of vectors in the FAISS index."""
    raise NotImplementedError


def meta_size() -> int:
    """Return the number of entries in the metadata list."""
    raise NotImplementedError
