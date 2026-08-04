# Task 14 PIV - AI Consultation API and Desktop UI

## Planned

Task 14 exposes the Task 13 `LLMClient` through FastAPI and adds a PySide6 MVP
chat interface in the desktop client. RAG retrieval, approved knowledge
citations, ingestion, and AI mutations remain out of scope.

## Implemented

- Added authenticated `POST /api/ai/consult` under a dedicated AI router.
- Added request/response schemas for AI consultation prompts and answers.
- Added a thin `AIConsultationService` that injects `LLMClient` and calls
  Ollama without retrieval context for this task.
- Added `OLLAMA_MODEL` environment support with a local default.
- Added desktop `AIChatService` using the existing shared `ApiClient`.
- Added passive PySide6 `AIChatView` with RTL chat history, prompt input, and
  submit/loading state.
- Added `AIChatPresenter` to validate prompts, prevent duplicate sends while
  loading, append conversation messages, clear the input, and surface errors.
- Added an AI navigation item for manager, instructor, and customer workspaces.

## PRD Requirements Advanced

- `FR-AI-01` through `FR-AI-03`: users can now submit AI consultation prompts
  and receive generated text through the desktop workflow.
- `FR-AI-06`: the AI flow is read-only and exposes no operational mutation
  capability.
- `FR-AUTH-02` and `FR-AUTH-03`: the endpoint requires an authenticated user,
  and desktop navigation exposes the screen only inside an authenticated shell.
- `NFR-01` and `NFR-03`: the desktop UI includes Hebrew RTL presentation and a
  visible loading state during generation.

## Files Changed

- `backend/app/core/environment.py`
- `backend/app/main.py`
- `backend/app/application/services/ai_service.py`
- `backend/app/routers/ai.py`
- `backend/app/schemas/ai.py`
- `backend/.env.example`
- `backend/tests/test_ai_consult_api.py`
- `desktop_client/app/main.py`
- `desktop_client/app/features/ai_assistant/presenter.py`
- `desktop_client/app/shared/navigation.py`
- `desktop_client/app/features/ai_assistant/service.py`
- `desktop_client/app/features/ai_assistant/view.py`
- `desktop_client/tests/test_presenters.py`
- `desktop_client/tests/test_services.py`
- `docs/piv/14-ai-chat-ui-endpoints.md`
- `docs/piv/requirements-traceability.md`

## How To Run

Start Ollama locally with a downloaded model matching `OLLAMA_MODEL`, then run
the backend and desktop client as usual.

Example backend environment:

```powershell
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
```

The API endpoint is:

```text
POST /api/ai/consult
Authorization: Bearer <token>
Body: {"prompt": "מה כדאי להכין לאירוע?"}
```

The desktop AI screen is available from the authenticated shell navigation as
`יועץ AI`.

## Validation

- `.\.venv\Scripts\python.exe -m unittest backend.tests.test_ai_consult_api backend.tests.test_rag_llm_client desktop_client.tests.test_services desktop_client.tests.test_presenters -v`
- `.\.venv\Scripts\python.exe -m compileall backend desktop_client`

Automated tests mock the LLM client, so validation does not require a live
Ollama process.

## Next Task

The next AI task should add role-aware retrieval over approved internal
knowledge, citations/source display, and an unavailable-information response
when retrieval does not provide sufficient evidence.
