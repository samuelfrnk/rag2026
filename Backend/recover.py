"""
recover_meta.py
---------------
Rebuilds arxiv_meta.json from the CSV without re-embedding.
Run this if the .faiss file exists but arxiv_meta.json is missing.

    python recover_meta.py
"""

import json
import pandas as pd
from pathlib import Path
from config import CFG


def safe(row, col: str) -> str:
    val = row.get(col, "")
    return "" if pd.isna(val) else str(val)


def main():
    assert Path(CFG["index_path"]).exists(), (
        f"No .faiss file found at '{CFG['index_path']}' — nothing to recover."
    )
    assert not Path(CFG["meta_path"]).exists(), (
        f"'{CFG['meta_path']}' already exists — delete it first if you want to rebuild."
    )

    print("Loading dataset …")
    df = pd.read_csv(CFG["data_path"])
    df.columns = [c.strip().lower() for c in df.columns]
    df = (
        df.dropna(subset=[CFG["col_title"], CFG["col_abstract"]])
          .drop_duplicates(subset=CFG["col_title"])
          .reset_index(drop=True)
    )
    print(f"  {len(df):,} rows after dedup/dropna")

    print("Building meta …")
    meta = [
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

    print(f"Writing {CFG['meta_path']} …")
    with open(CFG["meta_path"], "w") as f:
        json.dump(meta, f)

    print(f"Done — {len(meta):,} entries written to '{CFG['meta_path']}'.")


if __name__ == "__main__":
    main()