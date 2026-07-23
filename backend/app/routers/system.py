from fastapi import APIRouter, HTTPException

from backend.app.db.connection import get_connection
from backend.app.db.init_db import initialize_database
from backend.app.db.schema import EXPECTED_TABLES


router = APIRouter(prefix="/system", tags=["system"])


@router.get("/db-status")
def db_status() -> dict[str, str]:
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {"status": "ok", "database": "reachable"}


@router.post("/init-db")
def init_db() -> dict[str, object]:
    try:
        with get_connection() as conn:
            initialize_database(conn)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {"status": "ok", "tables": EXPECTED_TABLES}


@router.get("/schema-summary")
def schema_summary() -> dict[str, object]:
    try:
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
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    tables = [
        {"name": table_name, "exists": table_name in existing_tables}
        for table_name in EXPECTED_TABLES
    ]
    return {"status": "ok", "tables": tables}
