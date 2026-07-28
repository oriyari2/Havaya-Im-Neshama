from collections.abc import Iterator
from contextlib import contextmanager
import os

import psycopg
from psycopg import Connection

from backend.app.core.environment import load_backend_env


def get_database_url() -> str:
    load_backend_env()
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
