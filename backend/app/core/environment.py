from __future__ import annotations

import os
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[2]
BACKEND_ENV_PATH = BACKEND_DIR / ".env"
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "llama3.1"
DEFAULT_OLLAMA_EMBEDDING_MODEL = "nomic-embed-text-v2-moe"
DEFAULT_OLLAMA_KEEP_ALIVE = "30m"
DEFAULT_OLLAMA_GENERATION_TIMEOUT_SECONDS = 600.0
DEFAULT_OLLAMA_STARTUP_TIMEOUT_SECONDS = 30.0
DEFAULT_OLLAMA_TEMPERATURE = 0.1
DEFAULT_OLLAMA_NUM_PREDICT = 2000
DEFAULT_DB_POOL_MIN_SIZE = 1
DEFAULT_DB_POOL_MAX_SIZE = 5

RAG_MAX_COSINE_DISTANCE = 0.58
RAG_RETRIEVAL_TOP_K = 5

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
    return RAG_MAX_COSINE_DISTANCE


def get_rag_retrieval_top_k() -> int:
    """Return the default number of RAG retrieval results."""
    return RAG_RETRIEVAL_TOP_K


def get_db_pool_min_size() -> int:
    load_backend_env()
    configured = _positive_int("DB_POOL_MIN_SIZE", DEFAULT_DB_POOL_MIN_SIZE)
    return min(configured, DEFAULT_DB_POOL_MAX_SIZE)


def get_db_pool_max_size() -> int:
    load_backend_env()
    configured = _positive_int("DB_POOL_MAX_SIZE", DEFAULT_DB_POOL_MAX_SIZE)
    return max(get_db_pool_min_size(), min(configured, DEFAULT_DB_POOL_MAX_SIZE))


def get_ollama_keep_alive() -> str:
    load_backend_env()
    return os.getenv("OLLAMA_KEEP_ALIVE", DEFAULT_OLLAMA_KEEP_ALIVE).strip() or DEFAULT_OLLAMA_KEEP_ALIVE


def get_ollama_generation_timeout_seconds() -> float:
    load_backend_env()
    return _positive_float("OLLAMA_GENERATION_TIMEOUT_SECONDS", DEFAULT_OLLAMA_GENERATION_TIMEOUT_SECONDS)


def get_ollama_startup_timeout_seconds() -> float:
    load_backend_env()
    return _positive_float("OLLAMA_STARTUP_TIMEOUT_SECONDS", DEFAULT_OLLAMA_STARTUP_TIMEOUT_SECONDS)


def get_ollama_temperature() -> float:
    load_backend_env()
    return _positive_float("OLLAMA_TEMPERATURE", DEFAULT_OLLAMA_TEMPERATURE, allow_zero=True)


def get_ollama_num_predict() -> int:
    load_backend_env()
    return _positive_int("OLLAMA_NUM_PREDICT", DEFAULT_OLLAMA_NUM_PREDICT)


def _positive_int(key: str, default: int) -> int:
    try:
        value = int(os.getenv(key, str(default)))
    except ValueError:
        return default
    return value if value > 0 else default


def _positive_float(key: str, default: float, *, allow_zero: bool = False) -> float:
    try:
        value = float(os.getenv(key, str(default)))
    except ValueError:
        return default
    return value if value > 0 or (allow_zero and value == 0) else default
