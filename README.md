# Anime Recommender

A Streamlit application that recommends anime from the repository's synopsis dataset. It retrieves relevant records from a local Chroma vector store and uses the Groq-hosted `llama-3.1-8b-instant` model to produce recommendations.

## How it works

1. `pipeline/build_pipeline.py` reads `data/anime_with_synopsis.csv`, validates the expected `Name`, `Genres`, and `sypnopsis` columns, and writes a one-column `data/anime_updated.csv` containing combined title, overview, and genre text.
2. `src/vector_store.py` loads that processed CSV, splits its documents, embeds them with Hugging Face `all-MiniLM-L6-v2`, and persists the index in `chroma_db/` using Chroma.
3. `app/app.py` initializes `AnimeRecommendationPipeline` once per Streamlit resource cache. User preferences are passed to a LangChain retrieval QA chain, which retrieves context from Chroma and calls Groq.
4. The prompt requests exactly three numbered recommendations, with a summary and an explanation of fit, using retrieved context only.

The application expects the vector store to exist at `chroma_db/` before startup. The repository includes a Chroma database, but you can rebuild it from the checked-in CSV files as described below.

## Repository layout

```text
app/app.py                    Streamlit UI and cached pipeline initialization
config/config.py              Groq API key and model configuration
data/anime_with_synopsis.csv  Source anime dataset
data/anime_updated.csv        Processed text consumed by the vector-store builder
pipeline/build_pipeline.py    Dataset processing and vector-store build entry point
pipeline/pipeline.py          Recommendation pipeline orchestration
src/data_loader.py            CSV validation and combined-text generation
src/vector_store.py           Embedding, Chroma persistence, and loading
src/recommender.py            Groq-backed retrieval QA chain
src/prompt_template.py        Recommendation instructions and output format
src/utils/                    Logging and custom exception handling
chroma_db/                    Persisted local Chroma store
Dockerfile                    Streamlit container image definition
llmops-k8s.yaml               Kubernetes Deployment and LoadBalancer Service
pyproject.toml                Project metadata and dependency declarations
uv.lock                       Locked dependency resolution
```

`main.py` is a small placeholder that prints a greeting; it does not start the application. There is no API server or separate CLI in the current implementation.

## Requirements

- Python 3.13 or newer (declared in `pyproject.toml`)
- [uv](https://docs.astral.sh/uv/) for the setup commands below
- A Groq API key for generating recommendations
- Network access on first use to download model/dependency assets as needed

## Setup

From the repository root:

```sh
uv sync
```

Create a `.env` file in the repository root and provide the required Groq credential:

```dotenv
GROQ_API_KEY=your_groq_api_key
```

`config/config.py` loads this value with `python-dotenv`. The model name is currently fixed in code to `llama-3.1-8b-instant`; it is not read from an environment variable.

## Build or rebuild the local index

Run this from the repository root so the relative dataset paths resolve correctly:

```sh
uv run python -m pipeline.build_pipeline
```

This regenerates `data/anime_updated.csv` and builds the persisted Chroma index under `chroma_db/`. The source CSV is expected to contain `Name`, `Genres`, and the code's misspelled column name `sypnopsis`.

## Run the app

```sh
uv run streamlit run app/app.py
```

Enter anime preferences in the text field. For example, the UI suggests “light hearted anime with school settings.” Recommendations are generated when a non-empty query is entered.

## Dependencies and integrations

The project uses Streamlit for the UI; pandas for CSV processing; LangChain components for retrieval and chain orchestration; ChromaDB for local vector persistence; Hugging Face `all-MiniLM-L6-v2` for embeddings; and Groq's `llama-3.1-8b-instant` model for recommendation text. Dependencies are declared in `pyproject.toml` and locked in `uv.lock`; `requirements.txt` also lists the application dependencies.

## Container and Kubernetes files

The multi-stage `Dockerfile` installs a **CPU-only** PyTorch wheel (via `uv` + the PyTorch CPU index), copies the app and `chroma_db/`, exposes port `8501`, and starts Streamlit on `0.0.0.0:8501`. Using the default CUDA PyPI torch wheel produces a multi‑GB image that often stalls at Docker “unpacking” on small GCP VMs.

Build and run from the repository root (or use Compose on a VM):

```sh
DOCKER_BUILDKIT=1 docker build -t llmops-app:latest .
docker run --rm -p 8501:8501 --env-file .env llmops-app:latest

# GCP VM / local Compose alternative
docker compose up -d --build
```

Expect first-run downloads of the Hugging Face embedding model into the container cache (Compose mounts a named volume for this).

The checked-in `llmops-k8s.yaml` defines a one-replica Deployment and a `LoadBalancer` Service. It expects an image named `llmops-app:latest` and a Kubernetes Secret named `llmops-secrets` whose keys are provided to the container as environment variables. The manifest does not define image-building/publishing steps or create that Secret; configure those for your cluster before applying it. Ensure the image includes or otherwise has access to the `chroma_db/` data required by the app.

## Logging and errors

The application uses Python's standard logging at INFO level and wraps errors in `AnimeRecommendationException`, including the source file and line when traceback information is available. Logs are written under a generated `logs/` path relative to the current working directory; `logs/` is ignored by git.

## Tests

No test files or configured test runner are present in the repository. The documented build and run commands are the available execution paths; recommendation generation requires a valid `GROQ_API_KEY`.
