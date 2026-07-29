# Task 16: Role-Aware pgvector Knowledge Retrieval

## Plan

Implement standalone retrieval over the Task 15 `knowledge_chunks` table without
connecting it to `POST /api/ai/consult`.

The slice supports `FR-AI-02`, `FR-AI-05`, and `FR-AI-07` by embedding an
authenticated search query, retrieving approved knowledge with pgvector cosine
distance, applying fail-closed role filtering in SQL, and returning structured
chunks without stored embeddings.

## Implement

Added retrieval defaults as internal application constants in
`backend/app/core/environment.py`:

- `RAG_MAX_COSINE_DISTANCE = 0.45`
- `RAG_RETRIEVAL_TOP_K = 5`

These values are not deployment `.env` settings.

Added `POST /api/rag/search` to the existing RAG router. The endpoint accepts a
trimmed `query` and optional `limit`, requires authentication for `manager`,
`instructor`, or `customer`, and always uses the authenticated role rather than
request-supplied authorization metadata.
`KnowledgeSearchRequest` rejects unexpected fields with Pydantic
`extra="forbid"`, so a request containing `role` returns HTTP 422.

Added `KnowledgeRetrievalService`:

- normalizes query text
- embeds the query through the existing Task 15 embedding client
- rejects empty embeddings
- passes embedding model, actual dimensions, authenticated role, bounded limit,
  and cosine-distance threshold constant to the repository
- calculates `score = 1 - distance`
- preserves relevance order

Added `knowledge_retrieval_repository.search_knowledge_chunks`:

- uses parameterized SQL
- uses pgvector cosine distance with `<=>`
- filters by `embedding_model`
- filters by actual `embedding_dimensions`
- enforces role authorization in the database query
- applies the cosine-distance threshold and bounded result limit
- returns no embeddings

Authorization is fail-closed:

- managers can retrieve every chunk
- instructors require valid `metadata.allowed_roles` containing `instructor`
- customers require valid `metadata.allowed_roles` containing `customer`
- missing, null, non-array, or malformed `allowed_roles` is manager-only

Retrieved context is not yet integrated into the AI consultation prompt.

## Files Changed

Created:

- `backend/app/application/services/knowledge_retrieval_service.py`
- `backend/app/infrastructure/repositories/knowledge_retrieval_repository.py`
- `backend/tests/test_task16_rag_retrieval.py`
- `docs/piv/16-role-aware-pgvector-knowledge-retrieval.md`

Modified:

- `backend/.env.example`
- `backend/app/core/environment.py`
- `backend/app/routers/knowledge.py`
- `backend/app/schemas/knowledge.py`
- `docs/piv/requirements-traceability.md`
- `README.md`

## Validate

Automated validation passed:

```powershell
.\.venv\Scripts\python.exe -m unittest backend.tests.test_task16_rag_retrieval -v
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
.\.venv\Scripts\python.exe -m compileall backend desktop_client rag
git diff --check
```

Results:

- Focused Task 16 tests: 14 passed.
- Full backend unittest suite: 141 passed.
- Compile validation passed for `backend`, `desktop_client`, and `rag`.
- `git diff --check` passed with line-ending warnings only.

Live validation used local Ollama, `nomic-embed-text`, PostgreSQL, pgvector, and
real `knowledge_chunks` rows inserted through the existing Task 15 repository.
Temporary validation rows used source titles beginning with `Task16 Live` and
were removed after validation. The live validation procedure now requires
cleanup in a `try/finally` block or equivalent so temporary data does not remain
in `knowledge_chunks`.

Leftover temporary validation rows were found and removed before revalidation:

- `Task16 Live Customer Preparation`
- `Task16 Live Equipment - Catch the Light`
- `Task16 Live Manager Only Pricing Notes`

Controlled Hebrew validation then inserted three temporary rows whose titles
began with `Task16 Live Controlled`, queried them, and deleted them in a
`finally` cleanup block. Document embeddings and query embeddings both used:

- model: `nomic-embed-text`
- endpoint: `http://localhost:11434`
- Ollama response path: `/api/embed` `embeddings[0]`
- dimensions: `768`

Stored-vector checks for the controlled set:

- row count: `3`
- distinct stored vectors: `3`
- min/max `vector_dims(embedding)`: `768` / `768`

Manager-scoped controlled distances against the same three semantically
different documents:

| Query | Document | Distance | Passes 0.45 |
|---|---|---:|---|
| relevant: `מה צריך לבדוק לפני פעילות תפוס את האור?` | Manager Pricing | `0.041631` | yes |
| relevant: `מה צריך לבדוק לפני פעילות תפוס את האור?` | Equipment Catch the Light | `0.047522` | yes |
| relevant: `מה צריך לבדוק לפני פעילות תפוס את האור?` | Customer Arrival | `0.050360` | yes |
| paraphrased: `איך מכינים את ציוד האורות לפני האירוע?` | Manager Pricing | `0.041631` | yes |
| paraphrased: `איך מכינים את ציוד האורות לפני האירוע?` | Equipment Catch the Light | `0.047522` | yes |
| paraphrased: `איך מכינים את ציוד האורות לפני האירוע?` | Customer Arrival | `0.050360` | yes |
| unrelated: `איזה מסלול חללית מתאים למחקר על כוכבי לכת רחוקים?` | Manager Pricing | `0.030782` | yes |
| unrelated: `איזה מסלול חללית מתאים למחקר על כוכבי לכת רחוקים?` | Equipment Catch the Light | `0.033741` | yes |
| unrelated: `איזה מסלול חללית מתאים למחקר על כוכבי לכת רחוקים?` | Customer Arrival | `0.036086` | yes |

The previous identical-vector result was rechecked with a controlled diagnostic
that constructs the two Hebrew queries using Python Unicode escapes, records the
outgoing `OllamaEmbeddingClient` input strings, and compares full vectors by
stable SHA-256 hash rather than distance alone.

Diagnostic results:

| Path | Query 1 hash | Query 2 hash | Dims | Exact equal | Cosine distance |
|---|---|---|---:|---|---:|
| `OllamaEmbeddingClient` | `b1964ad0e31432d6c557ec74ab15f7be708d23f2f9450c03143e78baec101660` | `caec3af6e2a92c070b04031b7f738d46690f7dba080aa9d4d73f2d5f8a839763` | `768` / `768` | no | `0.105980997260` |
| Direct `POST /api/embed` | `b1964ad0e31432d6c557ec74ab15f7be708d23f2f9450c03143e78baec101660` | `caec3af6e2a92c070b04031b7f738d46690f7dba080aa9d4d73f2d5f8a839763` | `768` / `768` | no | `0.105980997260` |
| Batch `POST /api/embed` | `b1964ad0e31432d6c557ec74ab15f7be708d23f2f9450c03143e78baec101660` | `caec3af6e2a92c070b04031b7f738d46690f7dba080aa9d4d73f2d5f8a839763` | `768` / `768` | no | `0.105980997260` |

The outgoing query text hashes were also different:

- Query 1 text hash:
  `601afccb5cd871f33505652ef863ea6e9d2897e8654975c4c82b0a116f57b6d3`.
- Query 2 text hash:
  `a224192dc33a960532bb2a783f4e876d7f02670d2c74d5c5fd54cb1f4246e63b`.

Direct Ollama responses used the expected structure with top-level
`embeddings`, `model`, `total_duration`, `load_duration`, and
`prompt_eval_count`; vectors were parsed from `embeddings[0]`. Direct responses
matched the client responses exactly. Batch `POST /api/embed` returned two
vectors under `embeddings`.

Root-cause classification for the identical-vector observation:
validation-script defect. The earlier diagnostic did not reliably preserve the
Hebrew input text. The retrieval implementation's client request and
`embeddings[0]` response parsing were not shown to be defective.

Temporary rows did not distort the controlled retrieval result because they were
deleted before and after the controlled run.

Validation cases covered:

- relevant Hebrew retrieval for Catch the Light preparation/equipment knowledge
- manager-only knowledge visible to manager but not instructor/customer
- customer knowledge visible to customer and isolated from instructor unless
  both roles are allowed
- unrelated English approved-knowledge query returning an empty result list

The controlled live validation does not prove reliable Hebrew semantic
retrieval. Endpoint behavior, authorization, SQL retrieval, role filtering, and
automated tests are complete, but Hebrew model quality remains a known blocker
before AI-chat integration. Task 17 must not begin until the embedding behavior
is understood or corrected, or an evidence-based mitigation is selected.

## Known Limitations

The retrieval endpoint returns matching approved chunks only. It does not call
the LLM, generate an answer, produce citations in AI answers, or enforce
abstention behavior in `POST /api/ai/consult`.

No implementation defect was found in the current retrieval client or response
parsing. The remaining issue is unresolved Hebrew retrieval reliability, not a
completed AI-chat grounding result. The retrieval threshold was not changed and
the embedding model was not switched in this correction pass.

## Next Task

Task 16.1 - Investigate and validate Hebrew embedding quality.

Task 17 remains blocked until the Hebrew retrieval issue is resolved or an
evidence-based mitigation is selected. Do not immediately integrate retrieval
into `/api/ai/consult`.
