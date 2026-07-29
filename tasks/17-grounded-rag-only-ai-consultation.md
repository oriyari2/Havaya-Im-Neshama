# Task 17 — Grounded RAG-Only AI Consultation

## Goal

Connect the existing role-aware RAG retrieval to `POST /api/ai/consult`.

The AI must answer only from approved retrieved knowledge. If the retrieved context is missing or insufficient, return a fixed “no information” response. No fallback to general model knowledge or the web.

## Required Behavior

1. Authenticate the user and use only the authenticated role.
2. Call the existing `KnowledgeRetrievalService` before the LLM.
3. If retrieval returns no chunks:
   - do not call the LLM
   - return:
   ```json
   {
     "answer": "לא נמצא במאגר הידע המאושר מידע מספיק כדי לענות על השאלה.",
     "answer_basis": "none",
     "sources": []
   }
   ```
4. If chunks are found:
   - send only those chunks to the LLM
   - number them `[1]`, `[2]`, etc.
   - instruct the LLM to answer only from the provided context
   - forbid guessing, general knowledge, web knowledge, and unsupported details
   - require inline references such as `[1]`
   - require the exact sentinel `INSUFFICIENT_CONTEXT` when the context is insufficient
5. If the LLM returns `INSUFFICIENT_CONTEXT`, return the same `answer_basis="none"` response.
6. Successful response:
   ```json
   {
     "answer": "תשובה מבוססת מקור [1].",
     "answer_basis": "rag",
     "sources": [
       {
         "chunk_id": "uuid",
         "source_title": "title",
         "source_uri": "uri"
       }
     ]
   }
   ```
7. Return only sources actually used by the answer.
8. Preserve fail-closed role authorization. Never accept `role` from the request body.
9. Minimally update the desktop chat to show sources under RAG answers.

## Tests

Add tests proving:

- no retrieval results means the LLM is not called
- authenticated role is passed to retrieval
- retrieved chunks are included in the prompt
- the prompt forbids unsupported/general knowledge
- successful RAG answers return sources
- `INSUFFICIENT_CONTEXT` returns `answer_basis="none"`
- restricted knowledge is not exposed to unauthorized roles
- desktop source display works without redesign

## Validation

Run focused tests, the full backend suite, `compileall`, `git diff --check`, and live checks for:

- relevant equipment question
- unsupported installments question
- manager-only pricing as manager
- manager-only pricing as instructor

## Out of Scope

- web search
- general-model fallback
- mixed RAG/general answers
- reranking or hybrid search
- unrelated refactoring
- commit or push

## Documentation

Update:

- Task 17 PIV
- requirements traceability
- README
