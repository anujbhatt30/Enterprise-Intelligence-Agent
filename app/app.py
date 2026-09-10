"""
Step 5: Simple Streamlit UI for the enterprise intelligence agent.

A single chat box: type a question, see which tool handled it (RAG / SQL /
ANALYSIS / REASONING) and the final answer -- no terminal commands needed
after this point.

Run with:
    streamlit run app/app.py
"""

import os
import sys
import streamlit as st

# Make Steps 1-4 importable from here
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "rag"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sql_agent"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "router"))

from router_ollama import classify, rag_answer, sql_ask, handle_reasoning
from analysis_ollama import ask as analysis_ask

st.set_page_config(page_title="Enterprise Intelligence Agent", page_icon="🧠", layout="centered")

st.title("🧠 Enterprise Intelligence Agent")
st.caption("Ask about company policies, sales data, trends, or business questions. "
           "Runs fully locally via Ollama — no API key, no cloud calls.")

CATEGORY_LABELS = {
    "RAG": "📄 Document search (RAG)",
    "SQL": "🗄️ Database query (SQL)",
    "ANALYSIS": "📊 Data analysis (SQL + Python)",
    "REASONING": "🤔 Reasoning & recommendation",
}

EXAMPLE_QUESTIONS = [
    "Summarize the company's leave policy.",
    "What were total sales in Q4 2025?",
    "Which product category grew fastest?",
    "Why did Electronics sales decline and what should management do?",
]

if "history" not in st.session_state:
    st.session_state.history = []

with st.sidebar:
    st.subheader("Try an example")
    for q in EXAMPLE_QUESTIONS:
        if st.button(q, use_container_width=True):
            st.session_state.pending_question = q

# Replay chat history
for entry in st.session_state.history:
    with st.chat_message("user"):
        st.write(entry["question"])
    with st.chat_message("assistant"):
        st.caption(CATEGORY_LABELS.get(entry["category"], entry["category"]))
        st.write(entry["answer"])


def run_query(question):
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            category = classify(question)
            st.caption(CATEGORY_LABELS.get(category, category))

            if category == "RAG":
                result = rag_answer(question)
                answer = result["answer"]
            elif category == "SQL":
                answer = sql_ask(question)
            elif category == "ANALYSIS":
                answer = analysis_ask(question)
            else:
                answer = handle_reasoning(question)

        st.write(answer)

    st.session_state.history.append({
        "question": question, "category": category, "answer": answer
    })


# Handle example button clicks
if "pending_question" in st.session_state:
    q = st.session_state.pop("pending_question")
    run_query(q)

# Main chat input
user_question = st.chat_input("Ask a question...")
if user_question:
    run_query(user_question)
