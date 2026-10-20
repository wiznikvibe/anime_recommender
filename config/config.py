import os
from dotenv import load_dotenv

load_dotenv()


def _env(name: str, default: str | None = None) -> str | None:
    """Read env var; treat missing/blank as unset so defaults always win."""
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return value.strip()


GROQ_API_KEY = _env("GROQ_API_KEY")
HUGGING_FACE_API_KEY = _env("HUGGING_FACE_API_KEY") or _env("HF_TOKEN")

# Expose HF token under names sentence-transformers / huggingface_hub expect.
if HUGGING_FACE_API_KEY:
    os.environ.setdefault("HF_TOKEN", HUGGING_FACE_API_KEY)
    os.environ.setdefault("HUGGINGFACEHUB_API_TOKEN", HUGGING_FACE_API_KEY)

# Groq deprecated llama-3.1-8b-instant (shutdown 2026-08-16 for free/developer tiers).
MODEL_NAME = _env("GROQ_MODEL_NAME", "openai/gpt-oss-20b")

# Must match the model used to build chroma_db/. Changing this requires a rebuild:
#   uv run python -m pipeline.build_pipeline
EMBEDDING_MODEL_NAME = _env(
    "EMBEDDING_MODEL_NAME",
    "sentence-transformers/all-MiniLM-L6-v2",
)
