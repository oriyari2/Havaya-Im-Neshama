import os

from fastapi import APIRouter, HTTPException

from backend.app.core.security import get_app_env

from backend.app.db.init_db import initialize_database
from backend.app.db.schema import EXPECTED_TABLES
from backend.app.db.system_queries import check_database_reachable, get_schema_summary
from backend.app.db.connection import get_connection


router = APIRouter(prefix="/system", tags=["system"])


@router.get("/db-status")
def db_status() -> dict[str, str]:
    try:
        check_database_reachable()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {"status": "ok", "database": "reachable"}


@router.post("/init-db")
def init_db() -> dict[str, object]:
    if get_app_env() not in {"development", "local", "test"}:
        raise HTTPException(status_code=403, detail="Not authorized")
    if os.getenv("INIT_DB_ENABLED", "false").strip().lower() != "true":
        raise HTTPException(status_code=403, detail="Database initialization is disabled")
    try:
        with get_connection() as conn:
            initialize_database(conn)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {"status": "ok", "tables": EXPECTED_TABLES}


@router.get("/schema-summary")
def schema_summary() -> dict[str, object]:
    try:
        tables = get_schema_summary()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {"status": "ok", "tables": tables}
