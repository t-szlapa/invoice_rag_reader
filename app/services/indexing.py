"""Document indexing: chunking + embeddings + ChromaDB storage."""
from __future__ import annotations

import json

from app.config import settings
from app.db.vector_store import get_collection

_embedding_model = None


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        print(f"[Indexing] Loading embedding model '{settings.embedding_model}'...")
        _embedding_model = SentenceTransformer(settings.embedding_model)
        print("[Indexing] Embedding model ready.")
    return _embedding_model


def _build_chunks(document_id: str, ocr_text: str, ocr_json: str) -> list[dict]:
    """
    Build a list of chunks from OCR results.

    Strategy: each JSON field becomes a separate chunk.
    A full-text chunk is also appended as general context.
    """
    chunks = []

    try:
        parsed = json.loads(ocr_json)
        for key, value in _flatten_json(parsed):
            text = f"{key}: {value}"
            chunks.append({
                "id": f"{document_id}_{key}",
                "text": text,
                "metadata": {"document_id": document_id, "field": key, "source": "json"},
            })
    except (json.JSONDecodeError, TypeError):
        pass

    if ocr_text.strip():
        chunks.append({
            "id": f"{document_id}_full_text",
            "text": ocr_text.strip(),
            "metadata": {"document_id": document_id, "field": "full_text", "source": "ocr"},
        })

    return chunks


def _flatten_json(obj: dict | list | str, prefix: str = "") -> list[tuple[str, str]]:
    """Flatten a nested JSON structure into a list of (key, value) pairs."""
    items = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            full_key = f"{prefix}.{k}" if prefix else k
            items.extend(_flatten_json(v, full_key))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            items.extend(_flatten_json(v, f"{prefix}[{i}]"))
    else:
        items.append((prefix, str(obj)))
    return items


def index_document(document_id: str, ocr_text: str, ocr_json: str) -> int:
    """
    Index a document in ChromaDB.

    Returns the number of chunks stored.
    Re-indexing an already indexed document overwrites existing chunks (upsert).
    """
    chunks = _build_chunks(document_id, ocr_text, ocr_json)
    if not chunks:
        return 0

    model = _get_embedding_model()
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts, normalize_embeddings=True).tolist()

    collection = get_collection()
    collection.upsert(
        ids=[c["id"] for c in chunks],
        documents=texts,
        embeddings=embeddings,
        metadatas=[c["metadata"] for c in chunks],
    )

    return len(chunks)
