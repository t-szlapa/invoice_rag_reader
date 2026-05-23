"""Integration test for Stage 3 — real Donut OCR.

Requires sample images in samples/ (run: uv run setup/download_sample.py).
Skipped automatically if the sample file is missing.
"""
from __future__ import annotations

import io
import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

SAMPLE = Path("samples/faktura_500.jpg")


@pytest.mark.skipif(not SAMPLE.exists(), reason="Sample image not found — run setup/download_sample.py")
def test_ocr_completed_with_result():
    """Upload a real invoice and verify Donut returns text and JSON fields."""
    with TestClient(app) as client:
        with SAMPLE.open("rb") as f:
            resp = client.post(
                "/documents/upload",
                files={"file": ("faktura_500.jpg", f, "image/jpeg")},
            )
        assert resp.status_code == 202
        document_id = resp.json()["document_id"]

        # wait for OCR to finish (real model, up to 60s on CPU)
        for _ in range(60):
            time.sleep(2)
            status_resp = client.get(f"/documents/{document_id}")
            status = status_resp.json()["status"]
            if status in {"completed", "failed"}:
                break

        data = status_resp.json()
        assert data["status"] == "completed", f"OCR failed: {data}"
        assert data["ocr_text"], "ocr_text should not be empty"
        parsed = json.loads(data["ocr_json"])
        assert isinstance(parsed, dict), "ocr_json should be a valid JSON object"
