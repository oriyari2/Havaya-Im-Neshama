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
- `backend/app/core/environment.py`
- `backend/app/routers/ai.py`
- `backend/app/schemas/ai.py`
- `backend/tests/test_ai_consult_api.py`
- `backend/tests/test_rag_llm_client.py`
- `desktop_client/app/features/ai_assistant/service.py`
- `desktop_client/app/features/ai_assistant/presenter.py`
- `desktop_client/tests/test_services.py`
- `desktop_client/tests/test_presenters.py`
- `docs/piv/17-grounded-rag-only-ai-consultation.md`
- `docs/piv/requirements-traceability.md`
- `README.md`
- `rag/llm_client.py`

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

## Reliability Finalization Addendum

`POST /api/ai/consult` now keeps the existing RAG-first flow and removes the
fixed consultation completion deadline. Retrieval still runs first. If no
authorized chunks qualify, the endpoint keeps the existing
`answer_basis="none"` behavior and does not call Ollama.

When approved chunks exist, the backend calls local Ollama with `stream=true`,
consumes the NDJSON stream internally, accumulates response text server-side,
and returns only one final API response to the desktop client. Partial generated
text is never exposed to the API response or desktop UI.

The synchronous stream consumer waits while Ollama is making progress, with a
5-second connect timeout, 90-second read/idle timeout between received stream
chunks, and a 300-second generation safety cap enforced with monotonic elapsed
time checks between chunks. There are no background threads, retries, second
retrievals, or second model calls.

Retrieval remains configured for `RAG_RETRIEVAL_TOP_K=5`, but generation now
uses only the top two non-empty retrieved chunks in their original order. The
numbered prompt context is rebuilt from those two chunks, so citation indexes
`[1]` and `[2]` map exactly to the chunks supplied to `llama3.1`. Successful
`answer_basis="rag"` source records are selected only from those same generation
context chunks.

The grounded generation prompt was simplified and made Hebrew-first. It tells
the model to act as a "חוויה עם נשמה" consultant, answer only in Hebrew, use
only the attached sources, answer directly and concisely, prefer clear lists
when suitable, cite factual information with `[1]` or `[2]`, avoid unsupported
information, and return exactly `INSUFFICIENT_CONTEXT` when the sources are not
enough.

Completed-generation rejection diagnostics are now logged without user prompt,
model answer, or retrieved content. The logs distinguish
`insufficient_context`, `no_valid_citations`, and `length`. These diagnostics do
not change API output.

Final stream handling:

- `done_reason="stop"` validates citations exactly as before and returns
  `answer_basis="rag"` only for cited, supported answers.
- `done_reason="length"` discards all partial model text and returns the
  deterministic `rag_fallback`.
- `INSUFFICIENT_CONTEXT`, uncited answers, and unsupported answers keep the
  existing `answer_basis="none"` behavior.
- stream idle timeout, 300-second cap, connection failure, Ollama HTTP failure,
  malformed JSON, and incomplete/broken streams return deterministic
  `rag_fallback`.

The deterministic fallback performs no retry, second retrieval, or second model
call. It uses only the already authorized top retrieved chunks, deduplicates
logical sources, includes source names, trims content to readable snippets, and
preserves the returned source records. Empty retrieval, `INSUFFICIENT_CONTEXT`,
and uncited generated answers continue to use the existing no-answer behavior.
401/403 authentication and authorization behavior is unchanged.

The desktop presenter treats `answer_basis="rag_fallback"` as a successful
sourced assistant response, keeping the loading/duplicate-submit behavior owned
by the existing presenter operation guard.

Configuration remains on `llama3.1`, `nomic-embed-text-v2-moe`,
`keep_alive=30m`, and the existing retrieval threshold/top-k/RBAC settings.
The default `OLLAMA_NUM_PREDICT` maximum is now 400.

Focused validation for this addendum:

```powershell
.\.venv\Scripts\python.exe -m unittest backend.tests.test_rag_llm_client backend.tests.test_ai_consult_api -v
.\.venv\Scripts\python.exe -m compileall backend desktop_client rag
git diff --check
```

Focused tests cover active streams continuing beyond the old 40-second concept,
the 90-second read/idle timeout, `done_reason="stop"`,
`done_reason="length"`, generation context limited to the top two of five
retrieved chunks, citation/source mapping against those two generation chunks,
Hebrew-first grounded prompt instructions, partial stream timeout without
partial-text leakage, malformed/broken streams, the 300-second safety cap, no
retrieval results, and unchanged citation/source-deduped fallback behavior.
