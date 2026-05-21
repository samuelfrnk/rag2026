import os
import arxiv
import pandas as pd
import datetime
import config_reader
import requests
import json


DOI_PATH = ""
CSV_PATH = ""

def doi_to_arxiv_id(doi: str) -> str | None:
    """
    Extract a bare arXiv ID from a variety of DOI / URL formats.
    Returns None if no arXiv ID can be identified.
    """
    doi = doi.strip()
    if not doi:
        return None

    return doi.strip("https://doi.org/")

    # https://arxiv.org/abs/XXXX  or  http://arxiv.org/abs/XXXX
    m = re.search(r"arxiv\.org/abs/([^\s/?#]+)", doi, re.IGNORECASE)
    if m:
        return m.group(1)

    # DOI style:  10.48550/arXiv.XXXX  or  10.48550/arxiv.XXXX
    m = re.search(r"10\.\d{4,}/arxiv\.([^\s/?#]+)", doi, re.IGNORECASE)
    if m:
        return m.group(1)

    # Bare arXiv ID like  2301.07041  or  cs/0501042
    m = re.fullmatch(r"(\d{4}\.\d{4,5}(v\d+)?|[a-z\-]+/\d{7}(v\d+)?)", doi, re.IGNORECASE)
    if m:
        return doi

    return None


def result_to_row(res: arxiv.Result) -> dict:
    """Convert an arxiv.Result to a flat dict for CSV storage."""
    return {
        "arxiv_id":   res.entry_id.split("/abs/")[-1],
        "title":      res.title,
        "authors":    ", ".join(str(a) for a in res.authors),
        "abstract":   res.summary.replace("\n", " "),
        "published":  res.published.isoformat() if res.published else "",
        "updated":    res.updated.isoformat()   if res.updated   else "",
        "categories": ", ".join(res.categories),
        "doi":        res.doi or "",
        "entry_id":   res.entry_id,
        "pdf_url":    res.pdf_url or "",
    }


# ---------------------------------------------------------------------------
# Core scraper
# ---------------------------------------------------------------------------

def load_dois(doi_file: str) -> list[str]:
    with open(doi_file, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def get_resume_index(out_csv: str) -> int:
    """Return the number of rows already saved (= index to resume from)."""
    if not os.path.exists(out_csv):
        return 0
    try:
        df = pd.read_csv(out_csv)
        return len(df)
    except Exception:
        return 0


def scrape_dois(doi_file: str, out_csv: str) -> None:
    dois = load_dois(doi_file)
    total = len(dois)
    resume_at = get_resume_index(out_csv)

    if resume_at >= total:
        print(f"All {total} DOIs already scraped. Nothing to do.")
        return

    print(f"Loaded {total} DOIs from '{doi_file}'.")
    print(f"Resuming from index {resume_at} ({total - resume_at} remaining).\n")

    client = arxiv.Client(num_retries=3, page_size=1)

    write_header = not os.path.exists(out_csv) or resume_at == 0

    with open(out_csv, "a", encoding="utf-8", newline="") as csv_file:
        for i in range(resume_at, total):
            raw_doi = dois[i]
            arxiv_id = doi_to_arxiv_id(raw_doi)

            if arxiv_id is None:
                print(f"[{i+1}/{total}] SKIP  — cannot parse arXiv ID from: {raw_doi}")
                # Write a placeholder row so resume index stays consistent
                row = {"arxiv_id": "", "title": "", "authors": "", "abstract": "",
                       "published": "", "updated": "", "categories": "",
                       "doi": raw_doi, "entry_id": "", "pdf_url": ""}
                _append_row(csv_file, row, write_header)
                write_header = False
                continue

            try:
                search = arxiv.Search(id_list=[arxiv_id])
                results = list(client.results(search))

                if not results:
                    print(f"[{i+1}/{total}] NOT FOUND  — {arxiv_id}")
                    row = {"arxiv_id": arxiv_id, "title": "NOT FOUND", "authors": "",
                           "abstract": "", "published": "", "updated": "",
                           "categories": "", "doi": raw_doi, "entry_id": "", "pdf_url": ""}
                else:
                    converted_result = config_reader.get_arxiv_columns(results)

                    df = pd.DataFrame([converted_result])

                    df.to_csv(csv_file, index=False)

                _append_row(csv_file, row, write_header)
                write_header = False

            except KeyboardInterrupt:
                print("\nInterrupted by user. Progress saved — rerun to continue.")
                sys.exit(0)
            except Exception as e:
                print(f"[{i+1}/{total}] ERROR  — {arxiv_id}: {e}")
                row = {"arxiv_id": arxiv_id, "title": "ERROR", "authors": "",
                       "abstract": str(e), "published": "", "updated": "",
                       "categories": "", "doi": raw_doi, "entry_id": "", "pdf_url": ""}
                _append_row(csv_file, row, write_header)
                write_header = False

    print(f"\nDone. Results saved to '{out_csv}'.")


def _append_row(csv_file, row: dict, write_header: bool) -> None:
    """Append a single dict as a CSV row, flushing immediately for safety."""
    df = pd.DataFrame([row])
    df.to_csv(csv_file, index=False)
    csv_file.flush()


# ---------------------------------------------------------------------------
# Optional merge with a base CSV
# ---------------------------------------------------------------------------

def merge_csvs(base_csv: str, scraped_csv: str, merged_csv: str) -> None:
    """
    Combine base_csv (the 'default' arXiv scrape) with scraped_csv
    (results of this script), deduplicate on arxiv_id, and write merged_csv.
    """
    dfs = []
    for path, label in [(base_csv, "base"), (scraped_csv, "scraped")]:
        if not os.path.exists(path):
            print(f"Warning: {label} CSV not found at '{path}', skipping.")
            continue
        try:
            dfs.append(pd.read_csv(path))
            print(f"Loaded {label} CSV: {path}")
        except Exception as e:
            print(f"Warning: could not read {label} CSV: {e}")

    if not dfs:
        print("No data to merge.")
        return

    merged = pd.concat(dfs, ignore_index=True)

    # Deduplicate: prefer rows where title is not empty / error
    merged = merged[merged["title"].notna() & ~merged["title"].isin(["NOT FOUND", "ERROR"])]
    merged = merged.drop_duplicates(subset="arxiv_id", keep="first")

    merged.to_csv(merged_csv, index=False)
    print(f"Merged {len(merged)} unique papers → '{merged_csv}'")


if __name__ == "__main__":

    # Step 1 — scrape (resumes automatically if out CSV already exists)
    scrape_dois(args.dois, args.out)

    # Step 2 — merge (only if --merge was provided)
    if args.merge:
        merged_path = args.merged or args.out.replace(".csv", "_merged.csv")
        merge_csvs(args.merge, args.out, merged_path)