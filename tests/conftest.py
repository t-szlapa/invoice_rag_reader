"""Pytest configuration — applied before any application modules are imported."""
from __future__ import annotations

import os
import tempfile

import pytest

# chromadb uses opentelemetry-grpc with generated pb2 files incompatible
# with protobuf >= 4.x (Python C extension). Switch to pure-Python implementation.
os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")


@pytest.fixture(autouse=True)
def isolated_chroma(tmp_path, monkeypatch):
    """Redirect ChromaDB and SQLite to a temp directory for each test.

    Prevents state from previous test runs leaking into assertions.
    """
    import app.config as config_module
    import app.db.vector_store as vs_module

    monkeypatch.setattr(config_module.settings, "chroma_dir", tmp_path / "chroma")
    monkeypatch.setattr(config_module.settings, "sqlite_path", tmp_path / "app.db")
    monkeypatch.setattr(config_module.settings, "uploads_dir", tmp_path / "uploads")
    config_module.settings.ensure_dirs()

    from app.db.database import init_db
    init_db()

    # reset singletons so the next TestClient lifespan re-initializes them
    vs_module._client = None
    vs_module._collection = None

    yield

    vs_module._client = None
    vs_module._collection = None
