"""Verification tests for Stage 5 — /rag/search."""
from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

FAKE_OCR_JSON = json.dumps({
    "invoice_no": "INV-001",
    "total": "123.45",
    "date": "2024-01-15",
    "vendor": "Acme Corp",
})
FAKE_OCR_TEXT = "invoice_no: INV-001 total: 123.45 date: 2024-01-15 vendor: Acme Corp"

SAMPLE = Path("samples/faktura_500.jpg")


def test_search_empty_collection_returns_empty_list():
    """Search on an empty collection returns an empty results list, not an error."""
    with patch("app.services.search.get_collection") as mock_col:
        mock_col.return_value.count.return_value = 0
        with TestClient(app) as client:
            resp = client.post("/rag/search", json={"query": "invoice number"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["results"] == []
        assert data["query"] == "invoice number"


@pytest.mark.skipif(not SAMPLE.exists(), reason="Sample image not found — run setup/download_sample.py")
def test_search_returns_chunks_from_indexed_document():
    """Query returns chunks belonging to the correct document."""
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
        assert client.post(f"/documents/{document_id}/index").status_code == 200

        resp = client.post("/rag/search", json={"query": "invoice number", "n_results": 5})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["results"]) > 0

        document_ids = {r["document_id"] for r in data["results"]}
        assert document_id in document_ids

        scores = [r["score"] for r in data["results"]]
        assert scores == sorted(scores, reverse=True), "Results should be ordered by score descending"


@pytest.mark.skipif(not SAMPLE.exists(), reason="Sample image not found — run setup/download_sample.py")
def test_search_respects_n_results():
    """n_results parameter limits the number of returned chunks."""
    with TestClient(app) as client:
        with patch("app.services.ocr.run_inference", return_value=(FAKE_OCR_TEXT, FAKE_OCR_JSON)):
            with SAMPLE.open("rb") as f:
                resp = client.post(
                    "/documents/upload",
                    files={"file": ("faktura_500.jpg", f, "image/jpeg")},
                )
        document_id = resp.json()["document_id"]

        for _ in range(20):
            time.sleep(0.5)
            status = client.get(f"/documents/{document_id}").json()["status"]
            if status in {"completed", "failed"}:
                break

        client.post(f"/documents/{document_id}/index")

        resp = client.post("/rag/search", json={"query": "total amount", "n_results": 2})
        assert resp.status_code == 200
        assert len(resp.json()["results"]) <= 2
