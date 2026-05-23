"""OCR service — mock implementation, to be replaced with real Donut in Stage 3."""
from __future__ import annotations

import time

from app.db.database import update_status


def run_ocr(document_id: str) -> None:
    """Simulate OCR processing: queued -> processing -> completed."""
    try:
        update_status(document_id, "processing")
        time.sleep(2)
        update_status(document_id, "completed")
    except Exception:
        update_status(document_id, "failed")
