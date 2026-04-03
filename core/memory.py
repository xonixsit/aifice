"""
Persistent vector memory using ChromaDB.
Stores business context, past posts, leads, engagement history.
The learning agent writes here; all other agents read from here.
"""
import os
import chromadb
from chromadb.utils import embedding_functions
from config.settings import CHROMA_PERSIST_DIR, CLIENT_NAME

_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)


def _col(name: str):
    return _client.get_or_create_collection(name, embedding_function=_ef)


# ── Write ──────────────────────────────────────────────────────────────────

def remember(collection: str, doc_id: str, text: str, metadata: dict = {}):
    """Store or update a document in memory."""
    col = _col(collection)
    col.upsert(ids=[doc_id], documents=[text], metadatas=[metadata])


# ── Read ───────────────────────────────────────────────────────────────────

def recall(collection: str, query: str, n: int = 5) -> list[str]:
    """Retrieve the most relevant documents for a query."""
    col = _col(collection)
    if col.count() == 0:
        return []
    results = col.query(query_texts=[query], n_results=min(n, col.count()))
    return results["documents"][0]


def recall_all(collection: str) -> list[str]:
    """Return all documents in a collection."""
    col = _col(collection)
    if col.count() == 0:
        return []
    return col.get()["documents"]


# ── Named collections ──────────────────────────────────────────────────────
# Usage: memory.remember("business", "about", "We are a SaaS company...")
#        memory.recall("leads", "fintech startup founder")
COLLECTIONS = {
    "business":   "Core business info, tone, ICP, products",
    "posts":      "Published posts and their performance",
    "leads":      "Lead profiles and nurture stage",
    "engagement": "Comments, replies, DM history",
    "followups":  "Email threads and booking status",
}
