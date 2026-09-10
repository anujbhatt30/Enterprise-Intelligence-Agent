"""
Step 1c (Ollama version): Combine retrieved chunks with a LOCAL LLM to
produce a cited answer. No API key, no cost, no internet needed at
generation time -- everything runs on your machine via Ollama.

Setup (one-time):
    1. Install Ollama: https://ollama.com
    2. Pull a model:   ollama pull llama3.1
    3. pip install ollama
"""

import ollama
from retrieve import retrieve

MODEL = "qwen3.5:9b"  # change to whatever you pulled, e.g. "mistral", "phi3"


def build_prompt(question, chunks):
    context_block = "\n\n".join(
        f"[Source: {c['source']}]\n{c['text']}" for c in chunks
    )
    return f"""You are an internal company assistant. Answer the question using ONLY
the context below. If the answer isn't in the context, say so -- do not make
anything up. Always cite the source filename(s) you used at the end of your answer.

Context:
{context_block}

Question: {question}

Answer:"""


def answer_question(question, top_k=3, model=MODEL):
    chunks = retrieve(question, top_k=top_k)
    prompt = build_prompt(question, chunks)

    response = ollama.chat(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )

    answer_text = response["message"]["content"]
    sources = sorted(set(c["source"] for c in chunks))

    return {
        "answer": answer_text,
        "sources": sources,
        "retrieved_chunks": chunks,
    }


if __name__ == "__main__":
    result = answer_question("Summarize the company's leave policy.")
    print("ANSWER:\n", result["answer"])
    print("\nSOURCES:", result["sources"])
