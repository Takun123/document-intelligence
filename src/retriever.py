def retrieve_chunks(question, vectorstore, k=4):
    """
    Finds the top-k most relevant chunks for a given question.
    Returns: list of LangChain Document objects
    """
    return vectorstore.similarity_search(question, k=k)