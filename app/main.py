"""Punkt wejscia aplikacji FastAPI."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.db.database import init_db
from app.routers import documents, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(documents.router)


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    """Krotka informacja powitalna z odnosnikiem do dokumentacji."""
    return {"message": settings.app_name, "docs": "/docs"}
