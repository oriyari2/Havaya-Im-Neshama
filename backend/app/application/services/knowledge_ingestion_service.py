from __future__ import annotations

from dataclasses import dataclass
import hashlib
from uuid import UUID

from psycopg.rows import dict_row
from rag import EmbeddingClient, EmbeddingClientError, OllamaEmbeddingClient

from backend.app.core.environment import get_ollama_embedding_model
from backend.app.db.connection import get_connection
from backend.app.infrastructure.repositories import knowledge_repository
from backend.app.schemas.knowledge import KnowledgeIngestRequest


class KnowledgeIngestionError(RuntimeError):
    """Raised when approved knowledge cannot be embedded or stored."""


@dataclass(frozen=True)
class KnowledgeIngestionResult:
    source_title: str
    chunk_count: int
    chunk_ids: list[UUID]


def get_embedding_client() -> EmbeddingClient:
    return OllamaEmbeddingClient(model=get_ollama_embedding_model())


class KnowledgeIngestionService:
    def __init__(self, embedding_client: EmbeddingClient, *, chunk_size: int = 900, overlap: int = 120) -> None:
        self.embedding_client = embedding_client
        self.chunk_size = chunk_size
        self.overlap = overlap

    def ingest(self, payload: KnowledgeIngestRequest, *, created_by: UUID | str) -> KnowledgeIngestionResult:
        chunks = split_text(payload.content, chunk_size=self.chunk_size, overlap=self.overlap)
        if not chunks:
            raise ValueError("Content must not be empty")

        chunk_ids: list[UUID] = []
        try:
            with get_connection() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    for index, chunk in enumerate(chunks):
                        embedding_model = getattr(self.embedding_client, "model", "unknown")
                        embedding = self.embedding_client.embed(chunk)
                        if not embedding:
                            raise KnowledgeIngestionError("Embedding service returned an empty vector")
                        row = knowledge_repository.insert_knowledge_chunk(
                            cur,
                            source_title=payload.source_title.strip(),
                            source_uri=str(payload.source_uri) if payload.source_uri else None,
                            chunk_index=index,
                            content=chunk,
                            metadata=payload.metadata,
                            embedding_model=embedding_model,
                            embedding=embedding,
                            content_hash=_content_hash(chunk),
                            created_by=created_by,
                        )
                        chunk_ids.append(row["id"])
                conn.commit()
        except EmbeddingClientError as exc:
            raise KnowledgeIngestionError("Embedding service is unavailable") from exc

        return KnowledgeIngestionResult(
            source_title=payload.source_title.strip(),
            chunk_count=len(chunk_ids),
            chunk_ids=chunk_ids,
        )


def split_text(text: str, *, chunk_size: int, overlap: int) -> list[str]:
    clean_text = " ".join(text.split())
    if not clean_text:
        return []
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("Invalid chunk settings")

    chunks: list[str] = []
    start = 0
    while start < len(clean_text):
        end = min(start + chunk_size, len(clean_text))
        used_word_boundary = False
        if end < len(clean_text):
            boundary = clean_text.rfind(" ", start, end)
            if boundary > start:
                end = boundary
                used_word_boundary = True
        chunks.append(clean_text[start:end].strip())
        if end == len(clean_text):
            break
        start = max(0, end - overlap)
        while used_word_boundary and start > 0 and start < len(clean_text) and clean_text[start - 1] != " ":
            start += 1
    return chunks


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
