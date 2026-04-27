"""
build_index.py
--------------
One-time script that builds the FAISS index from the arXiv CSV dataset
and saves it to disk so the backend can load it at startup.

Run this ONCE before starting the backend:
    python build_index.py

Output files (written to the same directory as this script):
    arxiv.faiss       — FAISS flat index
    arxiv_meta.json   — parallel metadata list (title, abstract, authors, …)

You only need to re-run this if:
    - You change the dataset
    - You change the embedding model in config.py
    - You delete the cache files
"""

import json
import time
from pathlib import Path

import faiss
import numpy as np
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer
from tqdm.auto import tqdm

from config import CFG, DEVICE


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_dataset() -> pd.DataFrame:
    path = CFG["data_path"]
    assert Path(path).exists(), (
        f"Dataset not found at '{path}'.\n"
        "Download the CSV and update 'data_path' in config.py."
    )

    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]

    required = [CFG["col_title"], CFG["col_abstract"]]
    for col in required:
        assert col in df.columns, (
            f"Column '{col}' not found in CSV.\n"
            f"Available columns: {list(df.columns)}"
        )

    before = len(df)
    df = (
        df.dropna(subset=required)
        .drop_duplicates(subset=CFG["col_title"])
        .reset_index(drop=True)
    )
    print(f"Dataset loaded:  {before:,} rows → {len(df):,} after dedup/dropna")
    return df


def embed_texts(texts: list[str], model: SentenceTransformer) -> np.ndarray:
    batch_size = CFG["embed_batch"]
    all_embs   = []

    for i in tqdm(range(0, len(texts), batch_size), desc="Embedding batches"):
        batch = texts[i : i + batch_size]
        embs  = model.encode(batch, convert_to_numpy=True, show_progress_bar=False)
        # L2-normalise so inner product == cosine similarity
        embs  = embs / (np.linalg.norm(embs, axis=1, keepdims=True) + 1e-10)
        all_embs.append(embs.astype(np.float32))

    return np.vstack(all_embs)


def build_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatIP:
    dim   = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    print(f"FAISS index built: {index.ntotal:,} vectors, dim={dim}")
    return index


def build_meta(df: pd.DataFrame) -> list[dict]:
    """
    Build the metadata list that runs in parallel with the FAISS index.
    Index row N → meta[N].
    """
    def safe(row, col: str) -> str:
        val = row.get(col, "")
        return "" if pd.isna(val) else str(val)

    return [
        {
            "idx"             : int(i),
            "title"           : safe(row, CFG["col_title"]),
            "abstract"        : safe(row, CFG["col_abstract"]),
            "categories"      : safe(row, CFG["col_categories"]),
            "primary_category": safe(row, CFG["col_primary_cat"]),
            "authors"         : safe(row, CFG["col_authors"]),
            "pdf_url"         : safe(row, CFG["col_pdf_url"]),
            "published"       : safe(row, CFG["col_published"]),
            "entry_id"        : safe(row, CFG["col_entry_id"]),
        }
        for i, row in df.iterrows()
    ]


def save(index: faiss.IndexFlatIP, meta: list[dict]) -> None:
    faiss.write_index(index, CFG["index_path"])
    with open(CFG["meta_path"], "w") as f:
        json.dump(meta, f)
    print(f"Saved → {CFG['index_path']}")
    print(f"Saved → {CFG['meta_path']}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Guard: skip if cache already exists
    if Path(CFG["index_path"]).exists() and Path(CFG["meta_path"]).exists():
        print(
            "Index already exists — delete the files below and re-run to rebuild:\n"
            f"  {CFG['index_path']}\n"
            f"  {CFG['meta_path']}"
        )
        return

    print(f"Device : {DEVICE.upper()}")
    print(f"Model  : {CFG['embed_model']}\n")

    t_start = time.time()

    # 1. Load CSV
    df = load_dataset()

    # 2. Load embedding model
    print(f"\nLoading embedding model …")
    embed_model = SentenceTransformer(CFG["embed_model"], device=DEVICE)
    print(f"Embedding dim: {embed_model.get_sentence_embedding_dimension()}\n")

    # 3. Build combined text field for embedding (title + abstract)
    texts = (
        df[CFG["col_title"]].str.strip()
        + " [SEP] "
        + df[CFG["col_abstract"]].str.strip()
    ).tolist()

    # 4. Embed
    print(f"Embedding {len(texts):,} papers …")
    embeddings = embed_texts(texts, embed_model)

    # 5. Build FAISS index
    print("\nBuilding FAISS index …")
    index = build_faiss_index(embeddings)

    # 6. Build metadata
    meta = build_meta(df)

    # 7. Save to disk
    print("\nSaving to disk …")
    save(index, meta)

    elapsed = time.time() - t_start
    print(f"\nDone in {elapsed:.1f}s — index is ready for the backend.")


if __name__ == "__main__":
    main()