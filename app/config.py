"""
Application configuration.

All settings are read from environment variables (or a .env file).
This allows the OpenAI token to be added later without code changes,
and data paths to be overridden via environment variables / Docker volumes.
"""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "OCR/VLM RAG API"
    app_version: str = "0.1.0"

    # --- Data paths (mounted as Docker volumes) ---
    data_dir: Path = Path("data")
    uploads_dir: Path = Path("data/uploads")
    chroma_dir: Path = Path("data/chroma")
    sqlite_path: Path = Path("data/app.db")

    # --- Donut inference device ---
    # "auto" -> detect automatically (MPS on Mac, otherwise CPU).
    # Can be forced to "cpu" or "mps" via the DEVICE environment variable.
    device: str = "auto"

    # --- Models ---
    donut_model: str = "katanaml-org/invoices-donut-model-v1"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # --- OpenAI (token added later) ---
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    # --- Hugging Face ---
    hf_token: str | None = None

    # --- Upload ---
    allowed_extensions: set[str] = {".jpg", ".jpeg", ".png"}
    max_upload_mb: int = 20

    def ensure_dirs(self) -> None:
        """Create data directories if they do not exist."""
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)


settings = Settings()
