from __future__ import annotations

import os
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[2]
BACKEND_ENV_PATH = BACKEND_DIR / ".env"
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "llama3.1"
DEFAULT_OLLAMA_EMBEDDING_MODEL = "nomic-embed-text"
DEFAULT_RAG_MAX_COSINE_DISTANCE = 0.45
DEFAULT_RAG_RETRIEVAL_TOP_K = 5


def load_backend_env() -> None:
    """Load backend/.env without depending on the process working directory."""
    if not BACKEND_ENV_PATH.exists():
        return

    for raw_line in BACKEND_ENV_PATH.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def get_ollama_url() -> str:
    """Return the configured Ollama base URL for local RAG infrastructure."""
    load_backend_env()
    return os.getenv("OLLAMA_URL", DEFAULT_OLLAMA_URL).rstrip("/")


def get_ollama_model() -> str:
    """Return the configured Ollama model name for local generation."""
    load_backend_env()
    return os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL).strip()


def get_ollama_embedding_model() -> str:
    """Return the configured Ollama model name for local embeddings."""
    load_backend_env()
    return os.getenv("OLLAMA_EMBEDDING_MODEL", DEFAULT_OLLAMA_EMBEDDING_MODEL).strip()


def get_rag_max_cosine_distance() -> float:
    """Return the maximum accepted pgvector cosine distance for retrieval."""
    load_backend_env()
    raw_value = os.getenv("RAG_MAX_COSINE_DISTANCE", str(DEFAULT_RAG_MAX_COSINE_DISTANCE)).strip()
    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ValueError("RAG_MAX_COSINE_DISTANCE must be numeric") from exc
    if value < 0 or value > 2:
        raise ValueError("RAG_MAX_COSINE_DISTANCE must be between 0 and 2")
    return value


def get_rag_retrieval_top_k() -> int:
    """Return the default number of RAG retrieval results."""
    load_backend_env()
    raw_value = os.getenv("RAG_RETRIEVAL_TOP_K", str(DEFAULT_RAG_RETRIEVAL_TOP_K)).strip()
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError("RAG_RETRIEVAL_TOP_K must be an integer") from exc
    if value < 1 or value > 10:
        raise ValueError("RAG_RETRIEVAL_TOP_K must be between 1 and 10")
    return value
