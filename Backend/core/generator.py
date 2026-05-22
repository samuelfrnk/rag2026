"""
LLM answer generator — loads the language model and generates RAG answers.
Source: proof_of_concept.ipynb → load_llm(), build_prompt(), generate_answer()
"""

import torch
from config import CFG

MODEL_NAME = CFG["llm_model"]

_tokenizer = None
_model     = None


def load() -> bool:
    """
    Lazily load the LLM and tokenizer into memory.
    - CUDA available: 4-bit quantized on GPU (fits in 4 GB VRAM)
    - CPU only:       float32 on CPU (slow but functional for testing)
    Returns True on success, False if the model is unavailable.
    """
    global _tokenizer, _model
    if _model is not None:
        return True
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        use_gpu = torch.cuda.is_available()
        print(f"Loading LLM: {MODEL_NAME} ({'4-bit GPU' if use_gpu else 'float32 CPU'}) ...")

        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

        if use_gpu and CFG.get("llm_load_in_4bit", False):
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
            )
            _model = AutoModelForCausalLM.from_pretrained(
                MODEL_NAME,
                quantization_config=bnb_config,
                device_map="auto",
            )
        else:
            # CPU fallback — no quantization, float32
            _model = AutoModelForCausalLM.from_pretrained(
                MODEL_NAME,
                dtype=torch.float32,
            )

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


def generate(prompt: str, max_new_tokens: int = CFG["llm_max_tokens"], temperature: float = CFG["llm_temperature"]) -> str:
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
            attention_mask = torch.ones_like(input_ids),
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=temperature > 0,
            pad_token_id=_tokenizer.eos_token_id,
        )

    new_tokens = out[0][input_ids.shape[-1]:]
    return _tokenizer.decode(new_tokens, skip_special_tokens=True).strip()


def generate_chat(messages: list, max_new_tokens: int = CFG["llm_max_tokens"], temperature: float = CFG["llm_temperature"]) -> str:
    """Run the LLM on a full messages list (system/user/assistant turns) for multi-turn chat."""
    if _model is None or _tokenizer is None:
        raise RuntimeError("Generator not loaded. Call generator.load() first.")

    device = next(_model.parameters()).device
    try:
        input_ids = _tokenizer.apply_chat_template(
            messages, return_tensors="pt", add_generation_prompt=True
        )
        if hasattr(input_ids, "input_ids"):
            input_ids = input_ids.input_ids
        input_ids = input_ids.to(device)
    except Exception:
        flat = "\n".join(
            f"{m['role'].capitalize()}: {m['content']}" for m in messages
        ) + "\nAssistant:"
        input_ids = _tokenizer(flat, return_tensors="pt").input_ids.to(device)

    with torch.no_grad():
        out = _model.generate(
            input_ids,
            attention_mask = torch.ones_like(input_ids),
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=temperature > 0,
            pad_token_id=_tokenizer.eos_token_id,
        )

    new_tokens = out[0][input_ids.shape[-1]:]
    return _tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
