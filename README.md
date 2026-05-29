# OCR/VLM RAG API

REST API built with FastAPI: accepts invoice images, reads them with the **Donut** model,
then allows semantic search and question answering using a **RAG** approach.

Pipeline: `image → Donut (OCR/VLM) → text/JSON → embedding → vector store → search / RAG answer`

## Stack

| Layer             | Technology                                     |
| ----------------- | ---------------------------------------------- |
| API               | FastAPI + Pydantic v2                          |
| Package manager   | uv                                             |
| OCR/VLM           | Donut (`katanaml-org/invoices-donut-model-v1`) |
| Embeddings        | `sentence-transformers/all-MiniLM-L6-v2`       |
| Vector store      | ChromaDB (persistent on disk)                  |
| Metadata          | SQLite                                         |
| Answer generation | OpenAI API (optional)                          |

---

## Running locally

### Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) — `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Steps

#### Run locally

```bash
# 1. Install dependencies
uv sync

# 2. Configure environment
cp env.example .env   # fill in your tokens

# 3. Start the server (dev mode)
uv run --env-file .env uvicorn app.main:app --reload

# 4. Get the samples if needed
uv run setup/download_sample.py --samples=8
```

API: <http://127.0.0.1:8000>
Swagger UI: <http://127.0.0.1:8000/docs>

### Environment variables (`.env`)

```
HF_TOKEN=... # Hugging Face token
OPENAI_API_KEY=sk-...     # OpenAI token (optional — only needed for /rag/answer)
PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python   # workaround for chromadb/protobuf conflict
```

---

## Running with Docker

### Build the image

```bash
docker build -t ocr-rag-api .

# or with HF token to make it faster
HF_TOKEN=hf_... docker build --secret id=hf_token,env=HF_TOKEN -t ocr-rag-api .
```

> The first build may take longer than usual — it downloads the Donut model (~810 MB) and
> bakes it into an image layer. Subsequent builds (without changes to `pyproject.toml`)
> are fast thanks to layer caching.

### Run the container

```bash
docker run -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  ocr-rag-api
```

- `-v $(pwd)/data:/app/data` — SQLite and ChromaDB data survive container restarts
- `--env-file .env` — passes tokens (OPENAI_API_KEY) into the container

### Verify after startup

```bash
curl http://localhost:8000/health
```

---

## API usage examples

### Upload an invoice

```bash
curl -s -X POST http://localhost:8000/documents/upload \
  -F "file=@invoice.jpg" | jq .
# → {"document_id": "abc123", "filename": "invoice.jpg", "status": "queued"}
```

### Check OCR status

```bash
curl -s http://localhost:8000/documents/abc123 | jq .
# → {"status": "completed", "ocr_text": "...", "ocr_json": "..."}
```

### Index a document

```bash
curl -s -X POST http://localhost:8000/documents/abc123/index | jq .
# → {"chunks_indexed": 12, "indexed_at": "2024-01-15T10:00:00Z"}
```

### Semantic search

```bash
curl -s -X POST http://localhost:8000/rag/search \
  -H "Content-Type: application/json" \
  -d '{"query": "invoice number", "n_results": 3}' | jq .
```

### RAG answer (requires OPENAI_API_KEY)

```bash
curl -s -X POST http://localhost:8000/rag/answer \
  -H "Content-Type: application/json" \
  -d '{"query": "Who is the vendor?"}' | jq .
```

---

## Tests

```bash
uv run pytest
```

---

## Docker theory

### What is a Dockerfile?

A Dockerfile is a text file containing a sequence of instructions that Docker uses to
build an **image** — an immutable, ready-to-run package containing the application along
with all its dependencies, configuration, and filesystem. Each instruction (`FROM`, `RUN`,
`COPY`, `ENV`, `CMD`) describes one build step.

Relationship: `Dockerfile → (docker build) → image → (docker run) → container`

### How do image layers work?

Each instruction in a Dockerfile creates a new **layer** — an incremental filesystem diff.
Layers are:

- **immutable** — once built, a layer never changes
- **shared** — multiple images can share the same layer (e.g. `python:3.11-slim`)
- **cached** — Docker does not rebuild a layer if the instruction and its inputs have not
  changed since the last build

Example from this project:

```
Layer 1: FROM python:3.11-slim          ← base OS
Layer 2: COPY uv binary                 ← package manager
Layer 3: COPY pyproject.toml uv.lock    ← dependency specification
Layer 4: RUN uv sync                    ← ~800 MB packages (torch, transformers...)
Layer 5: COPY app/                      ← application code
Layer 6: RUN python -c "download model" ← Donut model ~810 MB
```

### Why does instruction order matter?

Docker invalidates the cache from the first changed layer downward. If you change a file
in `app/`, layer 5 is rebuilt — but layers 1–4 (dependencies, ~800 MB) stay cached.

**Bad order** (any code change rebuilds all dependencies):

```dockerfile
COPY . .           # any file change → cache miss
RUN uv sync        # ~20 min from scratch on every change
```

**Good order** (dependencies rebuild only when the lock file changes):

```dockerfile
COPY pyproject.toml uv.lock ./   # changes rarely → served from cache
RUN uv sync                       # ~20 min only when packages are updated
COPY app/ app/                    # changes often → only this layer is rebuilt
```

### What is docker context?

Docker context is the set of files sent to the Docker daemon during `docker build`.
By default it is the entire directory from which you run the command. Docker must
transfer these files (even over a local socket) before it can start building.

A large context means a slow build start and potential data leaks (e.g. `.venv` with
~800 MB of packages, or `.env` files containing secrets).

### What is `.dockerignore`?

`.dockerignore` works identically to `.gitignore` — it excludes files and directories
from the docker context. This project excludes, among others:

```
.venv/     # ~800 MB local packages — unnecessary, Docker installs its own
data/      # user data — mounted as a volume at runtime
.env       # tokens and secrets — passed via --env-file, not baked into the image
samples/   # example invoices — not needed in production
```

Without `.dockerignore`, every `docker build` would transfer gigabytes of unnecessary
files to the daemon, and tokens from `.env` could end up in image layers.

### How to optimize build time?

1. **Layer order** — things that change rarely (dependencies) before things that change
   often (application code). See above.

2. **Cache mount for the package manager** — `--mount=type=cache` stores downloaded
   packages between builds on the same machine without adding them to image layers:

   ```dockerfile
   RUN --mount=type=cache,target=/root/.cache/uv \
       uv sync --frozen
   ```

3. **`.dockerignore`** — smaller context means faster transfer to the daemon.

4. **`--frozen` in `uv sync`** — skips dependency resolution and uses exact versions
   from `uv.lock`. Faster and deterministic.

5. **Model baked into the image vs. downloaded at runtime** — in this project the Donut
   model (~810 MB) is downloaded during `docker build` and stored in an image layer.
   The container starts immediately without waiting for a download on every `docker run`.
