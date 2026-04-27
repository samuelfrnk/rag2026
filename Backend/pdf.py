import re
import pymupdf as fitz

def extract_pdf_text(data, max_chars = 3000):
    doc = fitz.open(stream=data, filetype="pdf")
    pages = [page.get_text("text") for page in doc]
    doc.close()
    
    text = "\n".join(pages)
    text = re.sub(r"\n{3,}", "\n\n", text)   # collapse excessive blank lines
    text = re.sub(r"[ \t]+", " ", text)       # collapse horizontal whitespace
    return text.strip()[:max_chars]