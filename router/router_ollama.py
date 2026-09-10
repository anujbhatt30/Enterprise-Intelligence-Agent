"""
Step 4: Router / orchestrator.

Looks at a user's question, decides which tool it needs, and calls it:
  - RAG        -> document questions (policies, handbooks)
  - SQL        -> direct factual/numeric questions ("what were total sales in Q4?")
  - ANALYSIS   -> questions needing computation on top of SQL ("which grew fastest?")
  - REASONING  -> "why" / "what should we do" questions -- pulls data via the
                  other tools first, then reasons over it

This ties together everything from Steps 1-3.
"""

import os
import sys
import ollama

# Make the other steps' modules importable from here
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "rag"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sql_agent"))

from generate_ollama import answer_question as rag_answer          # Step 1
from sql_agent_ollama import ask as sql_ask                        # Step 2
from analysis_ollama import load_quarterly_category_sales, compute_growth  # Step 3

MODEL = "qwen3.5:9b"

CATEGORIES = ["RAG", "SQL", "ANALYSIS", "REASONING"]


def classify(question):
    prompt = f"""Classify this question into exactly ONE category. Reply with ONLY
the category word, nothing else.

Categories:
- RAG: questions about company documents, policies, handbooks (e.g. "summarize the leave policy", "how many sick days do I get")
- SQL: direct factual/numeric questions answerable by a single database query (e.g. "what were total sales in Q4", "how many units did we sell")
- ANALYSIS: questions needing computation/comparison across data, like growth, trends, rankings over time (e.g. "which category grew fastest", "how did sales change this year")
- REASONING: "why" questions or requests for recommendations/advice that need interpretation, not just numbers (e.g. "why did sales decline", "what should management do")

Question: "{question}"

Category:"""

    response = ollama.chat(model=MODEL, messages=[{"role": "user", "content": prompt}])
    category = response["message"]["content"].strip().upper()

    # basic cleanup in case the model adds extra words
    for c in CATEGORIES:
        if c in category:
            return c
    return "REASONING"  # safe fallback -- reasoning can always attempt an answer


def handle_reasoning(question):
    """
    For 'why' / 'what should we do' questions: gather data from the other
    tools first, then ask the LLM to reason over it.
    """
    pivot = load_quarterly_category_sales()
    growth, first_q, last_q = compute_growth(pivot)
    table_text = growth.reset_index().to_string(index=False)

    prompt = f"""A user asked: "{question}"

Here is quarterly sales growth data by category ({first_q} vs {last_q}):

{table_text}

Based on this data, answer the user's question. If they're asking "why"
something happened, give plausible, data-grounded explanations (not wild
speculation). If they're asking what management should do, give concrete,
actionable recommendations tied to the specific numbers above.
"""
    response = ollama.chat(model=MODEL, messages=[{"role": "user", "content": prompt}])
    return response["message"]["content"]


def route(question):
    category = classify(question)
    print(f"[Router] Question classified as: {category}\n")

    if category == "RAG":
        result = rag_answer(question)
        return result["answer"]

    elif category == "SQL":
        return sql_ask(question)

    elif category == "ANALYSIS":
        # analysis_ollama.ask() already prints its own breakdown
        from analysis_ollama import ask as analysis_ask
        return analysis_ask(question)

    else:  # REASONING
        return handle_reasoning(question)


if __name__ == "__main__":
    test_questions = [
        "Summarize the company's leave policy.",
        "What were total sales in Q4 2025?",
        "Which product category grew fastest?",
        "Why did Electronics sales decline and what should management do?",
    ]

    for q in test_questions:
        print("=" * 70)
        print(f"QUESTION: {q}")
        print("=" * 70)
        answer = route(q)
        print(f"\nFINAL ANSWER:\n{answer}\n")
