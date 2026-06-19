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

def classify_clause(text):
    """
    Classify a clause as a binding obligation ('must_do') or a permission/
    protection ('rights'), based on the modal verb it contains. Done in
    plain code rather than by the LLM — keyword matching like this needs
    to be 100% consistent, and asking the model to apply the same simple
    rule by hand across a long list of clauses proved unreliable.
    """
    lowered = text.lower()

    # Negation/permission signals checked first, since "shall not"
    # contains "shall" as a substring — order matters here.
    rights_signals = ["shall not", "will not", "is not", " may ", "free to", "is entitled to"]
    must_do_signals = ["shall", "will"]

    for signal in rights_signals:
        if signal in lowered:
            return "rights"

    for signal in must_do_signals:
        if signal in lowered:
            return "must_do"

    return "must_do"  # fallback if no modal verb is detected


def identify_parties(vectorstore):
    """
    Identify every party to the document, their role, and every clause that
    applies to them. The LLM's job is now just extraction and correct
    attribution (which party a clause is actually about) — the must_do vs
    rights split happens afterward in code via classify_clause(), since
    that classification was more reliable as a keyword rule than as an
    LLM judgment call.
    """
    chunks = retrieve_all_chunks(vectorstore)
    context = format_context(chunks)

    prompt = f"""Read the document excerpts below and identify every party to this document.

Work through the document clause by clause, from beginning to end, so you don't skip anything.

For each party, include:
- "name" — their actual name if stated, or "Not specified" if the document only refers to them by role
- "role" — their role or title as described in the document
- "items" — every clause that describes something this party must do, may do, or is protected from, quoted or closely paraphrased, with the page number it was found on

Before assigning a clause to a party, confirm who the grammatical subject of that clause actually is — pay close attention to pronouns (e.g. "she"/"her" may refer to one specific party even mid-sentence) and to sentences that mention both parties at once (e.g. one party needing the other's written consent). Attribute each clause only to the party it actually describes, never to a party simply mentioned nearby.

Each clause should appear exactly once, under exactly one party.

Return ONLY valid JSON with this exact structure, no markdown formatting, no commentary:
{{
  "parties": [
    {{
      "name": "...",
      "role": "...",
      "items": [{{"item": "...", "page": ...}}]
    }}
  ]
}}

Document excerpts:
{context}
"""

    llm = get_llm()
    response = llm.invoke(prompt)
    raw = response.content.strip()

    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse JSON: {e}", "raw_response": raw}

    # Classify each extracted clause in code instead of relying on the LLM
    for party in parsed.get("parties", []):
        must_do = []
        rights = []
        for entry in party.pop("items", []):
            if classify_clause(entry["item"]) == "must_do":
                must_do.append(entry)
            else:
                rights.append(entry)
        party["must_do"] = must_do
        party["rights"] = rights

    return parsed

def flag_risks(vectorstore):
    """
    Identify potential risks, red flags, or gaps in the document: blank or
    unspecified terms, one-sided provisions, and protections that would
    normally be expected but are missing entirely. Unlike the other
    extraction features, this one requires judgment about what's NOT
    written, not just what is.
    """
    chunks = retrieve_all_chunks(vectorstore)
    context = format_context(chunks)

    prompt = f"""Read the document excerpts below and identify potential risks, red flags, or concerns for someone relying on this document.

Work through every section of the document methodically, including schedules, attachments, and signature blocks — not just the most visually obvious blanks. Less obvious gaps (e.g. an undefined scope of work, a blank effective date) matter just as much as prominent ones (e.g. a blank dollar amount).

Look specifically for three categories of risk:
1. "missing_information" — fields left blank or unspecified (e.g. missing dates, dollar amounts, names, or undefined duties/scope of work) where the missing information could cause confusion or disputes later.
2. "one_sided_terms" — provisions that grant a right, protection, or remedy to one party in a situation where the other party doesn't have an equivalent right in the same situation (e.g. one party can terminate freely but the other cannot).
3. "missing_protection" — a protection or clause you would normally expect in a document like this that is entirely absent (e.g. no dispute resolution process, no liability cap, no clearly defined scope of work).

For each risk found, include:
- "category" — one of: missing_information, one_sided_terms, missing_protection
- "description" — what the issue is and why it matters
- "page" — the page number where the issue appears, or null if the risk is the absence of something that doesn't appear anywhere in the document

Return ONLY valid JSON with this exact structure, no markdown formatting, no commentary:
{{
  "risks": [
    {{"category": "...", "description": "...", "page": ...}}
  ]
}}

Document excerpts:
{context}
"""

    llm = get_llm()
    response = llm.invoke(prompt)
    raw = response.content.strip()

    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
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

    print("\n=== Identify Parties ===")
    print(json.dumps(identify_parties(vectorstore), indent=2))

    print("\n=== Flag Risks ===")
    print(json.dumps(flag_risks(vectorstore), indent=2))
