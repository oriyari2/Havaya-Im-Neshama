# Experience-with-Soul

Student final project for Windows Systems Engineering.

The project will become the Havaya Im Neshama management system described in
[docs/PRD.md](docs/PRD.md). Task 01 creates only the initial working skeleton:
a FastAPI backend health check, a basic PySide6 desktop window, and empty folders
for later RAG, Docker, and database migration work.

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

Authentication, customers, activities, bookings, event sourcing, dashboard, and
RAG behavior are intentionally not implemented yet.
