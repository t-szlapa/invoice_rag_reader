"""Router sprawdzajacy stan aplikacji."""
from __future__ import annotations

from fastapi import APIRouter

from app.config import settings
from app.schemas.health import HealthResponse
from app.services.device import resolve_device

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Zwraca podstawowe informacje o stanie aplikacji."""
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        version=settings.app_version,
        device=resolve_device(settings.device),
        openai_configured=settings.openai_api_key is not None,
    )
