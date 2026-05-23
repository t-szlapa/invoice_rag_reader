"""OCR service — runs Donut inference and persists the result."""
from __future__ import annotations

from app.db.database import save_ocr_result, update_status
from app.services.donut import run_inference


def run_ocr(document_id: str, file_path: str) -> None:
    """Process a document image with Donut: queued -> processing -> completed/failed."""
    try:
        update_status(document_id, "processing")
        ocr_text, ocr_json = run_inference(file_path)
        save_ocr_result(document_id, ocr_text, ocr_json)
    except Exception as exc:
        update_status(document_id, "failed")
        print(f"[OCR] Failed for {document_id}: {exc}")
