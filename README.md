# Experience-with-Soul

Student final project for Windows Systems Engineering.

The project will become the Havaya Im Neshama management system described in
[docs/PRD.md](docs/PRD.md). The current MVP foundation includes FastAPI and
PySide6 MVP layers, Supabase-compatible PostgreSQL persistence, Hebrew demo
seed data, authentication/RBAC, customer/activity/instructor management,
event-sourced booking workflows, role-aware desktop screens, local Ollama AI
infrastructure, and the first approved-knowledge RAG ingestion slice.

## Project Structure

```text
backend/            FastAPI backend
desktop_client/     PySide6 desktop client
rag/                Ollama LLM and embedding clients
docker/             Local Ollama Docker Compose service
migrations/         Future database migrations
docs/               Product and project documentation
tasks/              Implementation task files
```

## Setup

**Prerequisites:**
- Python 3.10+
- Docker & Docker Compose (required for the local AI/Ollama server)

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

Copy `backend\.env.example` to `backend\.env` when local backend
configuration is needed. The backend reads configuration only from
`backend\.env`, resolved from the backend source location, and real secrets
must not be committed.

## AI Server Setup (Ollama)

The system uses a local Ollama server running inside a Docker container to
power the AI consultation and embedding features.

1. Ensure Docker Desktop is running, then navigate to the docker directory and start the container:
```powershell
cd docker
docker-compose up -d
```
2. Download the Llama 3 generation model into the running container. This may
   take a few minutes:
```powershell
docker exec ollama_server ollama pull llama3
```
3. Once the download is complete, a prompt (`>>>`) will appear. Type `/bye`
   and press Enter to exit. The server will continue running in the background.
4. Download the embedding model used by Task 15 RAG ingestion:
```powershell
docker exec ollama_server ollama pull nomic-embed-text
```

*Note: The backend connects to this service via `OLLAMA_URL` in `backend\.env`
(default: `http://localhost:11434`). Embeddings use `OLLAMA_EMBEDDING_MODEL`
(default: `nomic-embed-text`).*

## Initialize The Database

With a configured Supabase-compatible PostgreSQL connection, initialize the
schema through the guarded system endpoint:

```text
POST http://127.0.0.1:8000/system/init-db
```

Set `INIT_DB_ENABLED=true` in `backend\.env` for local/demo initialization.
The current schema includes booking event sourcing tables, activity image
metadata, and Task 15 `knowledge_chunks` storage using PostgreSQL `vector`.

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
- PySide6 login and role-based desktop shell using MVP boundaries.
- Role-aware dashboard, bookings, booking details/history, open events, and
  customer my-bookings screens backed by the FastAPI API.
- Manager booking creation, confirmation, cancellation, and supported field
  edits through the event-sourced command API with optimistic concurrency.
- Manager customer directory and nested contact management with search,
  filters and pagination. Customers use protected physical deletion; linked
  bookings/history/users return 409, while owned contacts cascade.
- Manager textual activity management and an active-only read-only activity
  catalog for instructors/customers, including search, filters, pagination,
  detail, and soft deactivate/reactivate.
- Manager instructor profile management with search/filter/page/detail and
  protected physical deletion, plus an instructor-owned read-only profile.
  Assignment/history/user dependencies return 409.
- Event-sourced instructor assignment/removal embedded in Booking Details and
  role-safe open-event detail for instructors.
- Paged and named booking filters, readable customer/activity projections,
  manager completion, role-operational dashboard drill-down, and synchronized
  role navigation (Task 12F).
- Local Ollama AI infrastructure integration via backend HTTP client (Task 13).
- Authenticated read-only AI consultation endpoint and PySide6 chat screen
  backed by the Ollama generation client (Task 14).
- Manager-only approved-knowledge RAG ingestion infrastructure using Ollama
  embeddings, deterministic chunking, content hashes, and PostgreSQL pgvector
  storage in `knowledge_chunks` (Task 15).

Task 16 retrieval infrastructure is the current completed slice. Retrieved
context is not yet integrated into the AI consultation prompt; role-filtered
citations, abstention behavior in generated answers, desktop knowledge-source
management, and UI/UX redesign remain future work. Task 17 is blocked until
Hebrew embedding/retrieval quality is understood or corrected.

## RAG Knowledge Ingestion

After the backend is running, managers can ingest approved internal knowledge:

```text
POST /api/rag/knowledge
```

The endpoint chunks the submitted text, calls Ollama embeddings, and stores the
approved chunks in PostgreSQL for a future retrieval task. The AI consultation
flow remains read-only for operational data.

Authenticated users can search approved knowledge independently of AI answer
generation:

```text
POST /api/rag/search
```

The endpoint embeds the normalized query with `OLLAMA_EMBEDDING_MODEL`, searches
`knowledge_chunks` with pgvector cosine distance, filters by the authenticated
role in the database query, and returns ordered chunks without exposing stored
embeddings. Managers can retrieve all chunks. Instructors and customers only see
chunks whose structured `metadata.allowed_roles` array includes their role;
missing or malformed role metadata is treated as manager-only.

Retrieval defaults are code-level application constants in
`backend/app/core/environment.py`, not deployment `.env` settings:

```python
RAG_MAX_COSINE_DISTANCE = 0.45
RAG_RETRIEVAL_TOP_K = 5
```

The search request rejects unexpected fields, so authorization metadata such as
`role` cannot be supplied by the caller. The authenticated role comes only from
the backend authentication context.

Controlled Task 16 Hebrew validation currently shows a retrieval-quality
limitation: unrelated Hebrew queries can receive very low cosine distances with
`nomic-embed-text`. Treat Task 16 as retrieval infrastructure; do not connect it
to grounded AI answers until that behavior is understood. A follow-up diagnostic
verified that two Hebrew paraphrase queries produce distinct outgoing request
strings and distinct 768-dimensional vectors through both `OllamaEmbeddingClient`
and direct `/api/embed`; the earlier identical-vector observation is classified
as a validation-script/input-encoding defect, not a client parsing defect.

## Validation

Recent Task 15 validation:

```powershell
.\.venv\Scripts\python.exe -m unittest backend.tests.test_task15_rag_ingestion
.\.venv\Scripts\python.exe -m unittest discover backend/tests
.\.venv\Scripts\python.exe -m compileall backend desktop_client
```

Expected results from the latest documented pass: Task 15 tests passed, the
full backend unittest suite passed, and compile validation passed for both
backend and desktop client.
