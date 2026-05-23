"""SQLite database initialization and access."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from app.config import settings


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.sqlite_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they do not exist. Called once on application startup."""
    settings.ensure_dirs()
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id          TEXT PRIMARY KEY,
                filename    TEXT NOT NULL,
                file_path   TEXT NOT NULL,
                status      TEXT NOT NULL DEFAULT 'queued',
                created_at  TEXT NOT NULL
            )
        """)
        # add OCR result columns to existing databases (idempotent)
        for column, definition in [("ocr_text", "TEXT"), ("ocr_json", "TEXT")]:
            try:
                conn.execute(f"ALTER TABLE documents ADD COLUMN {column} {definition}")
            except sqlite3.OperationalError:
                pass  # column already exists
        conn.commit()


def save_ocr_result(document_id: str, ocr_text: str, ocr_json: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE documents SET status = 'completed', ocr_text = ?, ocr_json = ? WHERE id = ?",
            (ocr_text, ocr_json, document_id),
        )
        conn.commit()


def get_document(document_id: str) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM documents WHERE id = ?", (document_id,)
        ).fetchone()


def update_status(document_id: str, status: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE documents SET status = ? WHERE id = ?",
            (status, document_id),
        )
        conn.commit()
