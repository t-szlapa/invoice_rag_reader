"""Verification tests for Stage 4 — ChromaDB indexing.

Tests do not require the Donut model — OCR is stubbed with known data.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

FAKE_OCR_JSON = json.dumps({
    "total": "123.45",
    "date": "2024-01-15",
    "vendor": "Acme Corp",
    "invoice_no": "INV-001",
})
FAKE_OCR_TEXT = "total: 123.45 date: 2024-01-15 vendor: Acme Corp invoice_no: INV-001"

SAMPLE = Path("samples/faktura_500.jpg")


@pytest.mark.skipif(not SAMPLE.exists(), reason="Sample image not found — run setup/download_sample.py")
def test_index_returns_409_when_not_completed():
    """Indexing a document that is not yet completed returns 409."""
    with TestClient(app) as client:
        with patch("app.services.ocr.run_inference", side_effect=RuntimeError("blocked")):
            with SAMPLE.open("rb") as f:
                resp = client.post(
                    "/documents/upload",
                    files={"file": ("faktura_500.jpg", f, "image/jpeg")},
                )
        assert resp.status_code == 202
        document_id = resp.json()["document_id"]

        for _ in range(5):
            time.sleep(0.5)
            status = client.get(f"/documents/{document_id}").json()["status"]
            if status != "processing":
                break

        assert status in {"queued", "failed"}
        index_resp = client.post(f"/documents/{document_id}/index")
        assert index_resp.status_code == 409


@pytest.mark.skipif(not SAMPLE.exists(), reason="Sample image not found — run setup/download_sample.py")
def test_index_stores_chunks_and_survives_restart():
    """Successful indexing stores chunks in ChromaDB that survive a client restart."""
    with TestClient(app) as client:
        with patch("app.services.ocr.run_inference", return_value=(FAKE_OCR_TEXT, FAKE_OCR_JSON)):
            with SAMPLE.open("rb") as f:
                resp = client.post(
                    "/documents/upload",
                    files={"file": ("faktura_500.jpg", f, "image/jpeg")},
                )
        assert resp.status_code == 202
        document_id = resp.json()["document_id"]

        for _ in range(20):
            time.sleep(0.5)
            status = client.get(f"/documents/{document_id}").json()["status"]
            if status in {"completed", "failed"}:
                break

        assert status == "completed"

        index_resp = client.post(f"/documents/{document_id}/index")
        assert index_resp.status_code == 200
        data = index_resp.json()
        assert data["chunks_indexed"] > 0
        assert data["indexed_at"]

        status_data = client.get(f"/documents/{document_id}").json()
        assert status_data["indexed_at"] is not None

    # restart client — verify chunks are still in Chroma
    with TestClient(app) as client:
        from app.db.vector_store import get_collection
        collection = get_collection()
        results = collection.get(where={"document_id": document_id})
        assert len(results["ids"]) > 0, "Chunks should survive a client restart"


def test_index_returns_404_for_unknown_document():
    """Indexing a non-existent document returns 404."""
    with TestClient(app) as client:
        resp = client.post("/documents/nonexistent-id/index")
        assert resp.status_code == 404
