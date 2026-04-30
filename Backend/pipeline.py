import torch
from config import CFG, DEVICE

def build_prompt(query, retrieved, pdf_context = ""):
    context_blocks = []
    for i, r in enumerate(retrieved, 1):
        context_blocks.append(
            f"[Paper {i}]\n"
            f"Title    : {r['title']}\n"
            f"Authors  : {r.get('authors', 'N/A')}\n"
            f"Published: {r.get('published', 'N/A')}\n"
            f"Category : {r.get('primary_category', r.get('categories', 'N/A'))}\n"
            f"Abstract : {r.get('abstract', '')[:600]}{'…' if len(r.get('abstract', '')) > 600 else ''}"
        )
    
    if pdf_context:
        context_blocks.append(f"[PDF Context]\n{pdf_context[:2000]}")
    
    context = "\n\n".join(context_blocks)
    pdf_note = (
        "If a PDF was attached, refer to it as [Attached PDF] and use its content to enhance your answer. "
        if pdf_context else "")
    
    return (
        "You are a helpful scientific assistant. "
        "Use ONLY the papers provided below to answer the user's question. "
        "Enumerate and list all papers that you found."
        "Cite papers by their number, e.g. [Paper 1], and quote the specific claim "
        "from the abstract that supports your answer."
        f"{pdf_note} "
        "If the answer cannot be found in the provided papers, say so.\n\n"
        "=== RETRIEVED PAPERS ===\n"
        f"{context}\n\n"
        "=== USER QUESTION ===\n"
        f"{query}\n\n"
        "=== YOUR ANSWER ===\n"
    )

def generate_answer(prompt):
    from models import APP_STATE
    
    tokenizer = APP_STATE['tokenizer']
    model = APP_STATE['llm']
    
    try:
        messages  = [{"role": "user", "content": prompt}]
        input_ids = tokenizer.apply_chat_template(
            messages,
            return_tensors        = "pt",
            add_generation_prompt = True,
        )
        if hasattr(input_ids, "input_ids"):
            input_ids = input_ids.input_ids
        input_ids = input_ids.to(DEVICE)
    except Exception:
        input_ids = tokenizer(prompt, return_tensors="pt").input_ids.to(DEVICE)
        
    with torch.no_grad():
        output_ids = model.generate(
            input_ids,
            attention_mask = torch.ones_like(input_ids),
            max_new_tokens = CFG["llm_max_tokens"],
            temperature = CFG["llm_temperature"],
            do_sample = CFG["llm_temperature"] > 0,
            pad_token_id = tokenizer.eos_token_id,
        )
        
    new_tokens = output_ids[0][input_ids.shape[-1]:]
    return tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

def generate_chat_answer(messages):
    from models import APP_STATE
    
    tokenizer = APP_STATE['tokenizer']
    model = APP_STATE['llm']
    
    try:
        input_ids = tokenizer.apply_chat_template(
            messages,
            return_tensors        = "pt",
            add_generation_prompt = True,
        )
        if hasattr(input_ids, "input_ids"):
            input_ids = input_ids.input_ids
        input_ids = input_ids.to(DEVICE)
    except Exception:
        flat = "\n".join(
            f"{m['role'].capitalize()}: {m['content']}" for m in messages
        ) + "\nAssistant:"
        input_ids = tokenizer(flat, return_tensors="pt").input_ids.to(DEVICE)
        
    with torch.no_grad():
        output_ids = model.generate(
            input_ids,
            attention_mask = torch.ones_like(input_ids),
            max_new_tokens = CFG["llm_max_tokens"],
            temperature = CFG["llm_temperature"],
            do_sample = CFG["llm_temperature"] > 0,
            pad_token_id = tokenizer.eos_token_id,
        )
        
    new_tokens = output_ids[0][input_ids.shape[-1]:]
    return tokenizer.decode(new_tokens, skip_special_tokens=True).strip()