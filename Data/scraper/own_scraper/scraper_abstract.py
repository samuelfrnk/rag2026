
# arxiv_fetch.py
import os
import arxiv
import pandas as pd
import datetime
import config_reader

num_results = 2000

dt_string_full = datetime.datetime.now().strftime("%d_%m_%H_%M")
dt_string_date = datetime.datetime.now().strftime("%d_%m")
dt_string_date = "30_04" 

parts_dir_path = os.path.join("Data", "datasets", "parts", dt_string_date)
#f"\datasets\parts\{dt_string_date}" 
csv_path = f"arxiv_data_{dt_string_date}_sz_{num_results}.csv"

parts_abs_path = os.path.join(os.getcwd(), parts_dir_path)
#os.path.abspath(parts_dir_path)

query_categories = [
"cs.AI",
"cs.AR",
"cs.CC",
"cs.CE",
"cs.CG",
"cs.CL",
"cs.CR",
"cs.CV",
"cs.CY",
"cs.DB",
"cs.DC",
"cs.DL",
"cs.DM",
"cs.DS",
"cs.ET",
"cs.FL",
"cs.GL",
"cs.GR",
"cs.GT",
"cs.HC",
"cs.IR",
"cs.IT",
"cs.LG",
"cs.LO",
"cs.MA",
"cs.MM",
"cs.MS",
"cs.NA",
"cs.NE",
"cs.NI",
"cs.OH",
"cs.OS",
"cs.PF",
"cs.PL",
"cs.RO",
"cs.SC",
"cs.SD",
"cs.SE",
"cs.SI",
"cs.SY",
"stat.CO",
"stat.ME",
"stat.ML",
"stat.TH",
"math.CO",
"math.DS",
"math.IT",
"math.LO",
"math.OC",
"math.PR",
"math.ST",
]

query_keywords = [
    "image segmentation",
    "self-supervised learning",
    "representation learning",
    "image generation",
    "object detection",
    "transfer learning",
    "transformers",
    "adversarial training",
    "generative adversarial networks",
    "model compression",
    "few-shot learning",
    "natural language",
    "graph neural network",
    "colorization",
    "depth estimation",
    "point cloud",
    "structured data",
    "optical flow",
    "reinforcement learning",
    "super resolution",
    "attention mechanism",
    "tabular learning",
    "unsupervised learning",
    "semi-supervised learning",
    "explainable AI",
    "radiance field",
    "decision tree",
    "time series",
    "molecule generation",
    "physics simulation",
    "computer graphics",
    "ray tracing",
    "photogrammetry",
]


def keyword_to_filename(keyword):
    """Convert a keyword string to a safe filename."""
    return keyword.replace(" ", "_") + ".csv"


def get_parts():
    """Return a set of keyword filenames already scraped in the parts directory."""
    if not os.path.exists(parts_abs_path):
        return set()
    return set(os.listdir(parts_abs_path))


def merge_parts():
    """Merge all part CSVs into a single deduplicated CSV."""
    parts = get_parts()
    if not parts:
        print("No part files found to merge.")
        return

    dfs = []
    for fname in parts:
        fpath = os.path.join(parts_abs_path, fname)
        try:
            dfs.append(pd.read_csv(fpath))
        except Exception as e:
            print(f"  -> Warning: could not read {fname}: {e}")

    if not dfs:
        print("No data loaded from parts.")
        return

    merged = pd.concat(dfs, ignore_index=True).drop_duplicates(subset="titles")
    merged.to_csv(csv_path, index=False)
    print(f"\n{len(merged)} unique papers saved to {csv_path}")


def run_scraper():

    os.makedirs(parts_abs_path, exist_ok=True)

    already_done = get_parts()

    print(f"parts dir: {parts_abs_path}")
    print(f"{len(already_done)} parts found; {len(query_categories)-len(already_done)} remaining")

    client = arxiv.Client(num_retries=3, page_size=50)

    def query_with_keywords(query, sort_type = arxiv.SortCriterion.LastUpdatedDate):
        search = arxiv.Search(
            query=f"cat:{query}",
            max_results=num_results,
            sort_by=sort_type,
        )
        results = []
        for res in client.results(search):

            converted_result = config_reader.get_arxiv_columns(res)
            results.append(converted_result)

        return results

    all_results = []

    for i, keyword in enumerate(query_categories):
        part_filename = keyword_to_filename(keyword)
        part_filepath = os.path.join(parts_abs_path, part_filename)

        if part_filename in already_done:
            print(f"[{i+1}/{len(query_categories)}] Skipping (already done): {keyword}")
            continue

        print(f"[{i+1}/{len(query_categories)}] Querying: {keyword}...")
        try:
            results = query_with_keywords(keyword)
            df_part = pd.DataFrame(results)
            df_part.to_csv(part_filepath, index=False)
            print(f"  -> {len(results)} papers found, saved to {part_filename}")
        except Exception as e:
            print(f"  -> Failed: {e}")

    merge_parts()


if __name__ == "__main__":
    print(f"RUNNING SCRAPER, id: {dt_string_date}")
    print(f"{len(query_categories)} keywords, {num_results} results")
    print(f"\t{len(query_categories) * num_results} data points expected")
    run_scraper()