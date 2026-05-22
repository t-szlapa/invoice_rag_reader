# OCR/VLM RAG API

REST API w FastAPI: przyjmuje obrazy dokumentow (faktur), odczytuje je modelem
**Donut**, a nastepnie pozwala wyszukiwac informacje i zadawac pytania w podejsciu
**RAG**.

Przeplyw: `obraz -> Donut (OCR/VLM) -> tekst/JSON -> embedding -> baza wektorowa -> wyszukiwanie / odpowiedz RAG`

> Status: **Etap 0** - szkielet projektu + `/health`. Kolejne etapy dodaja upload,
> przetwarzanie w tle, indeksowanie i RAG.

## Stack

- **uv** - menedzer pakietow i srodowiska
- **FastAPI + Pydantic** - API i walidacja
- **Donut** (`katanaml-org/invoices-donut-model-v1`) - odczyt dokumentow
- **sentence-transformers** - lokalne embeddingi
- **ChromaDB** - baza wektorowa (trwala na dysku)
- **SQLite** - metadane dokumentow
- **OpenAI API** - generowanie odpowiedzi w `/rag/answer`

## Wymagania

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

## Uruchomienie (lokalnie)

```bash
# 1. Instalacja zaleznosci (uv tworzy .venv automatycznie)
uv sync

# 2. (opcjonalnie) konfiguracja
cp .env.example .env   # token OpenAI mozna dodac pozniej

# 3. Start serwera
uv run uvicorn app.main:app --reload
```

API: <http://127.0.0.1:8000> · Dokumentacja (Swagger): <http://127.0.0.1:8000/docs>

## Weryfikacja Etapu 0

```bash
curl http://127.0.0.1:8000/health
```

Oczekiwana odpowiedz (200 OK):

```json
{
  "status": "ok",
  "app_name": "OCR/VLM RAG API",
  "version": "0.1.0",
  "device": "mps",
  "openai_configured": false
}
```

`device` bedzie `mps` na Apple Silicon, a `cpu` w kontenerze Docker.

## Weryfikacja Etapu 1

Poprawny upload (jpg/jpeg/png) zwraca 202 z `document_id`:

```bash
curl -s -X POST http://127.0.0.1:8000/documents/upload \
  -F "file=@faktura.jpg" | jq .
```

Oczekiwana odpowiedz (202 Accepted):

```json
{
  "document_id": "3f2a1b4c-...",
  "filename": "faktura.jpg",
  "status": "queued"
}
```

Niedozwolony format zwraca 400:

```bash
curl -s -o /dev/null -w "%{http_code}" -X POST http://127.0.0.1:8000/documents/upload \
  -F "file=@dokument.pdf"
# 400
```
