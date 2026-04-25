"""
LLM answer generator — loads the language model and generates RAG answers.
Source: proof_of_concept.ipynb → load_llm(), build_prompt(), generate_answer()
"""


def load() -> bool:
    """
    Lazily load the LLM and tokenizer into memory.
    Returns True on success, False if the model is unavailable.
    """
    raise NotImplementedError


def build_prompt(question: str, retrieved: list[dict]) -> str:
    """
    Build the RAG prompt string from the question and retrieved paper dicts.
    Each dict is expected to have 'title', 'summary', 'terms'.
    """
    raise NotImplementedError


def generate(prompt: str, max_new_tokens: int = 512, temperature: float = 0.7) -> str:
    """Run the loaded LLM on the prompt and return the generated answer string."""
    raise NotImplementedError
