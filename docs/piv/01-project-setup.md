# 01 Project Setup

## Plan

Create the smallest runnable project skeleton required for the first increment:

- FastAPI backend with a health check.
- PySide6 desktop client with a basic main window.
- Initial folders for future RAG, Docker, and migrations work.
- Example environment file without secrets.
- README setup and run instructions.

## Implement

- Added `backend/app/main.py` with a `/health` endpoint.
- Added backend and desktop dependency files.
- Added `desktop_client/app/main.py` with a simple `QMainWindow`.
- Added placeholder folders for `rag`, `docker`, and `migrations`.
- Added `.env.example`.
- Expanded `README.md` with setup and run instructions.

## Validate

- Import/compile check should pass after Python dependencies are installed.
- Manual backend check: run `uvicorn backend.app.main:app --reload` and open `/health`.
- Manual desktop check: run `python -m desktop_client.app.main`.
