from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from retriever import retrieve_chunks

load_dotenv()

SYSTEM_PROMPT = """You are a document analysis assistant. Answer the user's question based ONLY on the provided document excerpts below. Do not use any outside knowledge. If the answer is not found in the excerpts, say exactly: "This information is not available in the document." Always cite the page number(s) your answer comes from.

Document excerpts:
{context}"""


def get_llm():
    """
    Initializes the chat model. temperature=0 makes answers
    consistent and literal instead of creative — important
    for factual, grounded document QA.
    """
    return ChatOpenAI(model="gpt-4o-mini", temperature=0)


def format_context(chunks):
    """
    Turns retrieved chunks into a single labeled text block,
    so the model can see exactly which page each piece came from.
    """
    formatted = []
    for doc in chunks:
        page_label = doc.metadata.get("page", "unknown")
        formatted.append(f"[Page {page_label}]\n{doc.page_content}")
    return "\n\n---\n\n".join(formatted)


def ask_document(question, vectorstore, k=4):
    chunks = retrieve_chunks(question, vectorstore, k=k)
    context = format_context(chunks)
    system_message = SYSTEM_PROMPT.format(context=context)

    llm = get_llm()
    response = llm.invoke([
        {"role": "system", "content": system_message},
        {"role": "user", "content": question},
    ])

    answer = response.content
    not_found_phrase = "This information is not available in the document."

    # Only report sources when we actually found something —
    # citing pages for an answer we didn't give is misleading.
    if answer.strip() == not_found_phrase:
        sources = []
    else:
        sources = [doc.metadata.get("page", "unknown") for doc in chunks]

    return {"answer": answer, "sources": sources}


if __name__ == "__main__":
    from embeddings import load_vectorstore

    vectorstore = load_vectorstore()

    test_questions = [
        "What happens if the contractor breaches confidentiality?",
        "Who are the parties involved in this agreement?",
        "What is the termination date of this agreement?",
        "What is the penalty for late delivery of goods?",
    ]

    for q in test_questions:
        result = ask_document(q, vectorstore)
        print(f"Q: {q}")
        print(f"A: {result['answer']}")
        print(f"Sources: pages {result['sources']}")
        print()