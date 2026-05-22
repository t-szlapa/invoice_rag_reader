"""Testy weryfikacyjne Etapu 1 - upload dokumentow."""
from __future__ import annotations

import io
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)

FAKE_IMAGE = b"\xff\xd8\xff\xe0" + b"\x00" * 100  # minimalny naglowek JPEG


def _upload(filename: str, content: bytes = FAKE_IMAGE) -> object:
    return client.post(
        "/documents/upload",
        files={"file": (filename, io.BytesIO(content), "image/jpeg")},
    )


def test_upload_returns_202():
    resp = _upload("faktura.jpg")
    assert resp.status_code == 202


def test_upload_payload():
    resp = _upload("faktura.png")
    data = resp.json()
    assert "document_id" in data
    assert data["status"] == "queued"
    assert data["filename"] == "faktura.png"


def test_upload_invalid_format_returns_400():
    resp = _upload("dokument.pdf")
    assert resp.status_code == 400


def test_upload_record_survives_restart():
    """Rekord zapisany w SQLite jest dostepny po ponownym polaczeniu z baza."""
    resp = _upload("faktura_restart.jpg")
    document_id = resp.json()["document_id"]

    with sqlite3.connect(settings.sqlite_path) as conn:
        row = conn.execute(
            "SELECT id, status FROM documents WHERE id = ?", (document_id,)
        ).fetchone()

    assert row is not None
    assert row[0] == document_id
    assert row[1] == "queued"
