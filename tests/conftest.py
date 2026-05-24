"""Pytest configuration — applied before any application modules are imported."""
from __future__ import annotations

import os

# chromadb uses opentelemetry-grpc with generated pb2 files incompatible
# with protobuf >= 4.x (Python C extension). Switch to pure-Python implementation.
os.environ.setdefault("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION", "python")
