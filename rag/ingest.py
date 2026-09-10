"""
Step 1a: Chunk company documents and build a searchable index.

For a portfolio project, TF-IDF is a perfectly legitimate, fully-offline
retrieval baseline -- no API key needed to test it. When you're ready for
better semantic matching, swap `build_index()` to use OpenAI/Anthropic
embeddings or a local sentence-transformers model instead (see the
comment at the bottom of this file).
"""

import os
import glob
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "company_docs")
INDEX_PATH = os.path.join(os.path.dirname(__file__), "index.pkl")

CHUNK_SIZE = 500       # characters per chunk
CHUNK_OVERLAP = 100    # overlap between consecutive chunks


def load_documents():
    """Read every .txt file in data/company_docs/."""
    docs = []
    for path in glob.glob(os.path.join(DATA_DIR, "*.txt")):
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        docs.append({"source": os.path.basename(path), "text": text})
    return docs


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Simple sliding-window chunker."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end].strip())
        start += chunk_size - overlap
    return [c for c in chunks if c]


def build_index():
    docs = load_documents()
    if not docs:
        raise FileNotFoundError(f"No .txt files found in {DATA_DIR}")

    chunks = []       # list of chunk strings
    metadata = []      # parallel list of {"source": ...} for each chunk

    for doc in docs:
        for chunk in chunk_text(doc["text"]):
            chunks.append(chunk)
            metadata.append({"source": doc["source"]})

    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(chunks)

    with open(INDEX_PATH, "wb") as f:
        pickle.dump(
            {"vectorizer": vectorizer, "matrix": matrix, "chunks": chunks, "metadata": metadata},
            f,
        )

    print(f"Indexed {len(chunks)} chunks from {len(docs)} document(s) -> {INDEX_PATH}")


if __name__ == "__main__":
    build_index()

# --- Upgrading to semantic (embedding-based) search later ---
# Replace TfidfVectorizer with, e.g.:
#   from sentence_transformers import SentenceTransformer
#   model = SentenceTransformer("all-MiniLM-L6-v2")
#   embeddings = model.encode(chunks)
# ...and swap cosine_similarity in retrieve.py to compare query embeddings
# instead of TF-IDF vectors. Same overall pipeline, better semantic recall.
