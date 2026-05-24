"""Router for RAG endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from app.schemas.rag import SearchRequest, SearchResponse, SearchResult
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
