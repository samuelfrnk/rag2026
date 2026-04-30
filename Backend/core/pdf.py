"""
PDF text extraction — reads a PDF file and returns plain text for use as a search query.
Source: proof_of_concept.ipynb → extract_pdf_text(), pdf_to_query()
"""

import re

import pymupdf as fitz


def extract_text(pdf_bytes: bytes) -> str:
    """Extract all text from a PDF given its raw bytes."""
    doc   = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = [page.get_text("text") for page in doc]
    doc.close()

    text = "\n".join(pages)
    text = re.sub(r"\n{3,}", "\n\n", text)   # collapse excessive newlines
    text = re.sub(r"[ \t]+", " ", text)       # collapse spaces/tabs
    return text.strip()


def to_query(pdf_bytes: bytes, max_chars: int = 2000) -> str:
    """Extract text from a PDF and truncate to max_chars for use as a search query."""
    return extract_text(pdf_bytes)[:max_chars]
