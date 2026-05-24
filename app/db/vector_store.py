"""ChromaDB client — singleton with persistent storage on disk."""
from __future__ import annotations

import chromadb

from app.config import settings

_client: chromadb.PersistentClient | None = None
_collection: chromadb.Collection | None = None

COLLECTION_NAME = "documents"


def init_chroma() -> None:
    """Initialize client and collection. Called once on application startup."""
    global _client, _collection
    settings.ensure_dirs()
    _client = chromadb.PersistentClient(path=str(settings.chroma_dir))
    _collection = _client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    print(f"[Chroma] Collection '{COLLECTION_NAME}' ready ({_collection.count()} chunks).")


def get_collection() -> chromadb.Collection:
    if _collection is None:
        raise RuntimeError("ChromaDB is not initialized. Call init_chroma() first.")
    return _collection
