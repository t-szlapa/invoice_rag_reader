"""Router for document operations."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile

from app.config import settings
from app.db.database import get_document, save_indexed_at
from app.schemas.document import DocumentStatusResponse, DocumentUploadResponse, IndexResponse
from app.services.indexing import index_document
from app.services.ocr import run_ocr
from app.services.storage import save_upload

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=202)
def upload_document(file: UploadFile, background_tasks: BackgroundTasks) -> DocumentUploadResponse:
    """Accept a document image (jpg/jpeg/png), save it and queue it for OCR."""
    suffix = Path(file.filename).suffix.lower()
    if suffix not in settings.allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{suffix}'. Allowed: jpg, jpeg, png.",
        )

    doc = save_upload(file)
    background_tasks.add_task(run_ocr, doc.id, doc.file_path)

    return DocumentUploadResponse(
        document_id=doc.id,
        filename=doc.filename,
        status=doc.status,
    )


@router.get("/{document_id}", response_model=DocumentStatusResponse)
def get_document_status(document_id: str) -> DocumentStatusResponse:
    """Return the current processing status of a document."""
    row = get_document(document_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    return DocumentStatusResponse(
        document_id=row["id"],
        filename=row["filename"],
        status=row["status"],
        created_at=row["created_at"],
        ocr_text=row["ocr_text"],
        ocr_json=row["ocr_json"],
        indexed_at=row["indexed_at"],
    )


@router.post("/{document_id}/index", response_model=IndexResponse)
def index_document_endpoint(document_id: str) -> IndexResponse:
    """Index a document in ChromaDB. Requires status 'completed'."""
    row = get_document(document_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Document not found.")

    if row["status"] != "completed":
        raise HTTPException(
            status_code=409,
            detail=f"Document is not ready for indexing (status: '{row['status']}').",
        )

    chunks_count = index_document(document_id, row["ocr_text"], row["ocr_json"])
    indexed_at = datetime.now(timezone.utc).isoformat()
    save_indexed_at(document_id, indexed_at)

    return IndexResponse(
        document_id=document_id,
        chunks_indexed=chunks_count,
        indexed_at=indexed_at,
    )
