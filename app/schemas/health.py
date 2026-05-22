"""Schematy Pydantic dla endpointu /health."""
from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    device: str
    openai_configured: bool
