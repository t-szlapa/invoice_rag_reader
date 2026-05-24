"""Semantic search over indexed documents."""
from __future__ import annotations

from app.db.vector_store import get_collection
from app.services.indexing import _get_embedding_model


def search(query: str, n_results: int = 5) -> list[dict]:
    """
    Embed the query and return the n most similar chunks from ChromaDB.

    Each result dict contains: text, score, document_id, field.
    Returns an empty list if the collection has no documents.
    """
    collection = get_collection()
    if collection.count() == 0:
        return []

    model = _get_embedding_model()
    query_embedding = model.encode([query], normalize_embeddings=True).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=min(n_results, collection.count()),
        include=["documents", "distances", "metadatas"],
    )

    hits = []
    for text, distance, metadata in zip(
        results["documents"][0],
        results["distances"][0],
        results["metadatas"][0],
    ):
        hits.append({
            "text": text,
            "score": round(1 - distance, 4),  # cosine distance -> similarity
            "document_id": metadata.get("document_id", ""),
            "field": metadata.get("field", ""),
        })

    return hits
