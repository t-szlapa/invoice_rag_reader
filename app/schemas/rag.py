"""Pydantic schemas for RAG endpoints."""
from __future__ import annotations

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str
    n_results: int = Field(default=5, ge=1, le=20)


class SearchResult(BaseModel):
    text: str
    score: float
    document_id: str
    field: str


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
