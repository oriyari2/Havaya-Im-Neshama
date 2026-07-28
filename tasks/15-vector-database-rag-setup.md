# Task 15: Vector Database & RAG Ingestion Infrastructure

## Objective
Establish the foundational infrastructure for vector-based RAG by enabling vector storage capabilities in PostgreSQL, setting up embedding generation (via Ollama), and allowing document/knowledge chunk ingestion.

## Requirements
1. **Database Schema (Vector Support):**
   - Create or update a database migration/schema in `backend/app/db/` to support storing text chunks alongside their vector embeddings (using PostgreSQL vector extensions or structured metadata tables compatible with the current setup).
2. **Embedding Client:**
   - Extend the `rag/` package or create an embedding service (e.g., using Ollama's embedding endpoint or a lightweight local method) to convert text snippets into vector representations.
3. **Ingestion API / Service:**
   - Create a backend service/endpoint allowing administrative ingestion of internal knowledge (e.g., equipment guides, event rules, customer constraints) so they can be chunked, embedded, and stored.
4. **Testing:**
   - Add unit/integration tests verifying that text can be processed, embedded, and stored correctly through the repository layer.

## Constraints
- Keep the design aligned with the existing FastAPI, repository, and CQRS/MVP patterns.
- Avoid introducing external vector DB containers (like Qdrant); utilize the existing PostgreSQL architecture to keep deployment simple and unified.