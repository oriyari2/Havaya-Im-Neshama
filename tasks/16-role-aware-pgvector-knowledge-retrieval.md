# Task 16 — Role-Aware pgvector Knowledge Retrieval

## Mandatory Project Instructions

Before making any code changes:

1. Read the repository root `AGENTS.md` completely.
2. Follow every applicable instruction in `AGENTS.md`.
3. Read the relevant project documentation, including:

   * `README.md`
   * `docs/PRD.md`
   * architecture documentation under `docs/`
   * all relevant PIV documentation under `docs/piv/`
4. Inspect the completed Task 15 implementation before designing Task 16.
5. Follow the existing project structure, naming conventions, dependency-injection style, repository patterns, authentication conventions, error-handling conventions and test style.

If this task conflicts with `AGENTS.md`, the project architecture or an existing PIV decision, follow the higher-level project instruction and report the conflict.

Execute this task according to the project’s PIV process:

```text
Plan
Implement
Validate
```

Do not skip live validation merely because mocked tests pass.

---

# Objective

Implement standalone, role-aware semantic retrieval from the existing PostgreSQL `knowledge_chunks` table using:

* the existing Ollama embedding abstraction
* `nomic-embed-text`
* PostgreSQL `pgvector`
* cosine distance
* authenticated user roles
* configurable relevance filtering
* a standalone REST endpoint

The retrieval feature must be implemented and validated independently.

Do not connect it to the AI consultation flow in this task.

---

# Current State

Task 15 already provides:

* an embedding-client abstraction
* `OllamaEmbeddingClient`
* Ollama `POST /api/embed` integration
* `nomic-embed-text`
* 768-dimensional embeddings
* PostgreSQL with the `pgvector` extension
* the `knowledge_chunks` table
* deterministic chunking and hashing
* knowledge persistence
* manager-only knowledge ingestion through:

```http
POST /api/rag/knowledge
```

The existing implementation is the source of truth.

Reuse it rather than creating a parallel embedding or database infrastructure.

---

# Required Search Flow

The retrieval flow must be:

```text
Authenticated search request
        |
        v
Normalize and validate query
        |
        v
Create query embedding
        |
        v
Determine embedding dimensions
        |
        v
Search knowledge_chunks using pgvector
        |
        v
Filter by authenticated role
        |
        v
Filter weak semantic matches
        |
        v
Return ordered knowledge chunks
```

The service must not call the LLM and must not generate an answer.

---

# API Endpoint

Implement:

```http
POST /api/rag/search
```

Use the existing RAG router if one already exists.

Do not create a competing or duplicate router.

The endpoint must require authentication and must be available to:

```text
manager
instructor
customer
```

The user role must come only from the authenticated user context.

The request must not accept a role, user ID or authorization metadata.

---

# Request Contract

Example:

```json
{
  "query": "מה צריך לבדוק לפני פעילות תפוס את האור?",
  "limit": 5
}
```

Validation rules:

* `query` is required.
* `query` must be a string.
* leading and trailing whitespace should be removed.
* an empty or whitespace-only query must be rejected.
* `limit` defaults to the configured retrieval default.
* `limit` must be between `1` and `10`.

Use Pydantic validation according to the project’s existing schema conventions.

---

# Response Contract

Example:

```json
{
  "query": "מה צריך לבדוק לפני פעילות תפוס את האור?",
  "results": [
    {
      "chunk_id": "uuid-value",
      "source_title": "מדריך ציוד - תפוס את האור",
      "source_uri": "demo://knowledge/equipment-guide",
      "chunk_index": 0,
      "content": "לפני הפעילות יש לטעון את כל יחידות האור ולבדוק את המטענים.",
      "metadata": {
        "category": "equipment",
        "language": "he",
        "allowed_roles": [
          "manager",
          "instructor"
        ]
      },
      "distance": 0.18,
      "score": 0.82
    }
  ]
}
```

Requirements:

* Results must be ordered from the smallest distance to the largest distance.
* `distance` is the cosine distance returned by pgvector.
* `score` is calculated as:

```text
score = 1 - distance
```

* Do not expose the stored embedding.
* Do not expose internal database fields that are not part of the API contract.
* Preserve metadata as structured JSON.

When there are no authorized and sufficiently relevant results, return HTTP 200:

```json
{
  "query": "original query",
  "results": []
}
```

An empty result is not an error.

---

# Retrieval Repository

Add a repository dedicated to semantic knowledge retrieval, following the existing repository structure.

A possible name is:

```text
knowledge_retrieval_repository.py
```

Do not force this path if the repository already has a different established convention.

The repository must receive:

* query embedding
* authenticated role
* embedding model
* embedding dimensions
* result limit
* maximum allowed cosine distance, if filtering is performed in SQL

The repository must:

* query `knowledge_chunks`
* use parameterized SQL
* use the pgvector cosine-distance operator:

```sql
<=>
```

* filter by the configured embedding model
* filter by the actual query-vector dimensions
* enforce role authorization
* order by cosine distance
* apply a bounded result limit
* return structured rows
* never return unauthorized rows

Reuse the project’s existing vector-serialization logic.

Do not introduce a second vector representation unless required by the current database abstraction.

---

# Role-Aware Retrieval Policy

Authorization must be fail-closed.

## Manager

A manager may retrieve every knowledge chunk.

The manager is not restricted by `metadata.allowed_roles`.

## Instructor

An instructor may retrieve a chunk only when:

```text
metadata.allowed_roles
```

is a valid array containing:

```text
instructor
```

## Customer

A customer may retrieve a chunk only when:

```text
metadata.allowed_roles
```

is a valid array containing:

```text
customer
```

## Missing or Invalid Authorization Metadata

Treat a chunk as manager-only when `allowed_roles`:

* is missing
* is null
* is not an array
* is malformed
* does not contain the authenticated role

Authorization filtering must be enforced in the repository/database query.

It is not sufficient to retrieve all matching chunks and remove unauthorized chunks only in the router.

---

# Retrieval Service

Add a retrieval service following the existing service or application-layer conventions.

A possible name is:

```text
KnowledgeRetrievalService
```

The service must:

1. normalize the query
2. create an embedding using the existing embedding client
3. reject an empty embedding
4. determine the actual embedding dimensions
5. pass the configured embedding-model name to the repository
6. pass the authenticated role to the repository
7. pass the validated result limit
8. filter weak matches if the repository does not already do so
9. calculate `score = 1 - distance`
10. preserve relevance order
11. return structured search results

The service must not:

* call `OllamaLLMClient`
* build an AI prompt
* generate an answer
* modify the AI consultation endpoint

---

# Retrieval Constants

Use the following internal application constants:

```python
RAG_MAX_COSINE_DISTANCE = 0.45
RAG_RETRIEVAL_TOP_K = 5
```

They must be defined in:

```text
backend/app/core/environment.py
```

They are code-level MVP defaults, not deployment `.env` settings. Do not read
them from `.env`, and do not list them in `.env.example`.

Requirements:

## `RAG_MAX_COSINE_DISTANCE`

* default: `0.45`
* internal code constant
* not configurable through `.env`

## `RAG_RETRIEVAL_TOP_K`

* default: `5`
* internal code constant
* not configurable through `.env`
* must be between `1` and `10`
* the API must never allow more than `10`

The threshold is an initial MVP value.

Its effectiveness must be checked using real Hebrew retrieval before Task 17
integrates retrieved context into generated AI answers.

---

# Error Handling

Follow the project’s existing API and exception conventions.

Handle at least:

## Invalid Request

Return the project’s normal validation response for:

* missing query
* whitespace-only query
* `limit` below 1
* `limit` above 10

## Embedding Failure

When Ollama embedding generation fails:

* use the existing embedding-client exception
* convert it through the project’s normal API error handling
* do not expose stack traces or internal connection details

## Database Failure

A failed database query must not be converted into a successful empty result.

Use the project’s existing database-error behavior.

## No Results

No matching results must return HTTP 200 with an empty `results` list.

---

# Required Automated Tests

Add focused tests for Task 16 using the project’s existing testing style.

A possible test module is:

```text
backend/tests/test_task16_rag_retrieval.py
```

Use a different location only if required by the existing test organization.

## Service Tests

Test that:

1. the normalized query is passed to the embedding client
2. the returned vector is passed to the repository
3. the actual vector dimensions are passed to the repository
4. the configured embedding model is passed to the repository
5. the authenticated role is passed to the repository
6. the validated limit is passed to the repository
7. results preserve distance order
8. score is calculated as `1 - distance`
9. weak matches are removed
10. an empty repository result returns an empty list
11. an empty embedding is rejected
12. an embedding-client failure is handled correctly

## Repository Tests

Test observable behavior for:

1. cosine distance retrieval
2. ordering by distance
3. bounded result limits
4. embedding-model filtering
5. embedding-dimension filtering
6. manager access to all chunks
7. instructor access only to allowed chunks
8. customer access only to allowed chunks
9. missing `allowed_roles` being manager-only
10. null `allowed_roles` being manager-only
11. malformed `allowed_roles` being manager-only
12. multiple allowed roles
13. no unauthorized rows being returned

Avoid brittle tests that depend on the full SQL string unless the existing repository-test style requires them.

## Router Tests

Test that:

1. unauthenticated access is rejected
2. manager can search
3. instructor can search
4. customer can search
5. the request cannot override the authenticated role
6. whitespace-only queries are rejected
7. `limit=0` is rejected
8. `limit=11` is rejected
9. an empty search result returns HTTP 200
10. successful responses match the response schema
11. embeddings are not exposed

---

# Live PIV Validation

Automated tests are not sufficient.

Perform live validation against the local services when available:

* Ollama
* `nomic-embed-text`
* PostgreSQL
* pgvector
* real `knowledge_chunks`

Validate at least the following cases.

## Case 1 — Relevant Hebrew Retrieval

Use approved knowledge such as:

```text
לפני פעילות תפוס את האור יש לטעון את יחידות האור,
לבדוק את המטענים ולוודא שכל ערכות הציוד מלאות.
```

Search with:

```text
מה צריך לבדוק לפני פעילות תפוס את האור?
```

Expected:

* the relevant source is returned
* it appears near the top
* it passes the configured distance threshold

If controlled Hebrew validation does not show reliable semantic ranking, record
the evidence as a blocker for Task 17 rather than claiming Hebrew retrieval has
passed.

## Case 2 — Role Isolation

Use manager-only knowledge.

Expected:

* manager can retrieve it
* instructor cannot retrieve it
* customer cannot retrieve it

## Case 3 — Customer Knowledge

Use knowledge allowed for `customer`.

Expected:

* customer can retrieve it
* instructor cannot retrieve it unless `instructor` is also allowed

## Case 4 — Unrelated Query

Search for information that is not present in the approved knowledge base.

Expected:

```json
{
  "results": []
}
```

Record the actual distances observed during live validation.

Do not change the threshold solely to force one specific sample to pass.
If unrelated Hebrew content is not filtered reliably, document that as unresolved
Hebrew retrieval quality rather than treating Task 16 as ready for AI-chat
integration.

---

# Documentation and PIV Record

Update documentation only where required.

Document:

* `POST /api/rag/search`
* `RAG_MAX_COSINE_DISTANCE`
* `RAG_RETRIEVAL_TOP_K`
* role-aware filtering
* fail-closed authorization behavior
* the fact that retrieval is independent from AI answer generation

Use wording such as:

```text
Role-aware semantic retrieval from approved knowledge is implemented.
Retrieved context is not yet integrated into the AI consultation prompt.
```

Do not claim that complete RAG integration is finished.

Create or update the appropriate Task 16 PIV documentation according to the existing naming and formatting conventions under:

```text
docs/piv/
```

The PIV record should document:

* Plan
* implementation decisions
* files changed
* validation commands
* automated test results
* live validation results
* observed cosine distances
* the distinction between completed retrieval infrastructure and unresolved
  Hebrew semantic-quality validation
* known limitations
* next recommended task

Do not invent a new PIV structure if one already exists.

---

# Out of Scope

Do not implement:

* integration with `POST /api/ai/consult`
* AI prompt grounding
* LLM answer generation
* citations in AI answers
* AI abstention behavior
* knowledge source listing
* knowledge source deletion
* source-management UI
* PDF ingestion
* hybrid search
* reranking
* vector-index optimization
* desktop UI changes
* unrelated refactoring
* commits
* pushes

Do not alter existing Task 15 ingestion behavior unless a minimal correction is required to unblock retrieval.

---

# Required Validation Commands

Run the focused Task 16 tests using the project’s actual test layout.

Expected command if the suggested module is used:

```powershell
.\.venv\Scripts\python.exe -m unittest backend.tests.test_task16_rag_retrieval -v
```

Run the complete backend suite:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
```

Run compilation validation:

```powershell
.\.venv\Scripts\python.exe -m compileall backend desktop_client rag
```

Run whitespace validation:

```powershell
git diff --check
```

If the repository uses different commands, use the existing project convention and report the exact commands used.

---

# Acceptance Criteria

Task 16 retrieval infrastructure is complete only when:

* the query is embedded using the existing embedding client
* retrieval uses pgvector cosine distance
* results are ordered by relevance
* embedding model and dimensions are filtered
* weak results are excluded
* role authorization is enforced in the repository query
* missing or malformed role metadata is manager-only
* manager, instructor and customer access is tested
* `/api/rag/search` works
* embeddings are not exposed
* focused tests pass
* the complete backend suite passes
* compilation validation passes
* `git diff --check` passes
* live role isolation passes
* actual distances are documented
* the appropriate PIV record is created or updated
* retrieval was not connected to the AI chat
* no unrelated features were added
* no commit or push was performed

Hebrew semantic-quality validation is a separate blocker before Task 17. Do not
claim Task 16 proves reliable Hebrew retrieval until controlled validation shows
that relevant Hebrew queries rank correctly and unrelated Hebrew queries are
filtered out. Task 17 must not begin until the embedding behavior is understood
or corrected.

---

# Required Final Report

Report:

1. the Plan used
2. implementation summary
3. exact files created
4. exact files modified
5. repository design
6. service flow
7. authorization policy
8. endpoint contract
9. retrieval constants added
10. focused test command and result
11. complete backend test command and result
12. compilation result
13. `git diff --check` result
14. live validation procedure
15. actual live results and distances
16. PIV documentation created or updated
17. limitations and follow-up recommendations
18. confirmation that no commit or push was performed
