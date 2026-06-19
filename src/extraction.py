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

def extract_dates(vectorstore):
    """
    Extract all dates, deadlines, and time-bound obligations from the document.
    Absolute calendar dates are sorted chronologically; relative deadlines
    (defined by an event, not a fixed date) are listed separately since they
    can't be meaningfully sorted on a calendar.
    """
    chunks = retrieve_all_chunks(vectorstore)
    context = format_context(chunks)

    prompt = f"""Read the document excerpts below and extract every date, deadline, or time-bound obligation mentioned.

Separate them into two categories:
1. "absolute_dates" — specific calendar dates (e.g. "January 15, 2004"). Sort this list chronologically, earliest first.
2. "relative_deadlines" — deadlines defined relative to an event rather than a fixed date (e.g. "within 10 working days of termination"). These cannot be sorted on a calendar, so list them in the order they appear in the document.

For every entry in both lists, include: the date or deadline text exactly as written, a short description of what it refers to, and the page number it was found on.

Return ONLY valid JSON with this exact structure, no markdown formatting, no commentary:
{{
  "absolute_dates": [
    {{"date": "...", "description": "...", "page": ...}}
  ],
  "relative_deadlines": [
    {{"deadline": "...", "description": "...", "page": ...}}
  ]
}}

If no entries exist for a category, return an empty list for that key.

Document excerpts:
{context}
"""

    llm = get_llm()
    response = llm.invoke(prompt)
    raw = response.content.strip()

    # Same cleanup as summarize_document — models sometimes wrap JSON in ```json fences anyway
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse JSON: {e}", "raw_response": raw}


if __name__ == "__main__":
    from embeddings import load_vectorstore

    vectorstore = load_vectorstore()

    print("=== Summarize ===")
    print(json.dumps(summarize_document(vectorstore), indent=2))

    print("\n=== Extract Dates ===")
    print(json.dumps(extract_dates(vectorstore), indent=2))

