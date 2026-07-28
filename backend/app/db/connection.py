from collections.abc import Iterator
from contextlib import contextmanager
import os
from pathlib import Path

import psycopg
from psycopg import Connection


ROOT_DIR = Path(__file__).resolve().parents[3]
BACKEND_DIR = ROOT_DIR / "backend"


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def load_local_env() -> None:
    backend_env_path = BACKEND_DIR / ".env"
    root_env_path = ROOT_DIR / ".env"

    if backend_env_path.exists():
        _load_env_file(backend_env_path)
    if root_env_path.exists():
        _load_env_file(root_env_path)


def get_database_url() -> str:
    load_local_env()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is missing. Add your Supabase PostgreSQL connection "
            "string to backend/.env."
        )
    return database_url.replace("postgresql+psycopg://", "postgresql://", 1)


@contextmanager
def get_connection() -> Iterator[Connection]:
    with psycopg.connect(get_database_url()) as conn:
        yield conn
