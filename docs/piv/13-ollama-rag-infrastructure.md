# Task 13 PIV - Ollama RAG Infrastructure

## Planned

Task 13 creates the Python backend-side infrastructure needed to communicate
with the already-running local Ollama service at `http://localhost:11434`.
Docker setup, model download, RAG retrieval, ingestion, endpoints, and desktop
AI screens are out of scope for this task.

## Implemented

- Added `OLLAMA_URL` environment support with a default of
  `http://localhost:11434`.
- Added an importable `rag` Python package.
- Added `LLMClient` as the application-facing generation interface.
- Added `OllamaLLMClient`, which sends non-streaming generation requests to
  Ollama's `/api/generate` endpoint through `httpx`.
- Added optional context injection in the client prompt shape so future RAG
  query services can pass approved retrieved snippets without changing the
  FastAPI service contract.
- Added focused client tests using mocked HTTP calls.

## PRD Requirements Advanced

- `FR-AI-01` through `FR-AI-04`: infrastructure groundwork for future
  recommendation, knowledge answer, proposal draft, and unavailable-answer
  flows.
- `FR-AI-06`: preserves the MVP read-only AI direction because this task adds
  generation infrastructure only and no mutation capability.
- Course architecture: advances the required Docker/Ollama and RAG concepts by
  isolating local LLM access behind an interface.

## Files Changed

- `backend/app/core/environment.py`
- `backend/.env.example`
- `backend/.env`
- `backend/requirements.txt`
- `rag/__init__.py`
- `rag/llm_client.py`
- `backend/tests/test_rag_llm_client.py`
- `docs/piv/13-ollama-rag-infrastructure.md`
- `docs/piv/requirements-traceability.md`

## How To Run

Install backend dependencies if needed:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

Use the client from backend services:

```python
from rag import OllamaLLMClient

client = OllamaLLMClient(model="your-downloaded-model")
answer = client.generate("What equipment is needed?", context=["Approved source text"])
```

The client reads `OLLAMA_URL` from `backend/.env` and falls back to
`http://localhost:11434`.

## Validation

- `.\.venv\Scripts\python.exe -m unittest backend.tests.test_rag_llm_client -v`
- `.\.venv\Scripts\python.exe -m compileall backend desktop_client`

No live Ollama request is required for automated validation; the unit tests
mock the HTTP transport.

## Next Task

The next AI task should add approved-knowledge ingestion/retrieval and a
role-aware RAG orchestration service that calls `LLMClient` only after retrieval
has supplied sufficient evidence.
