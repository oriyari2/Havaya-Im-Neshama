# Task 15: Vector Database and RAG Ingestion Infrastructure

## Plan

Build the first persistent RAG ingestion slice inside the existing FastAPI and PostgreSQL architecture. The task supports `FR-AI-02`, `FR-AI-04`, `FR-AI-05`, `FR-AI-06`, and especially `FR-AI-07` by creating approved-knowledge chunk storage and a controlled manager-only ingestion flow.

Out of scope for this task: retrieval ranking, role-filtered citations, desktop knowledge-source screens, and changing the AI consult endpoint to use retrieved context.

## Implement

Created PostgreSQL vector storage in `backend/app/db/schema.py`:

- Enables `pgcrypto` and `vector`.
- Adds `knowledge_chunks` for approved source title, URI, chunk text, metadata, embedding model, embedding dimensions, pgvector embedding, content hash, creator, and timestamp.
- Adds indexes for source title and content hash.

Created Ollama embedding infrastructure:

- `rag/embedding_client.py` defines `EmbeddingClient`, `EmbeddingClientError`, and `OllamaEmbeddingClient`.
- `backend/app/core/environment.py` adds `OLLAMA_EMBEDDING_MODEL`, defaulting to `nomic-embed-text`.
- `rag/__init__.py` exports the embedding interface.

Created ingestion application flow:

- `backend/app/schemas/knowledge.py` defines ingestion request/response DTOs.
- `backend/app/infrastructure/repositories/knowledge_repository.py` inserts chunk rows with parameterized SQL and pgvector casts.
- `backend/app/application/services/knowledge_ingestion_service.py` normalizes text, chunks it deterministically, embeds each chunk, hashes chunk content, and stores all chunks in one transaction.
- `backend/app/routers/knowledge.py` adds manager-only `POST /api/rag/knowledge`.
- `backend/app/main.py` registers the RAG ingestion router.

Also aligned `rag/llm_client.py` default timeout with the existing test contract.

## Validate

Automated validation passed:

```powershell
.\.venv\Scripts\python.exe -m unittest backend.tests.test_task15_rag_ingestion
.\.venv\Scripts\python.exe -m unittest discover backend/tests
.\.venv\Scripts\python.exe -m compileall backend desktop_client
```

Results:

- Task 15 focused tests: 7 passed.
- Full backend unittest suite: 123 passed.
- Compile validation passed for backend and desktop client.

The tests verify:

- Ollama embedding requests call `/api/embeddings` with the configured model.
- Embedding transport failures are translated into application errors.
- Text chunking is deterministic and uses overlap.
- Ingestion embeds and stores chunks through the repository layer.
- Repository SQL stores pgvector data through parameterized values.
- The API denies non-manager ingestion and supports dependency-injected service testing.

Database-backed validation against Supabase/PostgreSQL was not run in this pass because it would require a live configured database and Ollama embedding model. The schema is ready for the existing `/system/init-db` flow.

## Requirement Traceability

Advanced:

- `FR-AI-02`: approved knowledge can now be stored as embedded chunks for future grounded answers.
- `FR-AI-04`: future abstention behavior has the required persisted retrieval substrate.
- `FR-AI-05`: metadata storage prepares chunks for future role-aware retrieval filters.
- `FR-AI-06`: the ingestion route only writes knowledge chunks; the AI consult flow remains read-only for operational data.
- `FR-AI-07`: manager-controlled ingestion chunks, embeds, and stores approved knowledge.

## Next Task

Implement retrieval over `knowledge_chunks`, including vector similarity search, role/audience filtering from metadata, citations/source references, and abstention when no retrieved chunk is sufficient.
