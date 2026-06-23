# src/ui.py
# Phase 7a — Streamlit UI: sidebar + chat with citations
# Extraction feature buttons will be wired in Phase 7b.

import streamlit as st
from pathlib import Path
import tempfile
import os

# ── Import our own modules ──────────────────────────────────────────────────
from ingestion import load_document
from chunking import chunk_document
from embeddings import create_vectorstore
from chain import ask_document
from extraction import summarize_document, extract_dates, identify_parties, flag_risks

# ── Page config — must be the very first Streamlit call ────────────────────
st.set_page_config(
    page_title="DocuMind",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──────────────────────────────────────────────────────────────
# Streamlit's default styling is generic. This overrides it to look like
# a real product. We inject raw CSS into the page using st.markdown.
st.markdown("""
<style>
/* ---- Global ---- */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #0F1117;
    color: #E8E9F0;
}

[data-testid="stSidebar"] {
    background-color: #1A1D2E;
    border-right: 1px solid #2A2D3E;
}

/* ---- Sidebar text ---- */
[data-testid="stSidebar"] * {
    color: #E8E9F0 !important;
}

/* ---- Buttons ---- */
.stButton > button {
    background-color: #1E2130;
    color: #E8E9F0;
    border: 1px solid #2A2D3E;
    border-radius: 8px;
    width: 100%;
    transition: background-color 0.2s;
}
.stButton > button:hover {
    background-color: #2A2D3E;
    border-color: #F59E0B;
    color: #F59E0B;
}

/* ---- Chat bubbles ---- */
.bubble-wrapper {
    display: flex;
    margin-bottom: 8px;
}
.bubble-wrapper.user {
    justify-content: flex-end;
}
.bubble-wrapper.assistant {
    justify-content: flex-start;
}
.bubble {
    max-width: 75%;
    padding: 12px 16px;
    border-radius: 12px;
    font-size: 0.95rem;
    line-height: 1.6;
    white-space: pre-wrap;
}
.bubble.user {
    background-color: #2A2D3E;
    color: #E8E9F0;
    border-bottom-right-radius: 2px;
}
.bubble.assistant {
    background-color: #1E2130;
    color: #E8E9F0;
    border-bottom-left-radius: 2px;
}

/* ---- Citation badges ---- */
.citations {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 8px;
    margin-left: 4px;
}
.badge {
    background-color: #2A1F00;
    color: #F59E0B;
    border: 1px solid #F59E0B44;
    border-radius: 999px;
    padding: 2px 10px;
    font-size: 0.78rem;
    font-weight: 500;
}

/* ---- Status indicator ---- */
.status-ready {
    color: #34D399;
    font-weight: 600;
    font-size: 0.85rem;
}
.status-processing {
    color: #F59E0B;
    font-weight: 600;
    font-size: 0.85rem;
}

/* ---- Doc info card ---- */
.doc-card {
    background-color: #1E2130;
    border: 1px solid #2A2D3E;
    border-radius: 10px;
    padding: 12px 14px;
    margin: 10px 0;
    font-size: 0.88rem;
    line-height: 1.8;
}
}

/* ── Hide Streamlit branding ── */
#MainMenu, footer, header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ── Session state initialisation ────────────────────────────────────────────
# These keys are checked every rerun. If they don't exist yet, create them.
# This is how we persist data across reruns without using global variables.
def init_session():
    defaults = {
        "messages": [],          # list of {"role": "user"|"assistant", "content": str, "sources": list}
        "vectorstore": None,     # FAISS index, ready to query
        "doc_info": None,        # {"filename": str, "pages": int}
        "conversation_history": [],  # passed into ask_document() for memory
        "processing": False,     # True while pipeline is running
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session()


# ── Helper: run the full ingestion pipeline ─────────────────────────────────
def process_document(uploaded_file):
    """
    Takes a Streamlit UploadedFile object.
    Saves it to a temp file, runs the full pipeline, stores the
    vectorstore and doc info in session_state.
    Returns True on success, False on error.
    """
    try:
        # Streamlit gives us a file-like object, not a path.
        # PyMuPDF needs a real file path. We write to a temp file.
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        # Step 1 — parse PDF
        doc = load_document(tmp_path)

        # Step 2 — chunk
        chunks = chunk_document(doc)

        # Step 3 — embed + build vectorstore (this is the slow step, ~5-15s)
        vectorstore = create_vectorstore(chunks)

        # Save results to session
        st.session_state.vectorstore = vectorstore
        st.session_state.doc_info = {
            "filename": uploaded_file.name,
            "pages": doc["pages"],
        }
        st.session_state.messages = []
        st.session_state.conversation_history = []

        # Clean up temp file
        os.unlink(tmp_path)
        return True

    except Exception as e:
        st.error(f"Error processing document: {e}")
        return False


# ── Helper: render a single message bubble ──────────────────────────────────
def render_message(role: str, content: str, sources: list = None):
    """
    Renders one chat message as a styled HTML bubble.
    If role is 'assistant' and sources is a non-empty list, renders
    citation badges below the bubble.
    """
    bubble_html = f"""
    <div class="bubble-wrapper {role}">
        <div class="bubble {role}">{content}</div>
    </div>
    """
    st.markdown(bubble_html, unsafe_allow_html=True)

    # Citation badges — only for assistant messages with sources
    if role == "assistant" and sources:
        # Clean up: remove duplicates, sort, format as "Page N"
        clean_sources = sorted(set(sources))
        badges = "".join(
            f'<span class="badge">Page {p}</span>' for p in clean_sources
        )
        st.markdown(
            f'<div class="citations">{badges}</div>',
            unsafe_allow_html=True
        )
def format_extraction_result(result: dict) -> str:
    """
    Converts extraction result dicts into clean, readable text.
    Different layout per feature type, detected by the keys present.
    """
    lines = []

    # ── Summarize
    if "document_type" in result:
        lines.append(f"**Type:** {result.get('document_type', '—')}")
        lines.append(f"**Purpose:** {result.get('main_purpose', '—')}")
        lines.append("")
        lines.append("**Key Parties:**")
        for p in result.get("key_parties", []):
            lines.append(f"  • {p}")
        lines.append("")
        lines.append("**Key Points:**")
        for kp in result.get("key_points", []):
            lines.append(f"  • {kp}")
        if result.get("deadlines"):
            lines.append("")
            lines.append("**Deadlines mentioned:**")
            for d in result["deadlines"]:
                lines.append(f"  • {d}")

    # ── Extract Dates
    elif "absolute_dates" in result:
        if result.get("absolute_dates"):
            lines.append("**Calendar Dates:**")
            for item in result["absolute_dates"]:
                page = f"  *(Page {item.get('page', '?')})*" if item.get('page') else ""
                lines.append(f"  • {item.get('date', '—')} — {item.get('description', '—')}{page}")
        if result.get("relative_deadlines"):
            lines.append("")
            lines.append("**Relative Deadlines:**")
            for item in result["relative_deadlines"]:
                page = f"  *(Page {item.get('page', '?')})*" if item.get('page') else ""
                lines.append(f"  • {item.get('deadline', '—')} — {item.get('description', '—')}{page}")

    # ── Identify Parties
    elif "parties" in result:
        for party in result.get("parties", []):
            lines.append(f"**{party.get('name', '—')}** — {party.get('role', '—')}")
            if party.get("must_do"):
                lines.append("  *Obligations:*")
                for item in party["must_do"]:
                    page = f" *(Page {item.get('page', '?')})*" if item.get('page') else ""
                    lines.append(f"    • {item.get('item', '—')}{page}")
            if party.get("rights"):
                lines.append("  *Rights:*")
                for item in party["rights"]:
                    page = f" *(Page {item.get('page', '?')})*" if item.get('page') else ""
                    lines.append(f"    • {item.get('item', '—')}{page}")
            lines.append("")

    # ── Flag Risks
    elif "risks" in result:
        categories = {
            "missing_information": "⚠️ Missing Information",
            "one_sided_terms":     "⚖️ One-Sided Terms",
            "missing_protection":  "🛡️ Missing Protections",
        }
        for key, label in categories.items():
            items = [r for r in result.get("risks", []) if r.get("category") == key]
            if items:
                lines.append(f"**{label}:**")
                for item in items:
                    page = f" *(Page {item.get('page')})*" if item.get('page') else ""
                    lines.append(f"  • {item.get('description', '—')}{page}")
                lines.append("")

    return "\n".join(lines) if lines else "No data extracted."

# ── MAIN LAYOUT — two columns instead of collapsible sidebar ────────────────
left, right = st.columns([1, 3])

# ── LEFT COLUMN (was sidebar) ───────────────────────────────────────────────
with left:
    st.markdown("## 📄 DocuMind")
    st.markdown("*Business document intelligence*")
    st.divider()

    uploaded_file = st.file_uploader(
        "Upload a PDF document",
        type=["pdf"],
        label_visibility="collapsed",
    )

    if uploaded_file is not None:
        already_loaded = (
            st.session_state.doc_info is not None
            and st.session_state.doc_info["filename"] == uploaded_file.name
        )
        if not already_loaded:
            with st.spinner("Analysing document..."):
                success = process_document(uploaded_file)
            if success:
                st.success("Document ready.")

    if st.session_state.doc_info:
        info = st.session_state.doc_info
        st.markdown(f"""
        <div class="doc-card">
            <b>📋 {info['filename']}</b><br>
            Pages: {info['pages']}<br>
            <span class="status-ready">● Ready</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="doc-card">
            No document loaded.<br>
            <span class="status-processing">Upload a PDF to begin.</span>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    st.markdown("**Extract from document**")
    st.caption("Available once a document is loaded.")

    btn_summarize = st.button("📋 Summarize", disabled=st.session_state.doc_info is None)
btn_dates     = st.button("📅 Dates",     disabled=st.session_state.doc_info is None)
btn_parties   = st.button("👥 Parties",   disabled=st.session_state.doc_info is None)
btn_risks     = st.button("⚠️ Risks",     disabled=st.session_state.doc_info is None)

# ── Handle extraction button clicks
if btn_summarize:
    with st.spinner("Summarizing..."):
        result = summarize_document(st.session_state.vectorstore)
    msg = f"**📋 Document Summary**\n\n{format_extraction_result(result)}"
    st.session_state.messages.append({"role": "assistant", "content": msg, "sources": []})
    st.rerun()

if btn_dates:
    with st.spinner("Extracting dates..."):
        result = extract_dates(st.session_state.vectorstore)
    msg = f"**📅 Dates & Deadlines**\n\n{format_extraction_result(result)}"
    st.session_state.messages.append({"role": "assistant", "content": msg, "sources": []})
    st.rerun()

if btn_parties:
    with st.spinner("Identifying parties..."):
        result = identify_parties(st.session_state.vectorstore)
    msg = f"**👥 Parties Involved**\n\n{format_extraction_result(result)}"
    st.session_state.messages.append({"role": "assistant", "content": msg, "sources": []})
    st.rerun()

if btn_risks:
    with st.spinner("Flagging risks..."):
        result = flag_risks(st.session_state.vectorstore)
    msg = f"**⚠️ Risk Flags**\n\n{format_extraction_result(result)}"
    st.session_state.messages.append({"role": "assistant", "content": msg, "sources": []})
    st.rerun()

    st.divider()

    if st.button("🗑 Clear session", disabled=st.session_state.doc_info is None):
        for key in ["messages", "vectorstore", "doc_info", "conversation_history"]:
            st.session_state[key] = [] if key in ["messages", "conversation_history"] else None
        st.rerun()

# ── RIGHT COLUMN (main chat area) ───────────────────────────────────────────
with right:
    st.markdown("### Chat with your document")

    for msg in st.session_state.messages:
        render_message(msg["role"], msg["content"], msg.get("sources"))

    doc_ready = st.session_state.doc_info is not None
    placeholder = "Ask anything about the document..." if doc_ready else "Upload a document to begin."

    user_input = st.chat_input(placeholder, disabled=not doc_ready)

    if user_input and doc_ready:
        render_message("user", user_input)
        st.session_state.messages.append({"role": "user", "content": user_input, "sources": []})

        with st.spinner("Thinking..."):
            result = ask_document(
                question=user_input,
                vectorstore=st.session_state.vectorstore,
                chat_history=st.session_state.conversation_history,
)

        answer  = result["answer"]
        sources = result.get("sources", [])
        st.session_state.conversation_history = result.get("conversation_history", [])

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer,
            "sources": sources,
        })
        render_message("assistant", answer, sources)