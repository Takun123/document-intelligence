from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from retriever import retrieve_chunks

load_dotenv()

SYSTEM_PROMPT = """You are a document analysis assistant. Answer the user's question based ONLY on the provided document excerpts below. Do not use any outside knowledge.

If you can answer the question, even partially, using the excerpts, give the best answer you can and cite the page number(s) it comes from. Only if the excerpts contain absolutely nothing relevant to the question should you respond with exactly: "This information is not available in the document." Never add that sentence after an answer you have already given — use it only as a complete, standalone response when there is no relevant information at all.

Document excerpts:
{context}"""

MAX_HISTORY = 5


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


def ask_document(question, vectorstore, chat_history=None, k=4):
    if chat_history is None:
        chat_history = []

    chunks = retrieve_chunks(question, vectorstore, k=k)
    context = format_context(chunks)
    system_message = SYSTEM_PROMPT.format(context=context)

    llm = get_llm()

    # Rebuild the full message list fresh every call — the LLM has no
    # memory of its own, so this is the only way it "remembers" anything.
    messages = [{"role": "system", "content": system_message}]

    for exchange in chat_history:
        messages.append({"role": "user", "content": exchange["question"]})
        messages.append({"role": "assistant", "content": exchange["answer"]})

    messages.append({"role": "user", "content": question})

    response = llm.invoke(messages)

    answer = response.content
    not_found_phrase = "This information is not available in the document."

    if answer.strip() == not_found_phrase:
        sources = []
    else:
        sources = [doc.metadata.get("page", "unknown") for doc in chunks]

    updated_history = chat_history + [{"question": question, "answer": answer}]
    updated_history = updated_history[-MAX_HISTORY:]  # keep only last 5 exchanges

    return {"answer": answer, "sources": sources, "chat_history": updated_history}


if __name__ == "__main__":
    from embeddings import load_vectorstore

    vectorstore = load_vectorstore()

    # This is the actual Phase 5 test from the roadmap — a real follow-up
    # conversation, not independent questions.
    test_conversation = [
    "Who are the parties involved in this agreement?",
    "Can you tell me more about their roles and responsibilities?",
    "What happens if either of them fails to meet those obligations?",
]

    history = []
    for q in test_conversation:
        result = ask_document(q, vectorstore, chat_history=history)
        history = result["chat_history"]  # carry the notebook forward
        print(f"Q: {q}")
        print(f"A: {result['answer']}")
        print(f"Sources: pages {result['sources']}")
        print()