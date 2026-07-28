from __future__ import annotations

import os
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[2]
BACKEND_ENV_PATH = BACKEND_DIR / ".env"
DEFAULT_OLLAMA_URL = "http://localhost:11434"


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
