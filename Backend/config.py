import torch
from pathlib import Path

if torch.backends.mps.is_available():
    DEVICE = "mps"
elif torch.cuda.is_available():
    DEVICE = "cuda"
else:
    DEVICE = "cpu"
    
CFG = {
    "data_path" : "/Users/merterol/Desktop/rag2026/Data/cleaned_datasets/arxiv_data_22_04_cleaned.csv",
    "col_title" : "titles",
    "col_abstract" : "abstracts",
    "col_categories" : "categories",
    "col_primary_cat" : "primary_category",
    "col_authors" : "authors",
    "col_pdf_url" : "pdf_url",
    "col_published" : "published",
    "col_entry_id" : "entry_ids",
    
    
    "embed_model" : "sentence-transformers/all-mpnet-base-v2",
    "embed_dim" : 256,
    
    "index_path" : "arxiv.faiss",
    "meta:path" : "arxiv_meta.json",
    
    "llm_model" : "eepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
    "llm_max_tokens" : 2048,
    "llm_temperature" : 0.7,
    "llmn_load_in_4bit" : False,
    
    "top_k" : 5,
}