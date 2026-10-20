import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HUGGING_FACE_API_KEY = os.getenv("HUGGING_FACE_API_KEY") or os.getenv("HF_TOKEN")

# Expose HF token under names sentence-transformers / huggingface_hub expect.
if HUGGING_FACE_API_KEY:
    os.environ.setdefault("HF_TOKEN", HUGGING_FACE_API_KEY)
    os.environ.setdefault("HUGGINGFACEHUB_API_TOKEN", HUGGING_FACE_API_KEY)

# Groq deprecated llama-3.1-8b-instant (shutdown 2026-08-16 for free/developer tiers).
MODEL_NAME = os.getenv("GROQ_MODEL_NAME", "openai/gpt-oss-20b")

# Must match the model used to build chroma_db/. Changing this requires a rebuild:
#   uv run python -m pipeline.build_pipeline
EMBEDDING_MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL_NAME",
    "sentence-transformers/all-MiniLM-L6-v2",
)
