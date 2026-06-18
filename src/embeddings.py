from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()  # reads OPENAI_API_KEY from your .env file


def get_embedding_model():
    """
    Initializes the OpenAI embedding model.
    Automatically picks up OPENAI_API_KEY from the environment.
    """
    return OpenAIEmbeddings(model="text-embedding-3-small")


def create_vectorstore(chunks, save_path="data/faiss_index"):
    """
    Embeds a list of LangChain Document chunks and builds a FAISS index.
    Saves the index to disk so the same document never gets re-embedded.

    chunks: list of Document objects (output of chunk_document())
    Returns: a FAISS vectorstore, ready to be searched
    """
    embeddings = get_embedding_model()
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(save_path)
    return vectorstore


def load_vectorstore(save_path="data/faiss_index"):
    """
    Loads a previously saved FAISS index from disk instead of re-embedding.
    Returns: a FAISS vectorstore, ready to be searched
    """
    embeddings = get_embedding_model()
    return FAISS.load_local(
        save_path,
        embeddings,
        allow_dangerous_deserialization=True,
    )


if __name__ == "__main__":
    from ingestion import load_document
    from chunking import chunk_document

    result = load_document("data/sample_docs/sample_contract.pdf")
    chunks = chunk_document(result)

    print(f"Embedding {len(chunks)} chunks...")
    vectorstore = create_vectorstore(chunks)
    print("Vector store saved to data/faiss_index\n")

    test_question = "What happens if the contractor breaches confidentiality?"
    results = vectorstore.similarity_search(test_question, k=2)

    print(f"Test question: {test_question}\n")
    for i, doc in enumerate(results):
        print(f"--- Match {i + 1} (page {doc.metadata['page']}) ---")
        print(doc.page_content[:300])
        print()