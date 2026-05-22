"""Schematy Pydantic dla endpointow dokumentow."""
from __future__ import annotations

from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
