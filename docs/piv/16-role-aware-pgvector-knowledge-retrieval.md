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

## Corrected Continuation: Task 16 Evaluation

Plan: keep production retrieval compatible with existing `knowledge_chunks`, do not delete or re-ingest production knowledge, correct the isolated Hebrew evaluation fixture and metrics, compare thresholds before recommending any model, and keep `/api/ai/consult` blocked.

Implementation corrections:

- `rag/evaluation_fixture_task16_he.json` now contains 44 demo-only Hebrew cases: 27 relevant cases and 17 unrelated cases.
- Added hard negatives for cancellation policy, transportation, food inclusion, installments, instructor count, age-three suitability, rain plan, and insurance. All use `should_retrieve: false`.
- `rag/evaluation.py` now reports relevant accepted/rejected, unrelated accepted/rejected, precision, recall, false-positive rate, unrelated rejection rate, accepted Top-1 accuracy, wrong Top-1 accepted count, forbidden-source accepted count, unauthorized retrieval count, and first accepted expected-source count.
- A relevant case is accepted only when an expected source passes the threshold.
- The evaluator separately reports exact failures with query, authenticated role, expected sources, forbidden sources, returned titles, returned distances, threshold pass booleans, and failure reason.
- Threshold candidates now include explicit thresholds, every first-result distance, every expected-source distance, and midpoints between relevant and unrelated distances.
- The isolated evaluator still inserts only temporary `eval://task16-hebrew-model-comparison/...` rows and cleans them up in `try/finally`.

Production/evaluation isolation remains unchanged:

- Production ingestion embeds plain chunk text.
- Production retrieval embeds the plain normalized query.
- `OLLAMA_EMBEDDING_MODEL` and `RAG_MAX_COSINE_DISTANCE = 0.45` were not changed.
- Existing production knowledge was not deleted or re-ingested.

Corrected raw metrics:

| Model | Dims | Raw Top-1 | Raw Top-3 | Relevant first distance | Unrelated first distance | Relevant expected-source range | Unrelated result range | Unauthorized | Forbidden |
|---|---:|---:|---:|---|---|---|---|---:|---:|
| `nomic-embed-text` | 768 | 0.407 | 0.704 | 0.285-0.362 | 0.309-0.369 | 0.285-0.366 | 0.309-0.386 | 0 | 0 |
| `nomic-embed-text-v2-moe` | 768 | 0.963 | 1.000 | 0.345-0.649 | 0.592-0.914 | 0.345-0.683 | 0.592-0.966 | 0 | 0 |
| `bge-m3` | 1024 | 0.926 | 1.000 | 0.259-0.506 | 0.454-0.775 | 0.259-0.506 | 0.454-0.785 | 0 | 0 |

Explicit `nomic-embed-text-v2-moe` thresholds from `0.60` through `0.73`:

| Threshold | Relevant accepted/rejected | Unrelated accepted/rejected | Precision | Recall | FPR | Unrelated rejection | Accepted Top-1 | Wrong accepted Top-1 | Forbidden accepted | Unauthorized |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.60 | 19 / 8 | 1 / 16 | 0.950 | 0.704 | 0.059 | 0.941 | 1.000 | 0 | 0 | 0 |
| 0.61 | 19 / 8 | 1 / 16 | 0.950 | 0.704 | 0.059 | 0.941 | 1.000 | 0 | 0 | 0 |
| 0.62 | 21 / 6 | 1 / 16 | 0.955 | 0.778 | 0.059 | 0.941 | 1.000 | 0 | 0 | 0 |
| 0.63 | 21 / 6 | 2 / 15 | 0.913 | 0.778 | 0.118 | 0.882 | 1.000 | 0 | 0 | 0 |
| 0.64 | 26 / 1 | 2 / 15 | 0.929 | 0.963 | 0.118 | 0.882 | 0.962 | 1 | 0 | 0 |
| 0.65 | 27 / 0 | 2 / 15 | 0.931 | 1.000 | 0.118 | 0.882 | 0.963 | 1 | 0 | 0 |
| 0.66 | 27 / 0 | 2 / 15 | 0.931 | 1.000 | 0.118 | 0.882 | 0.963 | 1 | 0 | 0 |
| 0.67 | 27 / 0 | 3 / 14 | 0.900 | 1.000 | 0.176 | 0.824 | 0.963 | 1 | 0 | 0 |
| 0.68 | 27 / 0 | 3 / 14 | 0.900 | 1.000 | 0.176 | 0.824 | 0.963 | 1 | 0 | 0 |
| 0.69 | 27 / 0 | 3 / 14 | 0.900 | 1.000 | 0.176 | 0.824 | 0.963 | 1 | 0 | 0 |
| 0.70 | 27 / 0 | 3 / 14 | 0.900 | 1.000 | 0.176 | 0.824 | 0.963 | 1 | 0 | 0 |
| 0.71 | 27 / 0 | 4 / 13 | 0.871 | 1.000 | 0.235 | 0.765 | 0.963 | 1 | 0 | 0 |
| 0.72 | 27 / 0 | 5 / 12 | 0.844 | 1.000 | 0.294 | 0.706 | 0.963 | 1 | 0 | 0 |
| 0.73 | 27 / 0 | 5 / 12 | 0.844 | 1.000 | 0.294 | 0.706 | 0.963 | 1 | 0 | 0 |

A threshold around `0.69` accepts all 27 relevant cases but also accepts 3 of 17 unrelated hard negatives, so it is not acceptable for RAG-only behavior.

Recommended model candidate: `nomic-embed-text-v2-moe`. It has the strongest raw Top-1 accuracy, full raw Top-3 recall, zero unauthorized retrieval, zero forbidden retrieval, and better corrected separation than `bge-m3`.

Recommended threshold candidate for a future production experiment: generated threshold `0.581186`. It accepts 19/27 relevant cases, rejects 17/17 unrelated cases, has precision `1.000`, recall `0.704`, false-positive rate `0.000`, unrelated rejection `1.000`, accepted Top-1 accuracy `1.000`, wrong accepted Top-1 count `0`, forbidden accepted count `0`, and unauthorized accepted count `0`. This was not applied to production.

Exact failure summary at explicit threshold `0.55`: 11 relevant cases were rejected because their expected source did not pass the threshold. No unrelated, forbidden, or unauthorized case passed at `0.55`.

Exact failure summary at threshold `0.69`: 4 cases failed. One relevant case, `?? ????? ????? ????????`, accepted `Task16 Eval Preparation` before the expected `Task16 Eval Activity`. Three unrelated hard negatives were accepted: transportation, food-in-price, and instructor-count questions.

Validation results:

- `.\.venv\Scripts\python.exe -m unittest backend.tests.test_task15_rag_ingestion -v`: 11 passed.
- `.\.venv\Scripts\python.exe -m unittest backend.tests.test_task16_rag_retrieval -v`: 23 passed.
- Live `.\.venv\Scripts\python.exe -m rag.evaluate_task16_live`: completed after enabling UTF-8 console output.
- Cleanup verification for `source_uri LIKE 'eval://task16-hebrew-model-comparison/%'`: `0`.

Next work should continue Task 16 by deciding whether to adjust the fixture, add retrieval mitigation such as abstention/reranking/hybrid search, or run a controlled production-formatting experiment. Do not create Task 16.1 and do not begin Task 17 yet.
