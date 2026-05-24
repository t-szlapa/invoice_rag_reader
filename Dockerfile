FROM python:3.11-slim

# install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# install dependencies first — this layer is cached unless lock file changes
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python \
    uv sync --frozen --no-dev --no-install-project

# copy application code
COPY app/ app/

# pre-download Donut model into the image so it's not re-fetched on every container start
# (~810 MB added to the image; cached as a separate layer — rebuilds only when this line changes)
RUN PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python \
    /app/.venv/bin/python -c "\
from transformers import DonutProcessor, VisionEncoderDecoderModel; \
DonutProcessor.from_pretrained('katanaml-org/invoices-donut-model-v1'); \
VisionEncoderDecoderModel.from_pretrained('katanaml-org/invoices-donut-model-v1')"

# data directory is mounted as a volume at runtime
RUN mkdir -p data/uploads data/chroma

ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
