import os
import pandas as pd
import hashlib

FILENAME = "arxiv_scrape_1"
FILENAME = "arxiv_data_22_04"

CSV_PATH = f"datasets/{FILENAME}.csv"
OUTPUT_PATH = f"cleaned_datasets/{FILENAME}_cleaned.csv"
MIN_ABSTRACT_CHARS = 80

def load(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    print(f"Loaded {len(df):,} rows | columns: {list(df.columns)}")
    return df

def report_nulls(df: pd.DataFrame) -> None:
    null_counts = df.isnull().sum()
    print("\nNull counts per column:")
    print("\t", null_counts[null_counts > 0].to_string() or "  (none)")


def clean(df: pd.DataFrame) -> pd.DataFrame:
    original_len = len(df)

    # Standardise column names
    df.columns = df.columns.str.strip().str.lower()

    # Drop rows where fields are null
    col_names = ["abstracts", "titles", "entry_ids"]
    before = len(df)
    df = df.dropna(subset=col_names)
    print(f"\nDropped {before - len(df):,} rows with null in {col_names}")

    # Drop rows where abstract is too short
    before = len(df)
    df = df[df["abstracts"].str.len() >= MIN_ABSTRACT_CHARS]
    print(f"Dropped {before - len(df):,} rows with abstract < {MIN_ABSTRACT_CHARS} chars")

    # Strip on all string columns
    str_cols = df.select_dtypes(include="object").columns
    df[str_cols] = df[str_cols].apply(lambda c: c.str.strip())

    # Remove exact duplicate abstracts
    before = len(df)
    df = df.drop_duplicates(subset=["abstracts"])
    print(f"Dropped {before - len(df):,} exact-duplicate abstracts")

    # ── 8. Normalise terms
    df["categories"] = (
        df["categories"]
        .str.lower()
        .str.replace(r"\s+", " ", regex=True)
    )

    # hash (useful for incremental upserts later) ──
    df["content_hash"] = df["abstracts"].apply(
        lambda t: hashlib.sha256(t.encode()).hexdigest()
    )

    # Reset index
    df = df.reset_index(drop=True)

    print(f"\nCleaning complete: {original_len:,} -> {len(df):,} rows retained")
    return df


def save(df: pd.DataFrame, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    print(f"\nSaved cleaned data to {path}")

    print(df.describe())
    print(df.head(3).to_string())


if __name__ == "__main__":
    df = load(CSV_PATH)
    report_nulls(df)
    df = clean(df)
    report_nulls(df)
    save(df, OUTPUT_PATH)
