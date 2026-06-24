# DocuMind — Business Document Intelligence System

A RAG-powered web application that lets you chat with any business document, extract structured data, and identify risks — all grounded in the document with page citations.

**Live demo:** https://document-intelligence-zdxuwgyycxz7bqsyndf7nk.streamlit.app

---

## What It Does

Upload any PDF — contract, invoice, financial report, supplier agreement — and immediately:

- **Chat with it** — ask questions in natural language, get cited answers
- **Summarize** — document type, key parties, main purpose, key points
- **Extract dates** — all deadlines and calendar dates, sorted and cited
- **Identify parties** — names, roles, obligations, and rights
- **Flag risks** — unusual clauses, missing protections, one-sided terms
- **Follow-up questions** — full conversation memory across the session

---

## Architecture

```
[PDF Upload]
     ↓
[PyMuPDF — page-by-page text extraction]
     ↓
[LangChain RecursiveCharacterTextSplitter]
  500-token chunks · 50-token overlap · page metadata preserved
     ↓
[OpenAI text-embedding-3-small]
  Each chunk → 1536-dimensional vector
     ↓
[FAISS Vector Store — local index]
  Saved to disk · no re-embedding on reload
     ↓
[User Question]
     ↓
[Retriever — top-4 semantic search]
     ↓
[ConversationalRetrievalChain]
  System prompt · retrieved chunks · conversation window (last 5 turns)
     ↓
[GPT-4o-mini — grounded answer with page citations]
     ↓
[Streamlit UI — cited response + chat history]
```

---

## Evaluation (RAGAS)

Evaluated on 10 manually curated Q&A pairs from a sample contract using [RAGAS](https://github.com/explodinggradients/ragas).

| Metric             | Score  | Target |
|--------------------|--------|--------|
| Faithfulness       | 0.75   | > 0.85 |
| Answer Relevancy   | 0.84   | > 0.80 |
| Context Precision  | 0.86   | > 0.75 |
| Context Recall     | **1.00**   | > 0.70 |
| **Overall Average**    | **0.86**   |        |

Context Recall of 1.0 means the retriever found all necessary information for every question. Faithfulness is below target — the model occasionally adds correct but unretrieved detail; a tighter system prompt is a known improvement path.

Full report: [`tests/evaluation_report.json`](tests/evaluation_report.json)

---

## Tech Stack

| Layer | Tool |
|---|---|
| PDF Parsing | PyMuPDF (`fitz`) |
| Chunking | LangChain `RecursiveCharacterTextSplitter` |
| Embeddings | OpenAI `text-embedding-3-small` |
| Vector Store | FAISS (local) |
| LLM | `gpt-4o-mini` |
| Memory | LangChain `ConversationBufferWindowMemory` |
| Evaluation | RAGAS 0.1.21 |
| UI | Streamlit + custom CSS |
| Deployment | Streamlit Cloud |

---

## Run Locally

**1. Clone the repo**
```bash
git clone https://github.com/Takun123/document-intelligence.git
cd document-intelligence
```

**2. Create and activate a virtual environment**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Add your OpenAI API key**
```bash
cp .env.example .env
# Edit .env and add your key: OPENAI_API_KEY=sk-...
```

**5. Run the app**
```bash
streamlit run src/ui.py
```

The app will open at `http://localhost:8501`. Upload any PDF and start chatting.

---

## Project Structure

```
document-intelligence/
├── src/
│   ├── ingestion.py       # PDF parsing with PyMuPDF
│   ├── chunking.py        # Token-aware text splitting
│   ├── embeddings.py      # Vector store creation and loading
│   ├── retriever.py       # Semantic search
│   ├── chain.py           # Conversational RAG chain
│   ├── extraction.py      # Structured extraction (summary, dates, parties, risks)
│   └── ui.py              # Streamlit interface
├── tests/
│   ├── evaluate.py        # RAGAS evaluation script
│   └── evaluation_report.json
├── data/
│   └── sample_docs/       # not tracked by git (see .gitignore)
├── .env.example
├── requirements.txt
└── README.md
```

---

## Key Design Decisions

**Chunking at 500 tokens with 50-token overlap** — prevents cutting sentences mid-thought across chunk boundaries while keeping chunks small enough for precise retrieval.

**Top-4 retrieval** — wide enough to capture context spread across sections, narrow enough to avoid diluting the prompt with noise.

**Windowed memory (last 5 turns)** — enables natural follow-up questions without overflowing the model's context window on long sessions.

**Hallucination prevention** — system prompt explicitly forbids the model from using outside knowledge; answers must cite the document or state the information is not available.

---

## Part of a Two-Project AI Engineering Portfolio

This is Project A of two. Project B — an Autonomous Business Research Agent using LangGraph and multi-step tool use — is in development.

---

*Built with LangChain · FAISS · OpenAI · Streamlit*