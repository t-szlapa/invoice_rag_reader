"""RAG answer generation using OpenAI."""
from __future__ import annotations

from app.config import settings
from app.services.search import search

SYSTEM_PROMPT = (
    "You are an assistant that answers questions strictly based on the provided document context. "
    "If the answer is not present in the context, say so clearly. "
    "Be concise and cite the relevant fields when possible."
)


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

    if not sources:
        return "No indexed documents found to answer this question.", sources

    context = "\n".join(
        f"[{i + 1}] ({s['field']}) {s['text']}" for i, s in enumerate(sources)
    )
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
