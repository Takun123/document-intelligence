# src/ui.py
# Phase 9 — Deployment ready (API key input added)

import streamlit as st
import tempfile
import os

st.set_page_config(
    page_title="DocuMind",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
html, body,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stAppViewBlockContainer"] {
    background-color: #F7F8FA !important;
    color: #1A1D23 !important;
}
[data-testid="stAppViewBlockContainer"] {
    padding: 0 !important;
    max-width: 100% !important;
}
[data-testid="stHorizontalBlock"] {
    gap: 0 !important;
    align-items: stretch !important;
}
[data-testid="stHorizontalBlock"] > div:first-child {
    background-color: #FFFFFF !important;
    border-right: 1px solid #E8EAED !important;
    min-height: 100vh !important;
    padding: 2rem 1.5rem !important;
    box-shadow: 2px 0 8px rgba(0,0,0,0.04) !important;
}
[data-testid="stHorizontalBlock"] > div:last-child {
    background-color: #F7F8FA !important;
    padding: 2rem 2.5rem 6rem 2.5rem !important;
}
.wordmark {
    font-size: 1.25rem;
    font-weight: 700;
    color: #1A1D23;
    letter-spacing: -0.02em;
    margin-bottom: 2px;
}
.wordmark span { color: #4F46E5; }
.wordmark-sub {
    font-size: 0.7rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #9CA3AF;
    margin-bottom: 1.75rem;
    font-weight: 500;
}
/* ── API key banner ── */
.api-banner {
    background: linear-gradient(135deg, #EEF2FF 0%, #F5F3FF 100%);
    border: 1px solid #C7D2FE;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 1.25rem;
    font-size: 0.82rem;
    color: #3730A3;
    line-height: 1.6;
}
.api-banner strong { font-weight: 600; }
[data-testid="stFileUploader"] {
    background-color: #F7F8FA !important;
    border: 1.5px dashed #D1D5DB !important;
    border-radius: 10px !important;
}
[data-testid="stFileUploader"]:hover { border-color: #4F46E5 !important; }
[data-testid="stFileUploaderDropzone"] {
    background-color: transparent !important;
    padding: 0.6rem !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] p {
    font-size: 0.78rem !important;
    color: #9CA3AF !important;
}
.doc-card {
    background: linear-gradient(135deg, #EEF2FF 0%, #F5F3FF 100%);
    border: 1px solid #C7D2FE;
    border-radius: 10px;
    padding: 12px 14px;
    margin: 12px 0 18px 0;
    font-size: 0.82rem;
}
.doc-name {
    color: #3730A3;
    font-weight: 600;
    font-size: 0.84rem;
    display: block;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-bottom: 3px;
}
.doc-meta { color: #6B7280; font-size: 0.76rem; }
.status-dot {
    display: inline-block;
    width: 6px; height: 6px;
    background-color: #10B981;
    border-radius: 50%;
    margin-right: 5px;
    vertical-align: middle;
}
.doc-card-empty {
    background-color: #F9FAFB;
    border: 1px dashed #E5E7EB;
    border-radius: 10px;
    padding: 12px 14px;
    margin: 12px 0 18px 0;
    color: #9CA3AF;
    font-size: 0.8rem;
    text-align: center;
}
.section-label {
    font-size: 0.65rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #9CA3AF;
    font-weight: 600;
    margin: 20px 0 8px 0;
}
.stButton > button {
    background-color: #FFFFFF !important;
    color: #374151 !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 8px !important;
    width: 100% !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    padding: 0.45rem 0.875rem !important;
    text-align: left !important;
    transition: all 0.15s ease !important;
    margin-bottom: 5px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
}
.stButton > button:hover:not(:disabled) {
    background-color: #EEF2FF !important;
    color: #4F46E5 !important;
    border-color: #A5B4FC !important;
    box-shadow: 0 1px 3px rgba(79,70,229,0.15) !important;
}
.stButton > button:active:not(:disabled) {
    background-color: #E0E7FF !important;
    transform: scale(0.99) !important;
}
.stButton > button:disabled {
    opacity: 0.45 !important;
    background-color: #F9FAFB !important;
    color: #D1D5DB !important;
    box-shadow: none !important;
}
.chat-header {
    font-size: 0.7rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #9CA3AF;
    font-weight: 600;
    padding-bottom: 14px;
    border-bottom: 1px solid #E8EAED;
    margin-bottom: 20px;
}
.chat-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4rem 0;
    color: #9CA3AF;
}
.chat-empty-icon { font-size: 2rem; margin-bottom: 12px; opacity: 0.4; }
.chat-empty-text { font-size: 0.88rem; color: #B0B7C3; }
.bubble-wrapper { display: flex; margin-bottom: 6px; }
.bubble-wrapper.user { justify-content: flex-end; }
.bubble-wrapper.assistant { justify-content: flex-start; }
.bubble {
    max-width: 76%;
    padding: 11px 15px;
    font-size: 0.875rem;
    line-height: 1.65;
    white-space: pre-wrap;
}
.bubble.user {
    background-color: #4F46E5;
    color: #FFFFFF;
    border-radius: 16px 16px 4px 16px;
}
.bubble.assistant {
    background-color: #FFFFFF;
    color: #1F2937;
    border: 1px solid #E8EAED;
    border-radius: 4px 16px 16px 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}
.citations { display: flex; flex-wrap: wrap; gap: 5px; margin: 5px 0 14px 6px; }
.cite-tag {
    background-color: #EEF2FF;
    color: #4338CA;
    border: 1px solid #C7D2FE;
    border-radius: 4px;
    padding: 2px 7px;
    font-size: 0.71rem;
    font-family: monospace;
    font-weight: 500;
}
[data-testid="stBottom"] {
    background-color: #FFFFFF !important;
    border-top: 1px solid #E8EAED !important;
    padding: 14px 2.5rem !important;
    box-shadow: 0 -4px 16px rgba(0,0,0,0.05) !important;
}
[data-testid="stBottom"] > div { background-color: #FFFFFF !important; }
[data-testid="stChatInput"],
[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] > div > div {
    background-color: #FFFFFF !important;
    border: none !important;
}
[data-testid="stChatInputTextArea"] {
    background-color: #F7F8FA !important;
    color: #1A1D23 !important;
    border: 1.5px solid #E5E7EB !important;
    border-radius: 12px !important;
    font-size: 0.875rem !important;
    padding: 12px 16px !important;
}
[data-testid="stChatInputTextArea"]:focus {
    border-color: #A5B4FC !important;
    outline: none !important;
    box-shadow: 0 0 0 3px rgba(165,180,252,0.25) !important;
}
[data-testid="stChatInputTextArea"]::placeholder { color: #C4C9D4 !important; }
[data-testid="stChatInputSubmitButton"] svg { fill: #4F46E5 !important; }
[data-testid="stSpinner"] p { color: #6B7280 !important; font-size: 0.82rem !important; }
[data-testid="stAlert"] {
    background-color: #EEF2FF !important;
    border-color: #C7D2FE !important;
    color: #3730A3 !important;
    font-size: 0.82rem !important;
    border-radius: 8px !important;
}
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #E5E7EB; border-radius: 3px; }
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }
</style>
""", unsafe_allow_html=True)


# ── API key gate — must happen before any OpenAI import ──────────────────────
# On Streamlit Cloud there is no .env file, so we rely on the user providing
# their key via the input below, or on the OPENAI_API_KEY secret if set by
# the app owner for a private deployment.

def get_api_key() -> str:
    """Return the active OpenAI API key, preferring env over session input."""
    return os.environ.get("OPENAI_API_KEY", st.session_state.get("api_key", ""))

if "api_key" not in st.session_state:
    st.session_state["api_key"] = os.environ.get("OPENAI_API_KEY", "")

# Show the key input only when no key is set yet
if not st.session_state["api_key"]:
    st.markdown("""
    <div style="max-width:520px; margin: 4rem auto; text-align:center;">
        <div style="font-size:1.5rem; font-weight:700; color:#1A1D23; margin-bottom:6px;">
            Docu<span style="color:#4F46E5;">Mind</span>
        </div>
        <div style="font-size:0.72rem; letter-spacing:0.1em; text-transform:uppercase;
                    color:#9CA3AF; margin-bottom:2rem;">Document Intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="background:#FFFFFF; border:1px solid #E8EAED; border-radius:12px;
                    padding:2rem; box-shadow:0 4px 24px rgba(0,0,0,0.06);">
            <div style="font-size:0.95rem; font-weight:600; color:#1A1D23; margin-bottom:6px;">
                Enter your OpenAI API key
            </div>
            <div style="font-size:0.8rem; color:#6B7280; margin-bottom:1.25rem; line-height:1.6;">
                Your key is used only for this session and never stored.
                Get one at <a href="https://platform.openai.com/api-keys"
                style="color:#4F46E5;">platform.openai.com</a>
            </div>
        </div>
        """, unsafe_allow_html=True)

        key_input = st.text_input(
            "OpenAI API Key",
            type="password",
            placeholder="sk-...",
            label_visibility="collapsed",
        )
        if st.button("Start using DocuMind", use_container_width=True):
            if key_input.startswith("sk-"):
                st.session_state["api_key"] = key_input
                os.environ["OPENAI_API_KEY"] = key_input
                st.rerun()
            else:
                st.error("That doesn't look like a valid OpenAI key. It should start with sk-")
    st.stop()

# Key is set — make sure the env var is populated for all downstream modules
os.environ["OPENAI_API_KEY"] = st.session_state["api_key"]

# Now safe to import OpenAI-dependent modules
from ingestion import load_document
from chunking import chunk_document
from embeddings import create_vectorstore
from chain import ask_document
from extraction import summarize_document, extract_dates, identify_parties, flag_risks


# ── Session state ─────────────────────────────────────────────────────────────
def init_session():
    defaults = {
        "messages": [],
        "vectorstore": None,
        "doc_info": None,
        "conversation_history": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session()


# ── Pipeline ──────────────────────────────────────────────────────────────────
def process_document(uploaded_file):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
        doc         = load_document(tmp_path)
        chunks      = chunk_document(doc)
        vectorstore = create_vectorstore(chunks)
        st.session_state.vectorstore          = vectorstore
        st.session_state.doc_info             = {"filename": uploaded_file.name, "pages": doc["pages"]}
        st.session_state.messages             = []
        st.session_state.conversation_history = []
        os.unlink(tmp_path)
        return True
    except Exception as e:
        st.error(f"Error processing document: {e}")
        return False


# ── Render message ────────────────────────────────────────────────────────────
def render_message(role: str, content: str, sources: list = None):
    st.markdown(
        f'<div class="bubble-wrapper {role}"><div class="bubble {role}">{content}</div></div>',
        unsafe_allow_html=True,
    )
    if role == "assistant" and sources:
        tags = "".join(f'<span class="cite-tag">p.{p}</span>' for p in sorted(set(sources)))
        st.markdown(f'<div class="citations">{tags}</div>', unsafe_allow_html=True)


# ── Format extraction ─────────────────────────────────────────────────────────
def format_extraction_result(result: dict) -> str:
    lines = []
    if "document_type" in result:
        lines += [f"**Type:** {result.get('document_type','—')}",
                  f"**Purpose:** {result.get('main_purpose','—')}", "", "**Key Parties:**"]
        for p in result.get("key_parties", []): lines.append(f"  • {p}")
        lines += ["", "**Key Points:**"]
        for kp in result.get("key_points", []): lines.append(f"  • {kp}")
        if result.get("deadlines"):
            lines += ["", "**Deadlines:**"]
            for d in result["deadlines"]: lines.append(f"  • {d}")
    elif "absolute_dates" in result:
        if result.get("absolute_dates"):
            lines.append("**Calendar Dates:**")
            for item in result["absolute_dates"]:
                pg = f" *(p.{item.get('page')})*" if item.get('page') else ""
                lines.append(f"  • {item.get('date','—')} — {item.get('description','—')}{pg}")
        if result.get("relative_deadlines"):
            lines += ["", "**Relative Deadlines:**"]
            for item in result["relative_deadlines"]:
                pg = f" *(p.{item.get('page')})*" if item.get('page') else ""
                lines.append(f"  • {item.get('deadline','—')} — {item.get('description','—')}{pg}")
    elif "parties" in result:
        for party in result.get("parties", []):
            lines.append(f"**{party.get('name','—')}** — {party.get('role','—')}")
            if party.get("must_do"):
                lines.append("  *Obligations:*")
                for item in party["must_do"]:
                    pg = f" *(p.{item.get('page')})*" if item.get('page') else ""
                    lines.append(f"    • {item.get('item','—')}{pg}")
            if party.get("rights"):
                lines.append("  *Rights:*")
                for item in party["rights"]:
                    pg = f" *(p.{item.get('page')})*" if item.get('page') else ""
                    lines.append(f"    • {item.get('item','—')}{pg}")
            lines.append("")
    elif "risks" in result:
        for key, label in [("missing_information","Missing Information"),
                           ("one_sided_terms","One-Sided Terms"),
                           ("missing_protection","Missing Protections")]:
            items = [r for r in result.get("risks",[]) if r.get("category") == key]
            if items:
                lines.append(f"**{label}:**")
                for item in items:
                    pg = f" *(p.{item.get('page')})*" if item.get('page') else ""
                    lines.append(f"  • {item.get('description','—')}{pg}")
                lines.append("")
    return "\n".join(lines) if lines else "No data extracted."


# ── Layout ────────────────────────────────────────────────────────────────────
left, right = st.columns([1, 3])

# ── LEFT PANEL ────────────────────────────────────────────────────────────────
with left:
    st.markdown('<div class="wordmark">Docu<span>Mind</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="wordmark-sub">Document Intelligence</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"], label_visibility="collapsed")

    if uploaded_file is not None:
        already_loaded = (
            st.session_state.doc_info is not None
            and st.session_state.doc_info["filename"] == uploaded_file.name
        )
        if not already_loaded:
            with st.spinner("Processing document..."):
                process_document(uploaded_file)

    if st.session_state.doc_info:
        info = st.session_state.doc_info
        st.markdown(f"""
        <div class="doc-card">
            <span class="doc-name">{info['filename']}</span>
            <span class="doc-meta">{info['pages']} pages &nbsp;·&nbsp; <span class="status-dot"></span>ready</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="doc-card-empty">No document loaded</div>', unsafe_allow_html=True)

    doc_ready = st.session_state.doc_info is not None

    st.markdown('<div class="section-label">Extract</div>', unsafe_allow_html=True)
    btn_summarize = st.button("📋  Summarize document", disabled=not doc_ready)
    btn_dates     = st.button("📅  Dates & deadlines",  disabled=not doc_ready)
    btn_parties   = st.button("👤  Parties involved",   disabled=not doc_ready)
    btn_risks     = st.button("⚠️  Flag risk clauses",  disabled=not doc_ready)

    st.markdown('<div class="section-label" style="margin-top:24px;">Session</div>', unsafe_allow_html=True)
    if st.button("🗑  Clear session", disabled=not doc_ready):
        for key in ["messages", "vectorstore", "doc_info", "conversation_history"]:
            st.session_state[key] = [] if key in ["messages", "conversation_history"] else None
        st.rerun()

    # Allow switching API key
    st.markdown('<div class="section-label" style="margin-top:24px;">API Key</div>', unsafe_allow_html=True)
    if st.button("🔑  Change API key"):
        st.session_state["api_key"] = ""
        os.environ.pop("OPENAI_API_KEY", None)
        st.rerun()


# ── RIGHT PANEL ───────────────────────────────────────────────────────────────
with right:
    st.markdown('<div class="chat-header">Conversation</div>', unsafe_allow_html=True)

    if not st.session_state.messages:
        st.markdown("""
        <div class="chat-empty">
            <div class="chat-empty-icon">💬</div>
            <div class="chat-empty-text">Upload a document and ask anything about it.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state.messages:
            render_message(msg["role"], msg["content"], msg.get("sources"))

    chat_status = st.empty()

    if btn_summarize:
        with chat_status.status("Summarizing document...", expanded=True):
            result = summarize_document(st.session_state.vectorstore)
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"**Document Summary**\n\n{format_extraction_result(result)}",
            "sources": [],
        })
        st.rerun()

    if btn_dates:
        with chat_status.status("Extracting dates & deadlines...", expanded=True):
            result = extract_dates(st.session_state.vectorstore)
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"**Dates & Deadlines**\n\n{format_extraction_result(result)}",
            "sources": [],
        })
        st.rerun()

    if btn_parties:
        with chat_status.status("Identifying parties...", expanded=True):
            result = identify_parties(st.session_state.vectorstore)
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"**Parties Involved**\n\n{format_extraction_result(result)}",
            "sources": [],
        })
        st.rerun()

    if btn_risks:
        with chat_status.status("Flagging risk clauses...", expanded=True):
            result = flag_risks(st.session_state.vectorstore)
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"**Risk Flags**\n\n{format_extraction_result(result)}",
            "sources": [],
        })
        st.rerun()


# ── Chat input ────────────────────────────────────────────────────────────────
placeholder = "Ask anything about the document..." if doc_ready else "Upload a document to begin."
user_input = st.chat_input(placeholder, disabled=not doc_ready)

if user_input and doc_ready:
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
    st.session_state.messages.append({"role": "assistant", "content": answer, "sources": sources})
    st.rerun()