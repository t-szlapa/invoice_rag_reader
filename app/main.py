"""
Punkt wejscia aplikacji FastAPI.

Etap 0: szkielet + /health.
Kolejne etapy dolacza routery dla dokumentow i RAG.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.routers import health


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start: upewnij sie, ze katalogi danych istnieja.
    settings.ensure_dirs()
    yield
    # Shutdown: (na razie nic do sprzatania)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.include_router(health.router)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    """Krotka informacja powitalna z odnosnikiem do dokumentacji."""
    return {"message": settings.app_name, "docs": "/docs"}
