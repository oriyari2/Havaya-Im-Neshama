from collections.abc import Iterator
from contextlib import contextmanager
import os

import psycopg
from psycopg import Connection
from psycopg_pool import ConnectionPool

from backend.app.core.environment import get_db_pool_max_size, get_db_pool_min_size, load_backend_env


_pool: ConnectionPool | None = None


def get_database_url() -> str:
    load_backend_env()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is missing. Add your Supabase PostgreSQL connection "
            "string to backend/.env."
        )
    return database_url.replace("postgresql+psycopg://", "postgresql://", 1)


def open_connection_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            conninfo=get_database_url(),
            min_size=get_db_pool_min_size(),
            max_size=get_db_pool_max_size(),
            open=False,
        )
    if getattr(_pool, "closed", True):
        _pool.open()
    return _pool


def close_connection_pool() -> None:
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


def get_connection_pool() -> ConnectionPool:
    return open_connection_pool()


@contextmanager
def get_connection() -> Iterator[Connection]:
    pool = get_connection_pool()
    with pool.connection() as conn:
        yield conn


@contextmanager
def get_unpooled_connection() -> Iterator[Connection]:
    with psycopg.connect(get_database_url()) as conn:
        yield conn
