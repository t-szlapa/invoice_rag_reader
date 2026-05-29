"""RAG answer generation using OpenAI."""
from __future__ import annotations

from app.config import settings
from app.db.vector_store import get_collection
from app.services.search import search

SYSTEM_PROMPT = (
    "You are an assistant that answers questions strictly based on the provided document context. "
    "If the answer is not present in the context, say so clearly. "
    "Be concise and cite the relevant fields when possible."
)


def _fetch_full_texts(document_ids: list[str]) -> dict[str, str]:
    """Fetch the full_text chunk for each document from ChromaDB."""
    collection = get_collection()
    full_texts: dict[str, str] = {}
    for doc_id in document_ids:
        result = collection.get(
            where={"$and": [{"document_id": doc_id}, {"field": "full_text"}]},
            include=["documents"],
        )
        if result["documents"]:
            full_texts[doc_id] = result["documents"][0]
    return full_texts


def _build_context(sources: list[dict]) -> str:
    """
    Build context grouped by document.

    Each document is represented by its full invoice text, with matched field names
    listed as a hint so the model knows why the document was retrieved.
    """
    # group matched fields by document
    doc_fields: dict[str, list[str]] = {}
    for s in sources:
        doc_id = s["document_id"]
        doc_fields.setdefault(doc_id, [])
        if s["field"] != "full_text":
            doc_fields[doc_id].append(s["field"])

    full_texts = _fetch_full_texts(list(doc_fields.keys()))

    parts = []
    for i, (doc_id, fields) in enumerate(doc_fields.items(), start=1):
        text = full_texts.get(doc_id, "(full text not available)")
        hint = f"Matched fields: {', '.join(fields)}" if fields else "Matched: full text"
        parts.append(f"Document {i} (id: {doc_id}):\n{hint}\n{text}")

    return "\n\n---\n\n".join(parts)


def generate_answer(query: str, n_results: int = 5) -> tuple[str, list[dict]]:
    """
    Search for relevant chunks and generate an answer via OpenAI.

    Returns (answer, sources) where sources is the list of chunks used as context.
    Raises RuntimeError if OPENAI_API_KEY is not configured.
    """
    if not settings.openai_api_key:
        raise RuntimeError("OpenAI API key is not configured.")

    from openai import OpenAI

    sources = search(query, n_results)


    context = _build_context(sources)

    print(context)

    user_message = f"Context:\n{context}\n\nQuestion: {query}"

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0,
    )

    answer = response.choices[0].message.content.strip()
    return answer, sources
