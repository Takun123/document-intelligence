import os
import re
import fitz  # PyMuPDF


def clean_text(text):
    """
    Basic cleanup: collapse repeated newlines/spaces that PDFs
    often produce from weird layout artifacts.
    """
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r' +', ' ', text)
    return text.strip()


def load_document(file_path):
    """
    Load a PDF and extract text page by page, with metadata.

    Returns:
        {
            "filename": str,
            "pages": int,
            "content": [{"page": 1, "text": "..."}, {"page": 2, "text": "..."}, ...]
        }
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"No file found at: {file_path}")

    doc = fitz.open(file_path)

    pages_content = []
    for page_num, page in enumerate(doc, start=1):
        raw_text = page.get_text()
        pages_content.append({"page": page_num, "text": clean_text(raw_text)})

    result = {
        "filename": os.path.basename(file_path),
        "pages": doc.page_count,
        "content": pages_content
    }

    doc.close()
    return result


if __name__ == "__main__":
    sample_path = "data/sample_docs/sample_contract.pdf"
    result = load_document(sample_path)

    print(f"Filename: {result['filename']}")
    print(f"Total pages: {result['pages']}\n")

    for page in result['content'][:3]:
        print(f"--- Page {page['page']} ---")
        print(page['text'][:500])
        print()