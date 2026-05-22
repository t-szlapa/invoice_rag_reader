"""
Konfiguracja aplikacji.

Wszystkie ustawienia czytane sa ze zmiennych srodowiskowych (lub pliku .env).
Dzieki temu token OpenAI mozna dodac pozniej bez zmiany kodu, a w Dockerze
sciezki danych podmieniamy przez zmienne srodowiskowe / wolumeny.
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

    # --- Aplikacja ---
    app_name: str = "OCR/VLM RAG API"
    app_version: str = "0.1.0"

    # --- Sciezki danych (montowane jako wolumeny w Dockerze) ---
    data_dir: Path = Path("data")
    uploads_dir: Path = Path("data/uploads")
    chroma_dir: Path = Path("data/chroma")
    sqlite_path: Path = Path("data/app.db")

    # --- Urzadzenie do inferencji Donut ---
    # "auto" -> wykryj automatycznie (mps na Macu, inaczej cpu).
    # Mozna wymusic "cpu" lub "mps" przez zmienna srodowiskowa DEVICE.
    device: str = "auto"

    # --- Modele ---
    donut_model: str = "katanaml-org/invoices-donut-model-v1"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # --- OpenAI (token dodasz pozniej) ---
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    # --- Upload ---
    allowed_extensions: set[str] = {".jpg", ".jpeg", ".png"}
    max_upload_mb: int = 20

    def ensure_dirs(self) -> None:
        """Tworzy katalogi danych, jezeli nie istnieja."""
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)


settings = Settings()
