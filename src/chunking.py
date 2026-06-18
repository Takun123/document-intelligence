import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document


def count_tokens(text):
    """
    Count tokens the same way OpenAI's models do, using tiktoken.
    This makes chunk_size measure real tokens instead of raw characters.
    """
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def chunk_document(document_data, chunk_size=500, chunk_overlap=50):
    """
    Splits a document's text into overlapping chunks while preserving
    accurate page metadata, even when a chunk spans a page boundary.

    document_data: output of load_document()
        {"filename": str, "pages": int, "content": [{"page": int, "text": str}, ...]}

    Returns: list of LangChain Document objects, each with:
        - page_content: the chunk text
        - metadata: {"filename", "page" (int or "2-3" if spanning), "chunk_id"}
    """
    separator = "\n\n"

    # Step 1 — join all pages into one continuous text,
    # while recording which character range belongs to which page.
    full_text = ""
    page_ranges = []  # (page_number, start_char, end_char)

    for page in document_data["content"]:
        start = len(full_text)
        full_text += page["text"]
        end = len(full_text)
        page_ranges.append((page["page"], start, end))
        full_text += separator

    # Step 2 — split the continuous text normally, letting chunks
    # flow across page breaks wherever the natural text break falls.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=count_tokens,
    )
    raw_chunks = splitter.split_text(full_text)

    # Step 3 — map each chunk back to the page(s) it overlaps.
    documents = []
    search_from = 0

    for i, chunk_text in enumerate(raw_chunks):
        idx = full_text.find(chunk_text, max(0, search_from - 500))
        if idx == -1:
            idx = full_text.find(chunk_text)  # safety fallback

        chunk_start = idx
        chunk_end = idx + len(chunk_text)
        search_from = chunk_start + 1

        pages_covered = [
            p_num for (p_num, p_start, p_end) in page_ranges
            if not (chunk_end <= p_start or chunk_start >= p_end)
        ]

        if len(pages_covered) == 1:
            page_label = pages_covered[0]
        elif len(pages_covered) > 1:
            page_label = f"{pages_covered[0]}-{pages_covered[-1]}"
        else:
            page_label = "unknown"  # shouldn't normally trigger

        documents.append(
            Document(
                page_content=chunk_text,
                metadata={
                    "filename": document_data["filename"],
                    "page": page_label,
                    "chunk_id": i,
                },
            )
        )

    return documents


if __name__ == "__main__":
    from ingestion import load_document

    result = load_document("data/sample_docs/sample_contract.pdf")
    chunks = chunk_document(result)

    print(f"Total chunks created: {len(chunks)}\n")
    for doc in chunks[:5]:
        print(f"--- Chunk {doc.metadata['chunk_id']} (page {doc.metadata['page']}) ---")
        print(doc.page_content[:300])
        print()