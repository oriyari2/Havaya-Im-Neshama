# Task 18: Manager RAG Knowledge Management

## Plan

Add logical manager-managed RAG sources on top of the existing
`knowledge_chunks` table. Preserve Task 15-17 embedding formatting, chunking,
retrieval authorization, thresholding, and RAG-only consultation behavior.

## Implement

Managers can now create, upload, list, view, replace, and delete approved RAG
knowledge sources through backend APIs and a minimal PySide6 manager screen.

Implementation decisions:

- one pasted or uploaded document is grouped by stable `metadata.source_id`
- logical source metadata is copied to each chunk
- original content is stored in chunk metadata for manager source detail/edit
- `allowed_roles` accepts only `manager`, `instructor`, and `customer`
- `manager` is always retained
- `.txt` and `.md` uploads are supported; PDF/DOCX parsing is future work
- upload size limit is the shared source content limit of `50,000` characters
- replacement deletes chunks for the selected `source_id` and inserts new
  chunks in one transaction
- deletion removes only chunks with the selected `source_id`
- disposable Task 16 demo rows outside managed sources can be removed with a
  one-time cleanup procedure; arbitrary unmanaged production knowledge is
  preserved
- APIs never return embeddings

## API Endpoints Added

- `POST /api/rag/sources`
- `POST /api/rag/sources/upload`
- `GET /api/rag/sources`
- `GET /api/rag/sources/{source_id}`
- `PUT /api/rag/sources/{source_id}`
- `DELETE /api/rag/sources/{source_id}`

All source-management endpoints require the authenticated `manager` role.

## Files Changed

- `backend/app/application/services/knowledge_management_service.py`
- `backend/app/infrastructure/repositories/knowledge_repository.py`
- `backend/app/routers/knowledge.py`
- `backend/app/schemas/knowledge.py`
- `backend/tests/test_task18_knowledge_management.py`
- `rag/cleanup_task16_demo_knowledge.py`
- `desktop_client/app/main.py`
- `desktop_client/app/features/knowledge/presenter.py`
- `desktop_client/app/shared/navigation.py`
- `desktop_client/app/features/knowledge/service.py`
- `desktop_client/app/features/knowledge/view.py`
- `desktop_client/tests/test_knowledge_management.py`
- `desktop_client/tests/test_presenters.py`
- `desktop_client/tests/test_views.py`
- `docs/piv/18-manager-rag-knowledge-management.md`
- `docs/piv/requirements-traceability.md`
- `README.md`

## How To Run

Start PostgreSQL/Supabase-compatible persistence, Ollama, and the backend:

```powershell
uvicorn backend.app.main:app --reload
```

Run the desktop client:

```powershell
python -m desktop_client.app.main
```

Log in as a manager and open the `ניהול ידע` navigation item.

Run the one-time cleanup for disposable Task 16 demo chunks that were created
before managed source IDs existed:

```powershell
.\.venv\Scripts\python.exe -m rag.cleanup_task16_demo_knowledge
```

The cleanup deletes only unmanaged `knowledge_chunks` rows that match known
Task 16 demo identifiers, such as `source_uri LIKE 'demo://knowledge/%'`, known
Task 16 demo titles, or an explicit Task 16 demo metadata marker.

## Validation

Automated validation passed:

```powershell
.\.venv\Scripts\python.exe -m unittest backend.tests.test_task18_knowledge_management -v
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
.\.venv\Scripts\python.exe -m unittest discover -s desktop_client/tests -v
.\.venv\Scripts\python.exe -m compileall backend desktop_client rag
git diff --check
git status --short
```

Final desktop consistency cleanup additionally aligned local `.txt`/`.md`
validation with the shared `50,000` character source limit, cleared stale file
selection when source details load or pasted text changes, cleared file
selection after successful create/replace, and updated the README limit text.

Results:

- Focused Task 18 backend tests: 12 passed.
- Focused Task 18 desktop tests: 10 passed.
- Full backend unittest suite: 169 passed.
- Full desktop unittest suite: 86 passed.
- Compile validation passed for `backend`, `desktop_client`, and `rag`.
- `git diff --check` passed with line-ending warnings only.

Focused tests cover manager-only access, pasted text source creation, supported
upload, empty/unsupported upload rejection, upload size limit, manager role
retention, invalid role rejection, logical source listing, grouped replace/delete
API calls, replacement deleting all old selected-source chunks while preserving
another source, replacement creating only new chunks, deletion removing every
selected-source chunk, customer/instructor retrieval following `allowed_roles`,
Task 16 demo chunk cleanup preserving unmanaged non-demo sources, manager-only
desktop visibility, and basic presenter/service actions.

Live validation passed against the configured Supabase-compatible database and
local Ollama after allowing network access. Demo login succeeded for
`manager@example.com`, `instructor@example.com`, and `customer@example.com`.
The cleanup procedure deletes only known disposable Task 16 demo rows and
preserves unmanaged non-demo legacy knowledge. Manager-created customer-visible and
instructor-only sources were retrievable only by permitted roles. Customer
`/api/ai/consult` returned `answer_basis="rag"` with a cited managed source for
a natural question. Replacement removed old selected-source content and created
the new chunk. Deletion removed the selected source chunks. Temporary
live-validation managed sources were deleted at the end.

## PRD Requirements Advanced

- `FR-AI-05`: role-aware RAG access remains enforced by authenticated roles.
- `FR-AI-06`: RAG management is separate from read-only consultation; the AI
  assistant still does not mutate operational data.
- `FR-AI-07`: managers can maintain approved internal knowledge sources with
  role visibility metadata.

## Limitations

- PDF, DOCX, OCR, web search, and automatic business-rule extraction are not
  implemented.
- The desktop file picker reads `.txt`/`.md` content locally and sends it
  through the text-source API; the backend multipart upload endpoint is also
  available for API clients.
- Logical source metadata is stored in `knowledge_chunks.metadata`; there is no
  separate `knowledge_sources` table in this MVP slice.

## Next Task

Continue with the next task in the project plan; Task 18 is ready for review
before commit.
