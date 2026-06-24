# tests/evaluate.py
# Phase 8 — RAGAS Evaluation
#
# Run from the project root with venv active:
#   python tests/evaluate.py
#
# Requires: pip install "ragas==0.1.21" datasets --break-system-packages

import os
import sys
import json
from pathlib import Path

# ── Make sure src/ is on the path ────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
load_dotenv()

from ingestion import load_document
from chunking import chunk_document
from embeddings import create_vectorstore
from chain import ask_document

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)

# ── 1. Load and index the sample document ────────────────────────────────────
SAMPLE_PDF = Path(__file__).parent.parent / "data" / "sample_docs" / "sample_contract.pdf"

print("Loading and indexing document...")
doc        = load_document(str(SAMPLE_PDF))
chunks     = chunk_document(doc)
vectorstore = create_vectorstore(chunks)
print(f"  Indexed {len(chunks)} chunks from {doc['pages']} pages.\n")


# ── 2. Test set — 10 question / ground-truth pairs ───────────────────────────
TEST_SET = [
    {
        "question": "What is the legal relationship between the Committee and the Contractor?",
        "ground_truth": "The Contractor is engaged as an independent contractor, not as an employee, partner, agent, or joint venturer of the Committee.",
    },
    {
        "question": "When does the engagement end?",
        "ground_truth": "The engagement continues through January 15, 2004, or earlier upon completion of the Contractor's duties, unless terminated earlier or extended by mutual agreement.",
    },
    {
        "question": "What is the Contractor's hourly rate?",
        "ground_truth": "The hourly rate is not specified — it is left blank in Schedule A to be filled in.",
    },
    {
        "question": "How can the Committee terminate this Agreement normally?",
        "ground_truth": "The Committee can terminate the Agreement by giving 10 working days' written notice to the Contractor.",
    },
    {
        "question": "Under what conditions can the Committee terminate immediately without notice?",
        "ground_truth": "If the Contractor is convicted of a crime, fails to comply with written policies, is guilty of serious misconduct, or materially breaches the Agreement.",
    },
    {
        "question": "Is the Contractor allowed to work for other clients during this engagement?",
        "ground_truth": "Yes, the Contractor is expressly free to perform services for other parties while performing services for the Committee.",
    },
    {
        "question": "Who is responsible for the Contractor's taxes?",
        "ground_truth": "The Committee is not responsible for withholding taxes on the Contractor's compensation. The Contractor bears that responsibility.",
    },
    {
        "question": "Can the Contractor assign her rights or delegate her duties to someone else?",
        "ground_truth": "No, the Contractor cannot assign rights or delegate duties without the prior written consent of the Committee.",
    },
    {
        "question": "When must the Committee pay the Contractor's invoices?",
        "ground_truth": "Payment is due within 30 days of receipt of the Contractor's monthly invoice, supported by reasonable documentation.",
    },
    {
        "question": "What happens if one clause of the Agreement is found invalid?",
        "ground_truth": "The rest of the Agreement remains in full force and effect. An invalid clause does not void the entire contract.",
    },
]


# ── 3. Run each question through the RAG pipeline ────────────────────────────
print("Running 10 questions through the RAG pipeline...")
print("-" * 60)

questions    = []
answers      = []
contexts     = []
ground_truths = []

for i, item in enumerate(TEST_SET, 1):
    q = item["question"]
    print(f"  Q{i}: {q}")

    result  = ask_document(question=q, vectorstore=vectorstore)
    answer  = result["answer"]
    sources = result.get("sources", [])

    # Retrieve the actual chunk texts for context
    # RAGAS needs the raw text chunks, not just page numbers
    retriever   = vectorstore.as_retriever(search_kwargs={"k": 4})
    docs        = retriever.get_relevant_documents(q)
    context_texts = [d.page_content for d in docs]

    print(f"     Answer: {answer[:80]}...")
    print(f"     Sources: pages {sources}")
    print()

    questions.append(q)
    answers.append(answer)
    contexts.append(context_texts)
    ground_truths.append(item["ground_truth"])

print("-" * 60)
print("All questions answered. Running RAGAS evaluation...\n")


# ── 4. Build RAGAS dataset and evaluate ──────────────────────────────────────
ragas_dataset = Dataset.from_dict({
    "question":     questions,
    "answer":       answers,
    "contexts":     contexts,
    "ground_truth": ground_truths,
})

results = evaluate(
    dataset=ragas_dataset,
    metrics=[
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
    ],
)


# ── 5. Display results ────────────────────────────────────────────────────────
scores = {
    "faithfulness":      round(results["faithfulness"],      4),
    "answer_relevancy":  round(results["answer_relevancy"],  4),
    "context_precision": round(results["context_precision"], 4),
    "context_recall":    round(results["context_recall"],    4),
}

overall = round(sum(scores.values()) / len(scores), 4)
scores["overall_average"] = overall

print("\n" + "=" * 60)
print("  RAGAS EVALUATION RESULTS — DocuMind Phase 8")
print("=" * 60)
print(f"  Faithfulness        : {scores['faithfulness']:.4f}   (target > 0.85)")
print(f"  Answer Relevancy    : {scores['answer_relevancy']:.4f}   (target > 0.80)")
print(f"  Context Precision   : {scores['context_precision']:.4f}   (target > 0.75)")
print(f"  Context Recall      : {scores['context_recall']:.4f}   (target > 0.70)")
print("-" * 60)
print(f"  Overall Average     : {overall:.4f}")
print("=" * 60)

targets = {
    "faithfulness":      0.85,
    "answer_relevancy":  0.80,
    "context_precision": 0.75,
    "context_recall":    0.70,
}

print("\nTarget check:")
for metric, target in targets.items():
    score  = scores[metric]
    status = "PASS" if score >= target else "BELOW TARGET"
    print(f"  {metric:<22}: {score:.4f}  [{status}]")


# ── 6. Save to JSON ───────────────────────────────────────────────────────────
output = {
    "model":   "gpt-4o-mini",
    "document": "sample_contract.pdf",
    "num_questions": len(TEST_SET),
    "scores":  scores,
    "targets": targets,
    "per_question": [
        {
            "question":     questions[i],
            "answer":       answers[i],
            "ground_truth": ground_truths[i],
        }
        for i in range(len(TEST_SET))
    ],
}

output_path = Path(__file__).parent / "evaluation_report.json"
with open(output_path, "w") as f:
    json.dump(output, f, indent=2)

print(f"\nFull report saved to: {output_path}")