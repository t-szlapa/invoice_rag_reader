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
