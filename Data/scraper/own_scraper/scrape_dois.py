import os
import re
import sys
import arxiv
import pandas as pd
import datetime
import config_reader
import requests
import time


doi_list = [
    "1706.03762",

    "1312.5851",
    "1202.2160",
    "1202.6384",
    "1010.3467",
    "1412.6980",
    "1512.03385",

    "1810.04805",

    "2005.14165",
    "2302.13971",
    "1512.03385",
    "1406.2661",
    "1312.6114",
    "1409.0575",
    "2010.11929",
    "2006.11239",
    "1312.5602",
    "1707.06347",
    "1301.3781",
    "1301.3781",
]



doi_file = "top_cited_ids.txt"
#base_csv = "arxiv_dois_14_05.csv"
base_csv = "arxiv_data_30_04_sz_2000.csv"

merged_csv = "arxiv_data_merged_full.csv"
doi_file_filtered = "top_cited_ids_filtered.txt"

resume_index_override = 0

clear_file = False
doi_file = doi_file_filtered

resume_index_override = 5410

batch = 4

dt_string_date = datetime.datetime.now().strftime("%d_%m")

csv_path = f"arxiv_dois_13_05.csv"

def doi_to_arxiv_id(doi: str) -> str | None:

    doi = doi.strip()
    if not doi:
        return None

    # Direct Arxiv ID
    m = re.search(r"10\.48550/arxiv\.([^\s/?#]+)", doi, re.IGNORECASE)
    if m:
        return m.group(1)
    
    return None
 
    # DOI lookup
    try:
        resp = requests.get(
            "https://api.openalex.org/works",
            params={"filter": f"doi:{doi}", "select": "ids"},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if results:
            arxiv_url = results[0].get("ids", {}).get("arxiv", "")
            if arxiv_url:
                return arxiv_url.replace("https://arxiv.org/abs/", "").strip()
    except Exception as e:
        print(f"  -> OpenAlex lookup failed for {doi}: {e}")
 
    return None


def load_dois() -> list[str]:

    if len(doi_list) > 0:
        resume_index_override = 0
        doi_list.reverse()
        return doi_list

    with open(doi_file, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def get_resume_index() -> int:

    if clear_file:
        df = pd.DataFrame()
        df.to_csv(csv_path, mode="w", index=False)
        print("csv cleared, resetting index to 0")

        return 0

    if resume_index_override != 0:
        return resume_index_override

    if not os.path.exists(csv_path):
        return 0
    try:
        return len(pd.read_csv(csv_path))
    except Exception:
        return 0

def filter_dois():

    data = load_dois()
    filtered = [x for x in data if doi_to_arxiv_id(x)]

    print(f"filtering dois: {len(filtered)}/{len(data)}, removed {len(data)-len(filtered)} lines")

    r = (len(filtered)/len(data)) * 100

    print(f"\t new size: {len(filtered)}, {r:.2f}%")


    with open(doi_file_filtered, "w", encoding="utf-8") as f:
        for l in filtered:
            f.write(l + "\n")


    print(f"filtered dois written to {doi_file_filtered}")


def run_scraper():

    dois = load_dois()
    total = len(dois)
    resume_at = get_resume_index()
    resume_at = 0

    print(f"DOI file  : {doi_file}  ({total} entries)")
    print(f"Output CSV: {csv_path}")
    print(f"Resuming from index {resume_at} ({total - resume_at} remaining)\n")

    if resume_at >= total:
        print("Scrape already complete.")
        return

    client = arxiv.Client(num_retries=3, page_size=1)

    results_buffer = []

    write_interval = 10

    max_batch = total // batch

    res_batch = resume_at // batch

    for i in range(res_batch, max_batch):

        c_i = i * batch

        raw_dois = []
        arxiv_ids = []

        for ix in range(c_i, c_i + batch):
            raw_dois.append(dois[ix])
            arxiv_ids.append(doi_to_arxiv_id(dois[ix]))
        #raw_doi   = dois[i]
        #arxiv_id  = doi_to_arxiv_id(raw_doi)


        #if arxiv_id is None:
        #    print(f"[{i+1}/{total}] SKIP — cannot parse arXiv ID from: {raw_doi}")
        #    continue

        try:
            search  = arxiv.Search(id_list=arxiv_ids)
            results = list(client.results(search))

            if not results:
                print(f"[{i+1}/{total}] IDS NOT FOUND — {arxiv_ids}")
                continue


            if batch > len(results):
                print(f" BATCH NOT FULL; found {len(results)}/{batch}")
                
            for iy in range(batch):

                ix = c_i + iy 

                if iy > len(results):
                    print(f"SKIPPING INDEX {iy}")

                res = results[iy]
                arxiv_id = arxiv_ids[iy]

                converted = config_reader.get_arxiv_columns(res)
                results_buffer.append(converted)
                print(f"[{ix}/{total}] OK — {arxiv_id} | {res.title[:60]}")

        except KeyboardInterrupt:
            print("\nInterrupted. Saving progress...")
            _flush(results_buffer, first_write=(resume_at == 0))
            print(f"Saved {len(results_buffer)} new rows to {csv_path}. Rerun to continue.")
            sys.exit(0)

        except Exception as e:
            print(f"[{i+1}/{total}] ERROR — {arxiv_ids}: {e}")
            if "HTTP 429" in str(e):
                delay = 180
                print(f"DETECTED HTTP 429 Error: waiting for {delay} seconds...")
                time.sleep(delay)
            continue

        #if i % write_interval == 0:
        print(f"\t writing buffer to file {csv_path}...")
        _flush(results_buffer, first_write=(i == 0))
        results_buffer.clear() 


    _flush(results_buffer, first_write=(resume_at == 0))
    print(f"\nDone. {len(results_buffer)} new rows written to {csv_path}.")


def _flush(results: list[dict], first_write: bool):
    """Append results_buffer to csv_path (write header only on first write)."""
    if not results:
        return
    df = pd.DataFrame(results)
    df.to_csv(csv_path, mode="a", index=False, header=first_write)



def merge_with_base():

    dfs = []
    for path in [base_csv, csv_path]:
        if not os.path.exists(path):
            print(f"  -> Warning: not found, skipping: {path}")
            continue
        try:
            dfs.append(pd.read_csv(path))
        except Exception as e:
            print(f"  -> Warning: could not read {path}: {e}")

    if not dfs:
        print("No data to merge.")
        return

    merged = pd.concat(dfs, ignore_index=True).drop_duplicates(subset="titles")
    merged.to_csv(merged_csv, index=False)
    print(f"{len(merged)} unique papers saved to {merged_csv}")


if __name__ == "__main__":

    #run_scraper()
    #merge_with_base()
    #sys.exit(0)


    if doi_file != doi_file_filtered:
        filter_dois()
        doi_file = doi_file_filtered


    #sys.exit(0)


    run_scraper()

    dois = load_dois()
    total = len(dois)
    rows = get_resume_index()

    if rows >= total:
        print(f"\nScrape complete ({rows}/{total}). Merging with base CSV...")
        merge_with_base()
    else:
        print(f"\nScrape not yet complete ({rows}/{total} rows). Skipping merge.")
