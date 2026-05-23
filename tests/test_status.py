"""Testy weryfikacyjne Etapu 2 - statusy i BackgroundTasks."""
from __future__ import annotations

import io
import time

from fastapi.testclient import TestClient

from app.main import app

FAKE_IMAGE = b"\xff\xd8\xff\xe0" + b"\x00" * 100


def _upload(client: TestClient, filename: str = "faktura.jpg") -> str:
    resp = client.post(
        "/documents/upload",
        files={"file": (filename, io.BytesIO(FAKE_IMAGE), "image/jpeg")},
    )
    assert resp.status_code == 202
    return resp.json()["document_id"]


def test_get_status_queued():
    """Zaraz po uploadzie status to 'queued' (background task jeszcze nie ruszyl)."""
    with TestClient(app, raise_server_exceptions=True) as client:
        document_id = _upload(client)
        resp = client.get(f"/documents/{document_id}")
        assert resp.status_code == 200
        assert resp.json()["status"] in {"queued", "processing", "completed"}


def test_get_status_completed():
    """Po chwili status powinien dojsc do 'completed'."""
    with TestClient(app) as client:
        document_id = _upload(client)
        time.sleep(3)
        resp = client.get(f"/documents/{document_id}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"


def test_get_status_not_found():
    """Nieistniejace ID zwraca 404."""
    with TestClient(app) as client:
        resp = client.get("/documents/nieistniejace-id-12345")
        assert resp.status_code == 404
