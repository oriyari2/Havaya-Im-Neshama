# Experience-with-Soul

Student final project for Windows Systems Engineering.

The project will become the Havaya Im Neshama management system described in
[docs/PRD.md](docs/PRD.md). The current MVP foundation includes FastAPI and
PySide6 MVP layers, Supabase-compatible PostgreSQL persistence, Hebrew demo
seed data, authentication/RBAC, customer/activity/instructor management,
event-sourced booking workflows, role-aware desktop screens, local Ollama AI
infrastructure, approved-knowledge RAG ingestion and retrieval, and grounded
RAG-only AI consultation with manager knowledge-source management.

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
4. Download the embedding model used by Task 16 RAG ingestion and retrieval:
```powershell
docker exec ollama_server ollama pull nomic-embed-text-v2-moe
```

*Note: The backend connects to this service via `OLLAMA_URL` in `backend\.env`
(default: `http://localhost:11434`). Embeddings use `OLLAMA_EMBEDDING_MODEL`
(default: `nomic-embed-text-v2-moe`).*

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
- Manager activity-image upload/delete inside the Activities screen through the
  existing FastAPI/Cloudinary Gateway, plus read-only previews for active
  activities for instructors and customers (Task 19).
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
  backed by approved retrieved knowledge and the Ollama generation client
  (Tasks 14 and 17).
- Manager-only approved-knowledge RAG ingestion infrastructure using Ollama
  embeddings, deterministic chunking, content hashes, and PostgreSQL pgvector
  storage in `knowledge_chunks` (Task 15).
- Manager-only approved knowledge-source management for pasted text and
  `.txt`/`.md` uploads, with logical source listing, replace/delete, and
  configurable role visibility metadata (Task 18).

Task 17 connects role-aware retrieval to `POST /api/ai/consult`. The endpoint
retrieves approved chunks using only the authenticated role before generation,
answers only from those chunks, requires inline `[n]` citations, returns
`answer_basis="rag"` with used sources, and abstains with `answer_basis="none"`
without calling the LLM when reliable context is unavailable. There is no
general-knowledge or web fallback.

## Desktop Activity Images

Managers can select an activity and upload or delete JPEG, PNG, and WebP images
from the existing Activities screen. Instructors and customers see previews for
active activities without mutation controls. Upload/delete always use the
authenticated FastAPI endpoints and backend-owned image Gateway; the desktop
contains no Cloudinary credentials or SDK.

Desktop safety defaults are centralized in
`desktop_client/app/media_config.py`: uploads and preview downloads are limited
to 10 MiB, and at most three successful previews are retained in a memory-only
LRU cache. Public HTTPS preview requests omit the FastAPI bearer token. Preview
images are never written to disk, and the cache is cleared on logout or session
expiry. Redirects are accepted only when every target and the final response
remain on HTTPS.

## RAG Knowledge Ingestion

After the backend is running, managers can ingest approved internal knowledge:

```text
POST /api/rag/knowledge
```

The endpoint chunks the submitted text, preserves the original chunk content and
metadata in PostgreSQL, and embeds an enriched document input through
`format_document_embedding_input`. For `nomic-embed-text-v2-moe`, document
embedding input is prefixed with `search_document:`.

Authenticated users can search approved knowledge independently of AI answer
generation:

```text
POST /api/rag/search
```

The endpoint embeds the normalized query with `format_query_embedding_input`,
searches `knowledge_chunks` with pgvector cosine distance, filters by the
authenticated role in the database query, and returns ordered chunks without
exposing stored embeddings. For `nomic-embed-text-v2-moe`, query embedding input
is prefixed with `search_query:`. Managers can retrieve all chunks. Instructors
and customers only see chunks whose structured `metadata.allowed_roles` array
includes their role; missing or malformed role metadata is treated as
manager-only.

Retrieval defaults are code-level application constants in
`backend/app/core/environment.py`, not deployment `.env` settings:

```python
DEFAULT_OLLAMA_EMBEDDING_MODEL = "nomic-embed-text-v2-moe"
RAG_MAX_COSINE_DISTANCE = 0.58
RAG_RETRIEVAL_TOP_K = 5
```

The search request rejects unexpected fields, so authorization metadata such as
`role` cannot be supplied by the caller. The authenticated role comes only from
the backend authentication context.

Managers can also manage logical approved knowledge sources:

```text
POST   /api/rag/sources
POST   /api/rag/sources/upload
GET    /api/rag/sources
GET    /api/rag/sources/{source_id}
PUT    /api/rag/sources/{source_id}
DELETE /api/rag/sources/{source_id}
```

One pasted or uploaded document is grouped by a stable `metadata.source_id`
across all generated chunks. Source responses include title, optional
filename/source URI, category, optional activity name, original content,
allowed roles, and chunk counts, but never embeddings. Supported uploads are
UTF-8 `.txt` and `.md` files up to `50,000 characters`; PDF, DOCX, and OCR are not part
of the MVP. The `allowed_roles` list accepts only `manager`, `instructor`, and
`customer`; `manager` is always retained. Replace/delete operations target only
chunks with the selected source ID.

The desktop app exposes a minimal `ניהול ידע` screen only for managers.

If the database still contains disposable Task 16 demo chunks created before
managed source IDs existed, run the one-time cleanup:

```powershell
.\.venv\Scripts\python.exe -m rag.cleanup_task16_demo_knowledge
```

The cleanup deletes only unmanaged `knowledge_chunks` rows that match known
Task 16 demo identifiers, such as `demo://knowledge/...` URIs, known Task 16
demo titles, or explicit Task 16 demo metadata markers. Managed sources and
non-demo legacy sources are preserved.

Authenticated users can ask the grounded AI consultation endpoint:

```text
POST /api/ai/consult
```

The backend first calls the same role-aware retrieval service. If no chunks are
found, it returns:

```json
{
  "answer": "לא נמצא במאגר הידע המאושר מידע מספיק כדי לענות על השאלה.",
  "answer_basis": "none",
  "sources": []
}
```

When chunks are found, the LLM receives only numbered retrieved context and a
strict instruction to cite sources as `[1]`, `[2]`, etc. The desktop chat shows
returned source titles and URIs under RAG answers.

Task 16 now uses the selected production embedding strategy:
`nomic-embed-text-v2-moe`, 768 dimensions, `search_document:` for stored
knowledge embeddings, `search_query:` for retrieval embeddings, and threshold
`0.58`.

The Hebrew evaluation fixture is versioned at
`rag/evaluation_fixture_task16_he.json`, and the live model comparison can be
run with:

```powershell
.\.venv\Scripts\python.exe -m rag.evaluate_task16_live
```

The corrected live comparison found all requested models installed:
`nomic-embed-text`, `nomic-embed-text-v2-moe`, and `bge-m3`. The evaluator
inserts temporary `eval://task16-hebrew-model-comparison/...` rows, reuses the
production retrieval repository, verifies authorization against returned
`metadata.allowed_roles`, reports raw metrics before threshold filtering,
evaluates explicit and generated threshold candidates, emits exact failure
reports, and cleans up temporary rows with `try/finally`.

Use the repeatable Task 16 reset only for the disposable demo knowledge rows:

```powershell
.\.venv\Scripts\python.exe -m rag.reset_task16_demo_knowledge
```

The script deletes only `knowledge_chunks`, reingests the approved demo
knowledge through the production ingestion service, verifies all rows use
`nomic-embed-text-v2-moe` with 768 dimensions, runs Hebrew relevant and
unsupported searches at threshold `0.58`, checks fail-closed role authorization,
and snapshots unrelated table counts before and after the reset.

## Validation

Recent Task 17 validation:

```powershell
.\.venv\Scripts\python.exe -m unittest backend.tests.test_ai_consult_api -v
.\.venv\Scripts\python.exe -m unittest desktop_client.tests.test_services desktop_client.tests.test_presenters -v
.\.venv\Scripts\python.exe -m unittest backend.tests.test_task15_rag_ingestion
.\.venv\Scripts\python.exe -m unittest discover backend/tests
.\.venv\Scripts\python.exe -m compileall backend desktop_client
git diff --check
```

Expected results from the latest documented pass: focused AI/desktop tests,
the full backend unittest suite, compile validation, and whitespace validation
passed.
