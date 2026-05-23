"""FastAPI application entry point."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.db.database import init_db
from app.routers import documents, health
from app.services.donut import load_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    load_model()
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
    """Brief welcome message with a link to the API docs."""
    return {"message": settings.app_name, "docs": "/docs"}
