# AGENTS.md — Anime Recommender

Guidance for humans and coding agents working in this repository. Contents are based on inspection of source, manifests, and config as of the documentation pass. Items that could not be verified are called out explicitly.

---

## 1. Project purpose and core functionality

**Purpose:** A Streamlit app that recommends anime from a local synopsis dataset. It retrieves relevant records from a persisted Chroma vector store and uses Groq-hosted `llama-3.1-8b-instant` to generate recommendation text.

**Core flow:**

1. **Offline build** (`pipeline/build_pipeline.py`): Read `data/anime_with_synopsis.csv`, validate columns `Name`, `Genres`, and `sypnopsis` (spelling as in the CSV/code), write combined text to `data/anime_updated.csv`, embed with Hugging Face `all-MiniLM-L6-v2`, persist Chroma under `chroma_db/`.
2. **Runtime** (`app/app.py`): Cache-initialize `AnimeRecommendationPipeline`, take a free-text preference query, run a LangChain `RetrievalQA` chain against the local Chroma retriever and Groq LLM, display the result.

**Not part of the app:** `main.py` only prints a greeting; it does not start Streamlit or the pipeline. There is no separate HTTP API or CLI beyond the Streamlit entrypoint and the build module.

---

## 2. Technology stack and dependencies

| Area | Verified choice |
|------|-----------------|
| Language | Python `>=3.13` (`pyproject.toml`) |
| Package / lock | `uv` + `uv.lock`; hatchling build backend |
| UI | Streamlit |
| Data | pandas; CSV under `data/` |
| RAG / orchestration | LangChain ecosystem (`langchain`, `langchain-community`, `langchain-groq`, `langchain-huggingface`, `langchain-text-splitters`) |
| Vector store | ChromaDB (`langchain_community.vectorstores.Chroma`) |
| Embeddings | `sentence-transformers` via `HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")` |
| LLM | Groq `ChatGroq`, model `llama-3.1-8b-instant` (hardcoded in `config/config.py`) |
| Config | `python-dotenv`; `GROQ_API_KEY` from environment |
| Containers / K8s | `Dockerfile` (Python 3.13.5-slim + uv); `llmops-k8s.yaml` |

**Declared direct dependencies** (`pyproject.toml`):

- `chromadb`, `langchain`, `langchain-community`, `langchain-groq`, `langchain-huggingface`, `langchain-text-splitters`, `numpy`, `pandas`, `python-dotenv`, `sentence-transformers`, `streamlit`

`requirements.txt` lists the same application packages without version pins (and without `numpy` version constraints matching `pyproject.toml`).

**Transitive dependency note (verified in `uv.lock`):** `src/recommender.py` imports `langchain_classic.chains.RetrievalQA`. `langchain-classic` is **not** a direct dependency in `pyproject.toml`; it is pulled in via `langchain-community`. Prefer keeping `langchain-community` (or declaring `langchain-classic` explicitly) if that import path is retained.

**License:** MIT (see `LICENSE`).

---

## 3. Repository structure and important modules

```text
app/app.py                    Streamlit UI; @st.cache_resource pipeline init
config/config.py              load_dotenv; GROQ_API_KEY; MODEL_NAME
data/anime_with_synopsis.csv  Source dataset (includes MAL_ID, Score, etc.)
data/anime_updated.csv        Processed single-column combined_info CSV
pipeline/build_pipeline.py    Offline: process CSV + build Chroma index
pipeline/pipeline.py          AnimeRecommendationPipeline orchestration
src/data_loader.py            AnimeDataLoader — validate columns, write combined text
src/vector_store.py           VectorStoreBuilder — embed, persist, load Chroma
src/recommender.py            AnimeRecommender — Groq + RetrievalQA
src/prompt_template.py        PromptTemplate for three numbered recommendations
src/utils/logger.py           File logging under logs/
src/utils/custom_exceptions.py  AnimeRecommendationException
chroma_db/                    Persisted Chroma store (checked into git)
Dockerfile                    Container image for Streamlit on :8501
llmops-k8s.yaml               Deployment + LoadBalancer Service
pyproject.toml / uv.lock      Project metadata and locked deps
requirements.txt              Unpinned dependency list
main.py                       Placeholder greeting only
```

Hatch wheel packages: `src`, `pipeline`, `app`, `config` (`pyproject.toml`).

---

## 4. Application architecture and data flow

```text
[Build time]
anime_with_synopsis.csv
  → AnimeDataLoader.load_and_process()
  → anime_updated.csv (combined_info)
  → VectorStoreBuilder.build_and_save_vector_store()
  → chroma_db/ (CSVLoader → CharacterTextSplitter 1200/200 → Chroma.from_documents)

[Runtime]
User query (Streamlit text_input)
  → AnimeRecommendationPipeline.recommend()
  → VectorStoreBuilder.load_vector_store().as_retriever()
  → AnimeRecommender.get_recommendation()
  → RetrievalQA (stuff) + ChatGroq + get_anime_prompt()
  → Markdown/text response in UI
```

**Details agents should respect:**

- Runtime load uses `VectorStoreBuilder(csv_path="", persist_dir=persist_dir)` — only `persist_dir` matters for loading; the empty `csv_path` is intentional for the load path.
- Default persist directory is `chroma_db` (relative to process CWD). Run commands from the repository root so paths resolve.
- Prompt requires exactly three recommendations, grounded only in retrieved `{context}`; input variables are `context` and `question`.
- `ChatGroq` is constructed with `temperature=0`.
- Streamlit caches the pipeline via `@st.cache_resource` on `init_pipeline()`.

---

## 5. Environment setup and configuration

**Prerequisites (from README / manifests):**

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- Groq API key
- Network access for first-time model/dependency downloads as needed

**Setup (verified documented commands):**

```sh
uv sync
```

Create a repository-root `.env` (gitignored):

```dotenv
GROQ_API_KEY=your_groq_api_key
```

`config/config.py` loads `GROQ_API_KEY` via `os.getenv` after `load_dotenv()`. `MODEL_NAME` is fixed to `"llama-3.1-8b-instant"` in code — **not** read from the environment.

**Rebuild vector index** (from repo root):

```sh
uv run python -m pipeline.build_pipeline
```

**Run app:**

```sh
uv run streamlit run app/app.py
```

**Cannot verify:** Automated setup beyond these documented commands (e.g. conda, poetry, or CI-provisioned secrets).

---

## 6. Build, lint, and test commands

| Action | Command / status |
|--------|------------------|
| Install / sync | `uv sync` |
| Editable install (Docker) | `uv pip install --no-cache-dir -e .` (Dockerfile) |
| Build vector store | `uv run python -m pipeline.build_pipeline` |
| Run Streamlit | `uv run streamlit run app/app.py` |
| Docker build/run | `docker build -t anime-recommender .` then `docker run --rm -p 8501:8501 --env-file .env anime-recommender` (README) |

**Lint:** No project linter configuration was found (`ruff.toml`, `.ruff.toml`, `mypy.ini`, `setup.cfg`, `.pre-commit-config.yaml`, Makefile lint targets — absent). **No verified lint command.**

**Tests:** No test files, `pytest`/`tox` config, or test scripts are present in the repository. README states the same. **No verified test command.**

---

## 7. Coding conventions and error-handling patterns

Observed patterns in existing code (not a formal style guide):

- **Package layout:** Domain logic under `src/`; orchestration under `pipeline/`; UI under `app/`; secrets/model name under `config/`.
- **Logging:** Import `logging` from `src.utils.logger` (module configures `basicConfig` to a file under `logs/`). Messages are generally at INFO.
- **Exceptions:** Broad `try`/`except Exception` blocks wrap failures in `AnimeRecommendationException(e, sys)`, which records script path and line from `sys.exc_info()`. Some call sites also log the exception string before re-raising.
- **Typing:** Sparse; a few annotations (e.g. `query: str`, constructor args). Not consistently typed.
- **Imports:** Mix of absolute imports from `src.*`, `config.*`, `pipeline.*`.
- **Dataset contract:** Required columns include the misspelled `sypnopsis` — do not “fix” the column name without updating the CSV and all readers together.
- **UI:** Streamlit only; page title “Anime Recommender”, wide layout. Typos exist in UI copy (e.g. “prefernces”); preserve unless intentionally changing UX copy.

**Logger path behavior:** `src/utils/logger.py` builds a path under `logs/` using a timestamped name and calls `os.makedirs` on that path before writing the log file. `logs/` is gitignored. Prefer not changing logging layout casually without checking existing log consumers.

---

## 8. Security requirements and sensitive configuration

- **Secret:** `GROQ_API_KEY` must come from the environment (typically `.env`). Never commit `.env` — it is listed in `.gitignore`.
- **Do not** hardcode API keys in `config/config.py`, Kubernetes manifests, or source.
- **Kubernetes:** `llmops-k8s.yaml` injects env from Secret `llmops-secrets` via `envFrom.secretRef`. The manifest does **not** create that Secret; operators must create it out of band with the needed keys (at minimum whatever the app reads, i.e. `GROQ_API_KEY`).
- **Checked-in data:** Dataset CSVs and `chroma_db/` are in the tree; treat them as application data, not credentials. Still avoid committing local overrides that might contain secrets.
- **Cannot verify:** Secret rotation policy, production key management, or whether any real keys exist outside the local (gitignored) `.env`.

---

## 9. Deployment and CI/CD workflows

**Container (`Dockerfile` + `docker-compose.yml`):**

- Multi-stage: builder (`python:3.13.5-slim` + pinned `uv`) then slim runtime as uid `1000`
- CPU-only `torch` via `tool.uv.sources` → PyTorch CPU index (avoids ~6GB CUDA/`nvidia-*` wheels that stall Docker unpack on small GCP VMs)
- Install: `uv sync --frozen --no-dev` (lockfile); copies `app/`, `config/`, `pipeline/`, `src/`, `data/`, `chroma_db/`
- Exposes `8501`; healthcheck on `/_stcore/health`
- CMD: `streamlit run app/app.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true`
- VM path: prefix Docker with `env -u DOCKER_HOST` so the local daemon is used, e.g. `env -u DOCKER_HOST DOCKER_BUILDKIT=1 docker build -t llmops-app:latest .` or `env -u DOCKER_HOST docker compose up -d --build`

**Kubernetes (`llmops-k8s.yaml`):**

- Deployment `llmops-app`, 1 replica, image `llmops-app:latest`, `imagePullPolicy: IfNotPresent`, container port `8501`, env from `llmops-secrets`
- Service `llmops-service`, type `LoadBalancer`, port 80 → targetPort 8501
- Image name in the manifest (`llmops-app:latest`) differs from the README’s example local tag (`anime-recommender`); align tags when deploying.
- Ensure the image includes or mounts `chroma_db/` (and that CWD/paths match expectations).

**CI/CD:** No `.github/workflows`, GitLab CI, or other pipeline configs were found in the repository. **CI/CD automation cannot be verified** beyond the presence of Docker/K8s deployment files.

---

## 10. Rules for safely modifying the codebase

1. **Do not invent tooling.** There is no lint/test suite to “run” unless you add one; do not claim green CI if none exists.
2. **Preserve the data column contract** (`Name`, `Genres`, `sypnopsis`) unless you intentionally migrate the CSV and all code together.
3. **Run path-sensitive commands from the repo root** (`data/...`, `chroma_db/`).
4. **After changing embeddings, chunking, or source CSV,** rebuild with `uv run python -m pipeline.build_pipeline` and confirm `chroma_db/` is updated; the app loads the existing index and will not rebuild on startup.
5. **Keep `GROQ_API_KEY` out of git.** Use `.env` locally and K8s Secrets (or equivalent) in cluster.
6. **If changing the LLM or prompt,** update `config/config.py` and/or `src/prompt_template.py` and keep RetrievalQA input variables (`context`, `question`) consistent with the chain.
7. **If touching `langchain_classic` imports,** verify the dependency still resolves (today via `langchain-community`); consider declaring it directly if the import remains.
8. **`main.py` is not the app entrypoint** — do not assume changes there affect Streamlit behavior.
9. **Prefer minimal diffs** aligned with existing exception/logging patterns (`AnimeRecommendationException`, `src.utils.logger`).
10. **Deployment files:** If you change the Streamlit port or env var names, update `Dockerfile`, `llmops-k8s.yaml`, and docs together. Creating/updating the K8s Secret and publishing the image are out-of-repo steps.

### Unverified / absent (do not assume)

- Lint or format commands
- Automated tests
- CI/CD pipelines
- Non-Groq model configuration via env
- API server or production auth layer
- Official contribution/PR process beyond what is in `README.md`
