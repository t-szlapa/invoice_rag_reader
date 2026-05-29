"""Document record dataclass matching the SQLite schema."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Document:
    id: str
    filename: str
    file_path: str
    status: str
    created_at: str
