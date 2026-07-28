from __future__ import annotations

from backend.app.db.connection import get_connection
from backend.app.db.schema import EXPECTED_TABLES


def check_database_reachable() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
            cur.fetchone()


def get_schema_summary() -> list[dict[str, object]]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = ANY(%s);
                """,
                (EXPECTED_TABLES,),
            )
            existing_tables = {row[0] for row in cur.fetchall()}

    return [
        {"name": table_name, "exists": table_name in existing_tables}
        for table_name in EXPECTED_TABLES
    ]
