"""
FAISS retriever — loads the index + metadata and searches for similar papers.
Source: proof_of_concept.ipynb → load_index(), retrieve()
"""

import ast
import json
import re
import sys
from pathlib import Path
from typing import Optional

import faiss
import numpy as np

from core import embedder

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import CFG

INDEX_PATH  = Path(CFG["index_path"])
META_PATH   = Path(CFG["meta_path"])

_index: faiss.Index | None = None
_meta:  list | None        = None


def load() -> None:
    """Load arxiv.faiss and arxiv_meta.json into memory."""
    global _index, _meta
    print("Loading FAISS index and metadata...")
    _index = faiss.read_index(str(INDEX_PATH))
    with open(META_PATH, "r") as f:
        _meta = json.load(f)
    print(f"Index loaded: {_index.ntotal} vectors | {len(_meta)} papers in metadata.")


def search(query: str, top_k: int, categories: Optional[list[str]] = None) -> list[dict]:
    """
    Embed query, search FAISS, apply optional category filter.
    Returns a list of metadata dicts each with an added 'score' key.
    """
    if _index is None or _meta is None:
        raise RuntimeError("Retriever not loaded. Call retriever.load() first.")

    # BGE models require "query: " prefix for search queries
    prefixed_query = f"query: {query}"
    q_emb = embedder.embed(prefixed_query)

    #q_emb   = embedder.embed(query)
    fetch_k = min(top_k * 10 if categories else top_k, _index.ntotal)
    scores, ids = _index.search(q_emb, fetch_k)

    results = []
    for score, idx_val in zip(scores[0], ids[0]):
        if idx_val == -1:
            continue
        entry = _meta[idx_val].copy()
        entry["score"] = float(score)

        if categories:
            terms = _parse_terms(entry.get("categories", ""))
            if not any(cat in terms for cat in categories):
                continue

        results.append(entry)
        if len(results) >= top_k:
            break

    return results


def get_by_index(idx: int) -> dict:
    """Return the metadata entry for a given FAISS index position."""
    if _meta is None:
        raise RuntimeError("Retriever not loaded. Call retriever.load() first.")
    if idx < 0 or idx >= len(_meta):
        raise IndexError(f"Index {idx} out of range (0–{len(_meta) - 1}).")
    return _meta[idx]


def index_size() -> int:
    """Return the total number of vectors in the FAISS index."""
    return _index.ntotal if _index else 0


def meta_size() -> int:
    """Return the number of entries in the metadata list."""
    return len(_meta) if _meta else 0


def _parse_terms(raw: str) -> list[str]:
    """Turn the stored string "['cs.CV', 'cs.LG']" into a Python list."""
    if not raw:
        return []
    try:
        parsed = ast.literal_eval(raw)
        if isinstance(parsed, list):
            return [str(t) for t in parsed]
    except Exception:
        pass
    cleaned = re.sub(r"[\[\]'\"]", "", raw)
    return [t.strip() for t in cleaned.split(",") if t.strip()]
