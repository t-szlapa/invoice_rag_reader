"""Router dla operacji na dokumentach."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

from app.config import settings
from app.schemas.document import DocumentUploadResponse
from app.services.storage import save_upload

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=202)
def upload_document(file: UploadFile) -> DocumentUploadResponse:
    """Przyjmuje obraz dokumentu (jpg/jpeg/png), zapisuje go i kolejkuje do OCR."""
    suffix = Path(file.filename).suffix.lower()
    if suffix not in settings.allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Niedozwolony format pliku '{suffix}'. Dozwolone: jpg, jpeg, png.",
        )

    doc = save_upload(file)
    return DocumentUploadResponse(
        document_id=doc.id,
        filename=doc.filename,
        status=doc.status,
    )
