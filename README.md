# Experience-with-Soul

Student final project for Windows Systems Engineering.

The project will become the Havaya Im Neshama management system described in
[docs/PRD.md](docs/PRD.md). The current MVP foundation includes the initial
FastAPI and PySide6 skeleton, Supabase-compatible PostgreSQL setup, Hebrew demo
seed data, and a customer/contact CRUD API.

## Project Structure

```text
backend/            FastAPI backend
desktop_client/     PySide6 desktop client
rag/                Future RAG modules
docker/             Future Docker configuration
migrations/         Future database migrations
docs/               Product and project documentation
tasks/              Implementation task files
```

## Setup

Create a Python virtual environment from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies:

```powershell
pip install -r backend\requirements.txt
```

Install desktop dependencies:

```powershell
pip install -r desktop_client\requirements.txt
```

Copy `.env.example` to `.env` when local configuration is needed. Do not commit
real secrets.

## Run The Backend

```powershell
uvicorn backend.app.main:app --reload
```

Open the health check:

```text
http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## Run The Desktop App

```powershell
python -m desktop_client.app.main
```

## Current Scope

Implemented so far:

- FastAPI health/system endpoints.
- PostgreSQL schema initialization and Hebrew demo seed data.
- Customer and customer-contact CRUD API, including soft delete, active defaults,
  search, and `city` / `customer_type` filters.
- Basic PySide6 desktop startup shell.

Authentication, activities, bookings, event sourcing, dashboard, desktop feature
screens, image upload, and RAG behavior are intentionally not implemented yet.
