"""Pydantic schemas for document endpoints."""
from __future__ import annotations

from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str


class DocumentStatusResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    created_at: str
    ocr_text: str | None = None
    ocr_json: str | None = None
    indexed_at: str | None = None


class IndexResponse(BaseModel):
    document_id: str
    chunks_indexed: int
    indexed_at: str
