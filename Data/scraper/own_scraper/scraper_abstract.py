
# arxiv_fetch.py

import arxiv
import pandas as pd
import time

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

client = arxiv.Client(num_retries=5, page_size=50)

def query_with_keywords(query):
    search = arxiv.Search(
        query=query,
        max_results=150,
        sort_by=arxiv.SortCriterion.LastUpdatedDate,
    )
    results = []
    for res in client.results(search):
        results.append({
            "id": res.entry_id.split("/")[-1].split("v")[0],
            "pdf_url": res.pdf_url,
            "terms": res.categories,
            "titles": res.title,
            "abstracts": res.summary
        })
    return results


all_results = []

for i, keyword in enumerate(query_keywords):
    print(f"[{i+1}/{len(query_keywords)}] Querying: {keyword}...")
    try:
        results = query_with_keywords(keyword)
        all_results.extend(results)
        print(f"  -> {len(results)} papers found, {len(all_results)} total so far")
    except Exception as e:
        print(f"  -> Failed: {e}")


df = pd.DataFrame(all_results).drop_duplicates(subset="titles")
df.to_csv("arxiv_data.csv", index=False)
print(f"\n{len(df)} unique papers saved to arxiv_data.csv")