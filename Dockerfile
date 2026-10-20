# Multi-stage image for GCP VM / Kubernetes (CPU embeddings only).
# Default PyPI torch pulls ~6GB CUDA libs and stalls at "unpacking" on small VMs.
FROM python:3.13.5-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.12.21 /uv /uvx /usr/local/bin/

# Dependency layer (cached until lock/manifest change)
COPY pyproject.toml uv.lock README.md ./
RUN uv venv /app/.venv \
    && uv sync --frozen --no-dev --no-install-project

# Application code + runtime data (chroma index is required at startup)
COPY app/ app/
COPY config/ config/
COPY pipeline/ pipeline/
COPY src/ src/
COPY data/ data/
COPY chroma_db/ chroma_db/
COPY main.py ./

RUN uv sync --frozen --no-dev

# --- runtime: no compilers, smaller unpack ---
FROM python:3.13.5-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    HF_HOME=/app/.cache/huggingface \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 appuser \
    && mkdir -p /app/.cache/huggingface \
    && chown -R appuser:appuser /app

COPY --from=builder --chown=appuser:appuser /app /app

USER appuser

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app/app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true"]
