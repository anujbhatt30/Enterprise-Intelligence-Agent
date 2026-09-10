"""
Step 1b: Given a question, retrieve the most relevant chunks + their sources.
"""

import os
import pickle
from sklearn.metrics.pairwise import cosine_similarity

INDEX_PATH = os.path.join(os.path.dirname(__file__), "index.pkl")


def load_index():
    if not os.path.exists(INDEX_PATH):
        raise FileNotFoundError("No index found. Run `python rag/ingest.py` first.")
    with open(INDEX_PATH, "rb") as f:
        return pickle.load(f)


def retrieve(query, top_k=3):
    index = load_index()
    vectorizer = index["vectorizer"]
    matrix = index["matrix"]
    chunks = index["chunks"]
    metadata = index["metadata"]

    query_vec = vectorizer.transform([query])
    scores = cosine_similarity(query_vec, matrix)[0]

    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

    results = []
    for i in ranked:
        results.append({
            "text": chunks[i],
            "source": metadata[i]["source"],
            "score": round(float(scores[i]), 4),
        })
    return results


if __name__ == "__main__":
    query = "How many days of annual leave do employees get?"
    for r in retrieve(query):
        print(f"[{r['score']}] ({r['source']}) {r['text'][:120]}...")
