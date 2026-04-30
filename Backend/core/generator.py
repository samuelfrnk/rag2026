"""
LLM answer generator — loads the language model and generates RAG answers.
Source: proof_of_concept.ipynb → load_llm(), build_prompt(), generate_answer()
"""

import torch

MODEL_NAME = "Qwen/Qwen2.5-3B-Instruct"

_tokenizer = None
_model     = None


def load() -> bool:
    """
    Lazily load the LLM and tokenizer into memory.
    Returns True on success, False if the model is unavailable.
    """
    global _tokenizer, _model
    if _model is not None:
        return True
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        print(f"Loading LLM: {MODEL_NAME} ...")
        device = (
            "mps"  if torch.backends.mps.is_available()  else
            "cuda" if torch.cuda.is_available()           else
            "cpu"
        )
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        _model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            dtype=torch.float16 if device != "cpu" else torch.float32,
            device_map="auto"   if device != "cpu" else None,
        )
        if device == "cpu":
            _model = _model.to(device)
        _model.eval()
        print("LLM loaded.")
        return True
    except Exception as exc:
        print(f"LLM load failed: {exc}")
        return False


def build_prompt(question: str, retrieved: list[dict]) -> str:
    """
    Build the RAG prompt from the question and retrieved paper dicts.
    Each dict is expected to have 'title', 'summary', 'terms'.
    """
    context_blocks = []
    for i, r in enumerate(retrieved, 1):
        abstract = r.get("summary", "")[:600]
        context_blocks.append(
            f"[Paper {i}]\n"
            f"Title: {r['title']}\n"
            f"Terms: {r.get('terms', 'N/A')}\n"
            f"Abstract: {abstract}"
        )
    context = "\n\n".join(context_blocks)

    return (
        "You are a helpful scientific assistant. "
        "Use ONLY the papers provided below to answer the user's question. "
        "Cite papers by their number, e.g. [Paper 1]. "
        "If the answer cannot be found in the provided papers, say so.\n\n"
        f"=== RETRIEVED PAPERS ===\n{context}\n\n"
        f"=== USER QUESTION ===\n{question}\n\n"
        "=== YOUR ANSWER ===\n"
    )


def generate(prompt: str, max_new_tokens: int = 512, temperature: float = 0.7) -> str:
    """Run the loaded LLM on the prompt and return the generated answer string."""
    if _model is None or _tokenizer is None:
        raise RuntimeError("Generator not loaded. Call generator.load() first.")

    device = next(_model.parameters()).device
    try:
        messages  = [{"role": "user", "content": prompt}]
        input_ids = _tokenizer.apply_chat_template(
            messages, return_tensors="pt", add_generation_prompt=True
        ).to(device)
    except Exception:
        input_ids = _tokenizer(prompt, return_tensors="pt").input_ids.to(device)

    with torch.no_grad():
        out = _model.generate(
            input_ids,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=temperature > 0,
            pad_token_id=_tokenizer.eos_token_id,
        )

    new_tokens = out[0][input_ids.shape[-1]:]
    return _tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
