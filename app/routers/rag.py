"""Router for RAG endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.rag import AnswerRequest, AnswerResponse, SearchRequest, SearchResponse, SearchResult
from app.services.answer import generate_answer
from app.services.search import search

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/search", response_model=SearchResponse)
def rag_search(request: SearchRequest) -> SearchResponse:
    """Return the most relevant chunks for the given query."""
    hits = search(request.query, request.n_results)
    return SearchResponse(
        query=request.query,
        results=[SearchResult(**h) for h in hits],
    )


@router.post("/answer", response_model=AnswerResponse)
def rag_answer(request: AnswerRequest) -> AnswerResponse:
    """Generate an answer using retrieved context and OpenAI."""
    try:
        answer, sources = generate_answer(request.query, request.n_results)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return AnswerResponse(
        query=request.query,
        answer=answer,
        sources=[SearchResult(**s) for s in sources],
    )
