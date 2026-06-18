def retrieve_chunks(question, vectorstore, k=4):
    """
    Finds the top-k most relevant chunks for a given question.
    Returns: list of LangChain Document objects
    """
    return vectorstore.similarity_search(question, k=k)


def retrieve_all_chunks(vectorstore):
    """
    Returns every chunk stored in the vectorstore, with no filtering.

    Used for whole-document tasks (summarizing, extracting all dates,
    flagging risks) where similarity search doesn't make sense — there's
    no single topic to search for, so the model needs to see everything.
    """
    return list(vectorstore.docstore._dict.values())


if __name__ == "__main__":
    from embeddings import load_vectorstore

    vectorstore = load_vectorstore()
    chunks = retrieve_all_chunks(vectorstore)

    print(f"Total chunks retrieved: {len(chunks)}")
    for c in chunks:
        print(f"Page: {c.metadata.get('page')}")