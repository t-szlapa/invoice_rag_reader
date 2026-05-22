"""Zapis plikow na dysk i operacje na rekordach dokumentow w SQLite."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import UploadFile

from app.config import settings
from app.db.database import get_connection
from app.models.document import Document


def save_upload(file: UploadFile) -> Document:
    """Zapisuje plik na dysk i wstawia rekord do SQLite ze statusem 'queued'."""
    suffix = Path(file.filename).suffix.lower()
    document_id = str(uuid.uuid4())
    file_path = settings.uploads_dir / f"{document_id}{suffix}"

    contents = file.file.read()
    file_path.write_bytes(contents)

    created_at = datetime.now(timezone.utc).isoformat()

    with get_connection() as conn:
        conn.execute(
            "INSERT INTO documents (id, filename, file_path, status, created_at) "
            "VALUES (?, ?, ?, 'queued', ?)",
            (document_id, file.filename, str(file_path), created_at),
        )
        conn.commit()

    return Document(
        id=document_id,
        filename=file.filename,
        file_path=str(file_path),
        status="queued",
        created_at=created_at,
    )
