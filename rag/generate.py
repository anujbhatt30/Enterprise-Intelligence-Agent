"""
Step 1c: Combine retrieved chunks with an LLM call to produce a cited answer.

Requires an ANTHROPIC_API_KEY environment variable (or a .env file with one).
Get a key at https://console.anthropic.com/
"""

import os
from dotenv import load_dotenv
from anthropic import Anthropic
from retrieve import retrieve

load_dotenv()
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


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


def answer_question(question, top_k=3, model="claude-sonnet-4-6"):
    chunks = retrieve(question, top_k=top_k)
    prompt = build_prompt(question, chunks)

    response = client.messages.create(
        model=model,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )

    answer_text = response.content[0].text
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
