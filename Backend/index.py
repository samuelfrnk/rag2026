import json
import numpy as np
import faiss
from pathlib import Path

from config import CFG, DEVICE


def load_index() -> tuple[faiss.IndexFlatIP, list[dict]]:
    index_path = CFG["index_path"]
    meta_path  = CFG["meta_path"]

    assert Path(index_path).exists(), (
        f"FAISS index not found at '{index_path}'.\n"
        "Run the notebook first to build and cache the index."
    )
    assert Path(meta_path).exists(), (
        f"Metadata file not found at '{meta_path}'.\n"
        "Run the notebook first to build and cache the metadata."
    )

    index = faiss.read_index(index_path)
    with open(meta_path) as f:
        meta = json.load(f)

    print(f"[startup] FAISS index loaded: {index.ntotal:,} vectors, dim={index.d}")
    return index, meta


def retrieve(query: str, top_k: int) -> list[dict]:
    from models import APP_STATE   # lazy import — APP_STATE is populated by lifespan

    embed_model = APP_STATE["embed_model"]
    index       = APP_STATE["index"]
    meta        = APP_STATE["meta"]

    q_emb = embed_model.encode([query], convert_to_numpy=True)
    q_emb = (q_emb / (np.linalg.norm(q_emb, axis=1, keepdims=True) + 1e-10)).astype(np.float32)

    scores, ids = index.search(q_emb, top_k)

    results = []
    for score, idx in zip(scores[0], ids[0]):
        if idx == -1:
            continue
        entry = meta[idx].copy()
        entry["score"] = float(score)
        results.append(entry)
    return results