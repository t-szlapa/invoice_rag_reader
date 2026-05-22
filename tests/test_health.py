"""
Test weryfikacyjny Etapu 0.

Uruchom u siebie po `uv sync`:
    uv run pytest

Test sprawdza, ze aplikacja startuje i /health zwraca 200 z poprawna struktura.
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200():
    resp = client.get("/health")
    assert resp.status_code == 200


def test_health_payload():
    data = client.get("/health").json()
    assert data["status"] == "ok"
    assert data["app_name"]
    assert data["version"]
    # device powinno byc jednym z obslugiwanych
    assert data["device"] in {"cpu", "mps", "cuda"}
    # bez tokenu w srodowisku testowym
    assert data["openai_configured"] is False


def test_root_redirects_to_docs_info():
    data = client.get("/").json()
    assert data["docs"] == "/docs"
