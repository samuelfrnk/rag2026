import os
import pandas as pd
import psycopg2
import numpy as np
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from dotenv import load_dotenv

"""
Local Docker test instance (identical to Nuvolos config):

docker run -d --name pgvector-local -e POSTGRES_PASSWORD=pgvec_42 -p 5432:5432 pgvector/pgvector:pg16

docker exec -it pgvector-local psql -U postgres -c "CREATE DATABASE rag_db;"

docker run -d --name pgvector-local
    -e POSTGRES_PASSWORD=pgvec_42
    -p 5432:5432
    pgvector/pgvector:pg16
"""


load_dotenv()

CLEANED_DATA  = "cleaned_datasets/arxiv_scrape_1_cleaned.csv"

EMBEDDING_MODEL  = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIM    = 384
BATCH_SIZE       = 64
TABLE_NAME       = "abstracts"

DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:pgvec_42@localhost:5432"
)


SCHEMA_SQL = f"""
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;   -- enables hybrid keyword search later

CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    id            SERIAL PRIMARY KEY,
    entry_id      TEXT        NOT NULL UNIQUE,   -- arxiv ID
    title         TEXT        NOT NULL,
    abstract      TEXT        NOT NULL,
    terms         TEXT        DEFAULT '',        -- space-separated; filter before ANN
    pdf_url       TEXT        DEFAULT '',
    content_hash  TEXT        NOT NULL,          -- SHA-256 of abstract; used for upserts
    embedding     vector({EMBEDDING_DIM}),        -- the money column
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- ── Indexes ──────────────────────────────────────────────────────────────────

-- HNSW index for approximate nearest-neighbour (better recall than IVFFlat,
-- no need to VACUUM/rebuild when you add rows)
-- m=16, ef_construction=64 are good starting defaults; tune after benchmarking
CREATE INDEX IF NOT EXISTS idx_abstracts_embedding_hnsw
    ON {TABLE_NAME}
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Trigram index on abstract text for hybrid keyword search
CREATE INDEX IF NOT EXISTS idx_abstracts_abstract_trgm
    ON {TABLE_NAME}
    USING gin (abstract gin_trgm_ops);

-- Trigram index on title
CREATE INDEX IF NOT EXISTS idx_abstracts_title_trgm
    ON {TABLE_NAME}
    USING gin (title gin_trgm_ops);

-- B-tree on terms for fast pre-filtering before vector search
CREATE INDEX IF NOT EXISTS idx_abstracts_terms
    ON {TABLE_NAME} (terms);
"""

UPSERT_SQL = f"""
INSERT INTO {TABLE_NAME}
    (entry_id, title, abstract, terms, pdf_url, content_hash, embedding)
VALUES
    (%s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (entry_id) DO UPDATE SET
    title        = EXCLUDED.title,
    abstract     = EXCLUDED.abstract,
    terms        = EXCLUDED.terms,
    pdf_url      = EXCLUDED.pdf_url,
    content_hash = EXCLUDED.content_hash,
    embedding    = EXCLUDED.embedding;
"""
# ─────────────────────────────────────────────────────────────────────────────


def get_connection():
    conn = psycopg2.connect(DB_URL)
#    register_vector(conn)
    return conn


def init_schema(conn):
    with conn.cursor() as cur:
        cur.execute(SCHEMA_SQL)
    conn.commit()
    print("Database schema initialised")


def embed_batch(model: SentenceTransformer, texts: list[str]):
    """Returns L2-normalised embeddings (required for cosine similarity via dot product)."""
    vecs = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return vecs.astype(np.float32)


def ingest(df: pd.DataFrame, conn, model: SentenceTransformer):
    rows = df.to_dict("records")
    total = len(rows)

    with conn.cursor() as cur:
        for start in tqdm(range(0, total, BATCH_SIZE), desc="Inserting batches"):
            batch = rows[start : start + BATCH_SIZE]
            texts = [r["abstracts"] for r in batch]
            embeddings = embed_batch(model, texts)

            records = [
                (
                    r["entry_ids"],
                    r["titles"],
                    r["abstracts"],
                    r["terms"],
                    r["pdf_urls"],
                    r["content_hash"],
                    emb.tolist(),
                )
                for r, emb in zip(batch, embeddings)
            ]
            cur.executemany(UPSERT_SQL, records)
            conn.commit()

    print(f"\nIngested {total:,} rows ✓")


def verify(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {TABLE_NAME};")
        n = cur.fetchone()[0]
        cur.execute(
            f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE embedding IS NOT NULL;"
        )
        n_emb = cur.fetchone()[0]
    print(f"\nDB check: {n:,} rows total, {n_emb:,} with embeddings")


if __name__ == "__main__":
    print(f"Loading model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)

    print(f"Loading cleaned data from: {CLEANED_DATA}")
    df = pd.read_csv(CLEANED_DATA)
    print(f"  {len(df):,} rows ready for ingestion")

    conn = get_connection()
    try:
        init_schema(conn)
        ingest(df, conn, model)
        verify(conn)
    finally:
        conn.close()
