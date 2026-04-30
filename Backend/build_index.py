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
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import json
import time
from pathlib import Path

import faiss
import numpy as np
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModel
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


def mean_pool(token_embeddings: torch.Tensor, attention_mask: torch.Tensor) -> np.ndarray:
    """Mean pooling over token embeddings, masked by attention."""
    mask_expanded = attention_mask.unsqueeze(-1).float()
    summed  = (token_embeddings * mask_expanded).sum(dim=1)
    counts  = mask_expanded.sum(dim=1).clamp(min=1e-10)
    pooled  = (summed / counts).detach().cpu().numpy()
    pooled  = pooled / (np.linalg.norm(pooled, axis=1, keepdims=True) + 1e-10)
    return pooled.astype(np.float32)


def embed_texts(texts: list[str], tokenizer, model, batch_size: int = 32) -> np.ndarray:
    all_embs = []
    model.eval()
    with torch.no_grad():
        for i in tqdm(range(0, len(texts), batch_size), desc="Embedding"):
            batch  = texts[i : i + batch_size]
            inputs = tokenizer(batch, padding=True, truncation=True,
                                max_length=512, return_tensors="pt")
            # keep everything on CPU — avoids MPS segfault entirely
            outputs = model(**inputs)
            embs    = mean_pool(outputs.last_hidden_state, inputs["attention_mask"])
            all_embs.append(embs)
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
    hf_model_id = CFG["embed_model"].replace("sentence-transformers/", "")
    tokenizer = AutoTokenizer.from_pretrained(f"sentence-transformers/{hf_model_id}", use_fast=False)
    embed_model = AutoModel.from_pretrained(f"sentence-transformers/{hf_model_id}")
    embed_model.eval()
    print(f"Embedding dim: {embed_model.config.hidden_size}\n")

    # 3. Build combined text field for embedding (title + abstract)
    texts = (
        df[CFG["col_title"]].str.strip()
        + " [SEP] "
        + df[CFG["col_abstract"]].str.strip()
    ).tolist()

    # 4. Embed
    print(f"Embedding {len(texts):,} papers …")
    embeddings = embed_texts(texts, tokenizer, embed_model, batch_size=CFG["embed_batch"])

    # 5. Build FAISS index
    print("\nBuilding FAISS index …")
    if Path(CFG["index_path"]).exists():
        print(f"Index already exists at '{CFG['index_path']}' — delete it to rebuild.")
        return
    
    index = build_faiss_index(embeddings)
    
    # 6. Build metadata
    print("\nBuilding metadata …")
    if Path(CFG["meta_path"]).exists():
        print(f"Metadata already exists at '{CFG['meta_path']}' — delete it to rebuild.")
        return
    
    meta = build_meta(df)

    # 7. Save to disk
    print("\nSaving to disk …")
    save(index, meta)

    elapsed = time.time() - t_start
    print(f"\nDone in {elapsed:.1f}s — index is ready for the backend.")


if __name__ == "__main__":
    main()