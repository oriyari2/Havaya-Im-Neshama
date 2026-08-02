from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from uuid import UUID

from psycopg.rows import dict_row
from rag import EmbeddingClient, EmbeddingClientError
from rag.embedding_formatting import format_query_embedding_input

from backend.app.core.environment import get_ollama_embedding_model, get_rag_max_cosine_distance
from backend.app.db.connection import get_connection
from backend.app.infrastructure.repositories import knowledge_retrieval_repository


class KnowledgeRetrievalError(RuntimeError):
    """Raised when approved knowledge retrieval cannot be completed."""


@dataclass(frozen=True)
class KnowledgeSearchResultData:
    chunk_id: UUID
    source_title: str
    source_uri: str | None
    chunk_index: int
    content: str
    metadata: dict
    distance: float
    score: float


@dataclass(frozen=True)
class KnowledgeSearchData:
    query: str
    results: list[KnowledgeSearchResultData]
    embedding_ms: float = 0.0
    retrieval_ms: float = 0.0


class KnowledgeRetrievalService:
    def __init__(self, embedding_client: EmbeddingClient, *, max_cosine_distance: float | None = None) -> None:
        self.embedding_client = embedding_client
        self.max_cosine_distance = get_rag_max_cosine_distance() if max_cosine_distance is None else max_cosine_distance

    def search(self, *, query: str, authenticated_role: str, limit: int) -> KnowledgeSearchData:
        normalized_query = query.strip()
        if not normalized_query:
            raise ValueError("Query must not be empty")
        embedding_model = getattr(self.embedding_client, "model", None) or get_ollama_embedding_model()
        try:
            embedding_input = format_query_embedding_input(model=embedding_model, query=normalized_query)
            embedding_started = perf_counter()
            embedding = self.embedding_client.embed(embedding_input)
            embedding_ms = (perf_counter() - embedding_started) * 1000
        except EmbeddingClientError as exc:
            raise KnowledgeRetrievalError("Embedding service is unavailable") from exc
        if not embedding:
            raise KnowledgeRetrievalError("Embedding service returned an empty vector")

        embedding_dimensions = len(embedding)
        retrieval_started = perf_counter()
        with get_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                rows = knowledge_retrieval_repository.search_knowledge_chunks(
                    cur,
                    query_embedding=embedding,
                    authenticated_role=authenticated_role,
                    embedding_model=embedding_model,
                    embedding_dimensions=embedding_dimensions,
                    limit=limit,
                    max_cosine_distance=self.max_cosine_distance,
                )
        retrieval_ms = (perf_counter() - retrieval_started) * 1000

        results = [
            KnowledgeSearchResultData(
                chunk_id=row["chunk_id"],
                source_title=row["source_title"],
                source_uri=row["source_uri"],
                chunk_index=row["chunk_index"],
                content=row["content"],
                metadata=row["metadata"] or {},
                distance=float(row["distance"]),
                score=1 - float(row["distance"]),
            )
            for row in rows
            if float(row["distance"]) <= self.max_cosine_distance
        ]
        return KnowledgeSearchData(query=normalized_query, results=results, embedding_ms=embedding_ms, retrieval_ms=retrieval_ms)
