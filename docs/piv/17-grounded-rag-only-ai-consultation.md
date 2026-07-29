# Task 17: Grounded RAG-Only AI Consultation

## Plan

Connect the existing Task 16 role-aware retrieval path to
`POST /api/ai/consult` without adding web search, general-model fallback,
reranking, hybrid search, or unrelated UI redesign.

The endpoint must authenticate first, retrieve with the authenticated role, and
call the LLM only when approved chunks exist.

## Implement

Updated `AIConsultationService` so consultation is RAG-only:

- trims and validates the prompt
- calls `KnowledgeRetrievalService.search(...)` before generation
- passes only `authenticated_role` from the backend auth context
- returns the fixed no-information response when retrieval has no chunks
- builds a strict grounded prompt containing only numbered retrieved chunks
- forbids guessing, general knowledge, web knowledge, and unsupported details
- requires inline `[n]` citations
- requires exact `INSUFFICIENT_CONTEXT` when the chunks are insufficient
- treats `INSUFFICIENT_CONTEXT` and uncited answers as no answer
- returns `answer_basis="rag"` only when citations identify retrieved chunks
- returns only source records actually cited by the answer

Updated `POST /api/ai/consult` to inject the existing LLM and retrieval clients,
map retrieval errors to 503, and return:

- `answer`
- `answer_basis`
- `sources`

The endpoint remains read-only and preserves fail-closed authorization. The
request body still contains only the user prompt; request-supplied role data is
ignored by the consultation flow.

Updated the desktop MVP chat minimally:

- `AIChatService.consult(...)` now returns the backend response object
- `AIChatPresenter` formats RAG answers with a compact source list under the
  assistant message

## PRD Requirements Advanced

- `FR-AI-01`: recommendations can now be generated only from retrieved approved
  activity/business knowledge.
- `FR-AI-02`: price, equipment, and preparation answers are grounded in
  approved chunks with citations.
- `FR-AI-03`: proposal-style answers remain read-only and grounded only in
  retrieved chunks.
- `FR-AI-04`: missing or insufficient retrieval evidence produces an
  unavailable-information answer instead of invented details.
- `FR-AI-05`: retrieval uses authenticated role filtering before generation.
- `FR-AI-06`: AI consultation remains read-only and cannot mutate operational
  data.

## Files Changed

- `backend/app/application/services/ai_service.py`
- `backend/app/routers/ai.py`
- `backend/app/schemas/ai.py`
- `backend/tests/test_ai_consult_api.py`
- `desktop_client/app/services/ai_chat_service.py`
- `desktop_client/app/presenters/ai_chat_presenter.py`
- `desktop_client/tests/test_services.py`
- `desktop_client/tests/test_presenters.py`
- `docs/piv/17-grounded-rag-only-ai-consultation.md`
- `docs/piv/requirements-traceability.md`
- `README.md`

## How To Run

Start PostgreSQL/Supabase-compatible persistence and the local Ollama container,
then start the backend:

```powershell
uvicorn backend.app.main:app --reload
```

Run the desktop client:

```powershell
python -m desktop_client.app.main
```

Ask questions from the AI chat screen. RAG answers show their source titles and
URIs under the answer.

## Validation

Automated validation passed:

```powershell
.\.venv\Scripts\python.exe -m unittest backend.tests.test_ai_consult_api -v
.\.venv\Scripts\python.exe -m unittest desktop_client.tests.test_services desktop_client.tests.test_presenters -v
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
.\.venv\Scripts\python.exe -m compileall backend desktop_client
git diff --check
```

Results:

- Focused AI API tests: 7 passed.
- Focused desktop service/presenter tests: 22 passed.
- Full backend unittest suite: 154 passed.
- Compile validation passed for `backend` and `desktop_client`.
- `git diff --check` passed with line-ending warnings only.

Focused tests cover:

- no retrieval results means the LLM is not called
- authenticated role is passed to retrieval
- retrieved chunks are included in the prompt
- prompt forbids unsupported/general knowledge
- successful RAG answers return sources
- `INSUFFICIENT_CONTEXT` returns `answer_basis="none"`
- restricted knowledge is not exposed when retrieval denies the role
- desktop source display works without redesign

Live validation:

`rag.reset_task16_demo_knowledge` was run first to refresh only disposable
Task 16 demo knowledge rows. It deleted 8 `knowledge_chunks`, recreated 8,
verified `nomic-embed-text-v2-moe` with 768 dimensions, confirmed unrelated
table counts were unchanged, and confirmed retrieval behavior:

- relevant equipment question as instructor retrieved `Task16 Demo Equipment`
- unsupported installments question as manager returned no chunks
- manager-only pricing as manager retrieved `Task16 Demo Pricing`
- manager-only pricing as instructor returned no chunks

Live `POST /api/ai/consult` scenarios using real auth, configured PostgreSQL,
role-aware retrieval, and local Ollama:

- relevant equipment question as instructor: HTTP 503 because generation model
  `llama3.1` is not installed in local Ollama
- unsupported installments question as manager: HTTP 200,
  `answer_basis="none"`, no LLM call
- manager-only pricing as manager: HTTP 503 because generation model
  `llama3.1` is not installed in local Ollama
- manager-only pricing as instructor: HTTP 200, `answer_basis="none"`, no LLM
  call

Ollama status checks:

- `GET /api/tags`: HTTP 200
- `GET /api/version`: HTTP 200, version `0.32.5`
- `POST /api/embed` with `nomic-embed-text-v2-moe`: HTTP 200
- `POST /api/generate` with configured generation model `llama3.1`: HTTP 404,
  `model 'llama3.1' not found`

## Next Task

Continue with the next task file only after Task 17 live validation is recorded.
Future work may improve desktop knowledge-source management or AI UX, but those
are outside this task.
