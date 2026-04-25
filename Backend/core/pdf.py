"""
PDF text extraction — reads a PDF file and returns plain text for use as a search query.
Source: proof_of_concept.ipynb → extract_pdf_text(), pdf_to_query()
"""


def extract_text(pdf_bytes: bytes) -> str:
    """Extract all text from a PDF given its raw bytes."""
    raise NotImplementedError


def to_query(pdf_bytes: bytes, max_chars: int = 2000) -> str:
    """Extract text from a PDF and truncate to max_chars for use as a search query."""
    raise NotImplementedError
