import json
from retriever import retrieve_all_chunks
from chain import get_llm, format_context

SUMMARIZE_PROMPT = """You are a document analysis assistant. Based ONLY on the document excerpts below, provide a structured summary.

Return your response as valid JSON with exactly these keys:
{{
  "document_type": "what kind of document this is",
  "key_parties": ["list of parties involved"],
  "main_purpose": "one or two sentence summary of the document's purpose",
  "key_points": ["up to 5 key points from the document"],
  "deadlines": ["any deadlines or important dates mentioned, empty list if none"]
}}

Return ONLY the JSON object. No markdown formatting, no code fences, no extra text before or after it.

Document excerpts:
{context}"""


def summarize_document(vectorstore):
    chunks = retrieve_all_chunks(vectorstore)
    context = format_context(chunks)
    prompt = SUMMARIZE_PROMPT.format(context=context)

    llm = get_llm()
    response = llm.invoke([{"role": "user", "content": prompt}])
    raw = response.content.strip()

    # Peel off the markdown "sticky note" if the model added one anyway
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"error": "Failed to parse JSON", "raw_response": raw}


if __name__ == "__main__":
    from embeddings import load_vectorstore

    vectorstore = load_vectorstore()
    result = summarize_document(vectorstore)
    print(json.dumps(result, indent=2))