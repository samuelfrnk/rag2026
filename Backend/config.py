import torch
from pathlib import Path

if torch.backends.mps.is_available():
    DEVICE = "mps"
elif torch.cuda.is_available():
    DEVICE = "cuda"
else:
    DEVICE = "cpu"
    
CFG = {
    "data_path" : "/files/rag2026/arxiv_data_30_04_sz_2000.csv",
    "col_title" : "titles",
    "col_abstract" : "abstracts",
    "col_categories" : "categories",
    "col_primary_cat" : "primary_category",
    "col_authors" : "authors",
    "col_pdf_url" : "pdf_url",
    "col_published" : "published",
    "col_entry_id" : "entry_ids",
    
    
    "embed_model" : "sentence-transformers/all-MiniLM-L6-v2",
    "embed_batch" : 64,
    "embed_dim" : 256,
    
    "index_path" : "/files/tmp/arxiv.faiss",
    "meta_path" : "/files/tmp/arxiv_meta.json",
    
    "llm_model" : "Qwen/Qwen2.5-0.5B-Instruct",
    "llm_max_tokens" : 4096,
    "llm_temperature" : 0.7,
    "llmn_load_in_4bit" : False,
    
    "top_k" : 8,
}