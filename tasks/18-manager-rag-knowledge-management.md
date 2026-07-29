# Task 18 — Manager RAG Knowledge Management

## Goal

Allow managers to add, upload, list, replace, and delete approved RAG knowledge from the desktop application, while choosing which roles may retrieve each source.

## Scope

Implement manager-only knowledge-source management using the existing Task 15–17 ingestion, embedding, pgvector retrieval, authorization, and RAG-only consultation flow.

## Required Behavior

### 1. Knowledge Source Model

Treat one uploaded/pasted document as one logical source, even when it is stored as multiple chunks.

Each source must include:

- stable source ID
- title
- optional filename/source URI
- category
- optional activity name
- allowed roles
- original content
- creation/update metadata

Allowed roles:

- `manager`
- `instructor`
- `customer`

Rules:

- `manager` is always included.
- Reject unknown roles.
- Missing or malformed role metadata remains fail-closed.
- Do not expose embeddings through APIs.

Use the existing production embedding model, formatting, threshold, and chunking.

### 2. Manager-Only Backend API

Add manager-only endpoints to:

- create a source from pasted text
- create a source from an uploaded text document
- list logical sources, not individual chunks
- read source details and content
- replace a source and regenerate all its chunks
- delete a source and all its chunks

Minimum supported uploads:

- `.txt`
- `.md`

Only add PDF/DOCX support if the project already has a safe parser; otherwise report it as future work.

Validation:

- reject empty content
- reject unsupported file types
- apply a reasonable upload-size limit
- prevent duplicate old chunks during replacement
- make replacement atomic where practical
- deleting/replacing one source must not affect other sources

### 3. Desktop Manager Screen

Add a minimal manager-only knowledge-management screen with:

- source title
- category
- optional activity
- pasted-text input
- file picker
- instructor visibility checkbox
- customer visibility checkbox
- save/upload action
- logical source list
- view/edit action
- replace action
- delete action with confirmation

Managers must not see this screen when logged in as instructor or customer.

Do not redesign unrelated screens.

### 4. Authorization

- Only managers may create, list, view, replace, or delete knowledge sources.
- Retrieval remains role-aware through `allowed_roles`.
- Customers and instructors must never receive source-management APIs.
- Request bodies cannot override the authenticated user role.

### 5. Tests

Add focused backend and desktop tests proving:

- non-manager management access is denied
- manager can create pasted-text knowledge
- manager can upload supported files
- unsupported/empty files are rejected
- manager is automatically retained in `allowed_roles`
- invalid roles are rejected
- source listing aggregates chunks into one source
- replacement removes old chunks and creates only new chunks
- deletion removes every chunk belonging to the source
- unrelated sources remain unchanged
- instructor/customer retrieval follows selected visibility
- embeddings are never returned
- manager-only screen visibility and basic presenter/service actions work

## Validation

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest backend.tests.test_task18_knowledge_management -v
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
.\.venv\Scripts\python.exe -m unittest discover -s desktop_client/tests -v
.\.venv\Scripts\python.exe -m compileall backend desktop_client rag
git diff --check
git status --short
```

Also perform live checks:

1. Manager uploads a customer-visible activity document.
2. Customer retrieves and uses it through `/api/ai/consult`.
3. Manager uploads an instructor-only equipment document.
4. Instructor can retrieve it.
5. Customer cannot retrieve it.
6. Manager replaces the activity document and old content is no longer returned.
7. Manager deletes the source and none of its chunks remain.

## Documentation

Create/update:

- `docs/piv/18-manager-rag-knowledge-management.md`
- `docs/piv/requirements-traceability.md`
- `README.md`

## Out of Scope

- activity-capacity or price calculation engine
- automatic extraction of business rules from documents
- web search or general-knowledge fallback
- OCR
- unrelated UI redesign
- commit or push
