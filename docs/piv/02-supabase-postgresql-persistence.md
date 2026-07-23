# PIV 02 - Supabase PostgreSQL Persistence

## Plan

Create the first backend persistence layer for Supabase PostgreSQL without adding
authentication, CRUD screens, RAG, event sourcing, or other future tasks.

This task supports the MVP foundation for customers, contacts, activities,
instructors, bookings with multiple activities, equipment planning, and price
components.

## Implement

- Added `psycopg[binary]` as the PostgreSQL driver.
- Added `backend.app.db.connection` to load local `.env` files and open a
  PostgreSQL connection from `DATABASE_URL`.
- Added `backend.app.db.schema` with the required UUID-based tables and indexes.
- Added `backend.app.db.init_db` to run idempotent schema creation.
- Added `backend.app.routers.system` with database status, initialization, and
  schema summary endpoints.
- Registered the system router in the FastAPI app.
- Updated `backend/.env.example` with placeholder-only Supabase PostgreSQL connection
  configuration.
- Frontend does not connect directly to Supabase. Backend owns all persistence access.

## Validate

- `python -m compileall backend desktop_client` passed.
- `.venv\Scripts\python.exe -m compileall backend desktop_client` passed.
- FastAPI route import check passed and registered `/system/db-status`,
  `/system/init-db`, `/system/schema-summary`, and `/health`.
- Local endpoint probing with `TestClient` could not run because this skeleton
  does not include `httpx`.
- The local `backend/.env` currently does not include `DATABASE_URL`, so the
  database endpoints will return a clear configuration error until the real
  Supabase PostgreSQL connection string is added locally.
- Database-related environment variables are backend-only and are loaded from
  `backend/.env`.
