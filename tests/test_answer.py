"""Verification tests for Stage 6 — /rag/answer."""
from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

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


def test_answer_returns_503_without_api_key():
    """Missing OPENAI_API_KEY returns 503, not a crash."""
    with patch("app.config.settings.openai_api_key", None):
        with TestClient(app) as client:
            resp = client.post("/rag/answer", json={"query": "Who is the vendor?"})
    assert resp.status_code == 503
    assert "OpenAI" in resp.json()["detail"]


@pytest.mark.skipif(not SAMPLE.exists(), reason="Sample image not found — run setup/download_sample.py")
def test_answer_returns_answer_and_sources():
    """With a stubbed OpenAI client, answer and sources are returned correctly."""
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "The vendor is Acme Corp."

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

        assert status == "completed"
        client.post(f"/documents/{document_id}/index")

        with patch("app.config.settings.openai_api_key", "sk-fake"):
            with patch("openai.OpenAI") as mock_openai:
                mock_openai.return_value.chat.completions.create.return_value = mock_response
                resp = client.post("/rag/answer", json={"query": "Who is the vendor?"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["answer"] == "The vendor is Acme Corp."
    assert isinstance(data["sources"], list)
    assert len(data["sources"]) > 0
    assert "score" in data["sources"][0]
    assert "document_id" in data["sources"][0]
