from __future__ import annotations

from dataclasses import dataclass
import hashlib
from uuid import UUID, uuid4

from psycopg.rows import dict_row
from rag import EmbeddingClient, EmbeddingClientError
from rag.embedding_formatting import KnowledgeDocumentText, format_document_embedding_input

from backend.app.application.services.knowledge_ingestion_service import split_text
from backend.app.core.environment import get_ollama_embedding_model
from backend.app.db.connection import get_connection
from backend.app.infrastructure.repositories import knowledge_repository
from backend.app.schemas.knowledge import (
    MAX_KNOWLEDGE_SOURCE_CONTENT_CHARS,
    KnowledgeSourceCreateRequest,
    KnowledgeSourceReplaceRequest,
)


ALLOWED_KNOWLEDGE_ROLES = {"manager", "instructor", "customer"}
MAX_KNOWLEDGE_UPLOAD_CHARS = MAX_KNOWLEDGE_SOURCE_CONTENT_CHARS


class KnowledgeManagementError(RuntimeError):
    """Raised when managed RAG source persistence cannot be completed."""


@dataclass(frozen=True)
class KnowledgeSourceData:
    source_id: UUID
    title: str
    source_uri: str | None
    category: str
    activity_name: str | None
    allowed_roles: list[str]
    chunk_count: int
    created_by: UUID
    created_at: object | None
    updated_at: object | None
    content: str = ""


@dataclass(frozen=True)
class KnowledgeSourceWriteData:
    source: KnowledgeSourceData
    chunk_ids: list[UUID]


class KnowledgeManagementService:
    def __init__(self, embedding_client: EmbeddingClient, *, chunk_size: int = 900, overlap: int = 120) -> None:
        self.embedding_client = embedding_client
        self.chunk_size = chunk_size
        self.overlap = overlap

    def create(self, payload: KnowledgeSourceCreateRequest, *, created_by: UUID | str) -> KnowledgeSourceWriteData:
        source_id = uuid4()
        return self._write_source(
            source_id=source_id,
            title=payload.title,
            content=payload.content,
            source_uri=payload.source_uri,
            category=payload.category,
            activity_name=payload.activity_name,
            allowed_roles=payload.allowed_roles,
            created_by=created_by,
            replace_existing=False,
        )

    def list_sources(self) -> list[KnowledgeSourceData]:
        with get_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                return [self._source_from_row(row) for row in knowledge_repository.list_logical_sources(cur)]

    def get_source(self, source_id: UUID) -> KnowledgeSourceData | None:
        with get_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                row = knowledge_repository.get_logical_source(cur, source_id=source_id)
        return self._source_from_row(row) if row else None

    def replace(
        self,
        source_id: UUID,
        payload: KnowledgeSourceReplaceRequest,
        *,
        created_by: UUID | str,
    ) -> KnowledgeSourceWriteData:
        existing = self.get_source(source_id)
        if existing is None:
            raise LookupError("Knowledge source was not found")
        return self._write_source(
            source_id=source_id,
            title=payload.title or existing.title,
            content=payload.content,
            source_uri=payload.source_uri if payload.source_uri is not None else existing.source_uri,
            category=payload.category or existing.category,
            activity_name=payload.activity_name,
            allowed_roles=payload.allowed_roles,
            created_by=created_by,
            replace_existing=True,
        )

    def delete(self, source_id: UUID) -> int:
        with get_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                existing = knowledge_repository.get_logical_source(cur, source_id=source_id)
                if existing is None:
                    raise LookupError("Knowledge source was not found")
                deleted = knowledge_repository.delete_source_chunks(cur, source_id=source_id)
            conn.commit()
        return len(deleted)

    def cleanup_task16_demo_chunks(self) -> int:
        """Delete only disposable Task 16 demo rows outside managed sources."""
        with get_connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                deleted = knowledge_repository.delete_task16_demo_chunks(cur)
            conn.commit()
        return len(deleted)

    def _write_source(
        self,
        *,
        source_id: UUID,
        title: str,
        content: str,
        source_uri: str | None,
        category: str,
        activity_name: str | None,
        allowed_roles: list[str],
        created_by: UUID | str,
        replace_existing: bool,
    ) -> KnowledgeSourceWriteData:
        clean_content = content.strip()
        chunks = split_text(clean_content, chunk_size=self.chunk_size, overlap=self.overlap)
        if not chunks:
            raise ValueError("Content must not be empty")
        roles = normalize_allowed_roles(allowed_roles)
        clean_activity_name = activity_name.strip() if activity_name else None
        metadata = {
            "source_id": str(source_id),
            "category": category.strip(),
            "activity": clean_activity_name,
            "activity_name": clean_activity_name,
            "allowed_roles": roles,
            "original_content": clean_content,
        }
        chunk_ids: list[UUID] = []
        try:
            with get_connection() as conn:
                with conn.cursor(row_factory=dict_row) as cur:
                    if replace_existing:
                        knowledge_repository.delete_source_chunks(cur, source_id=source_id)
                    for index, chunk in enumerate(chunks):
                        embedding_model = getattr(self.embedding_client, "model", None) or get_ollama_embedding_model()
                        embedding_input = format_document_embedding_input(
                            model=embedding_model,
                            document=KnowledgeDocumentText(source_title=title.strip(), content=chunk, metadata=metadata),
                        )
                        embedding = self.embedding_client.embed(embedding_input)
                        if not embedding:
                            raise KnowledgeManagementError("Embedding service returned an empty vector")
                        row = knowledge_repository.insert_knowledge_chunk(
                            cur,
                            source_title=title.strip(),
                            source_uri=source_uri,
                            chunk_index=index,
                            content=chunk,
                            metadata=metadata,
                            embedding_model=embedding_model,
                            embedding=embedding,
                            content_hash=_content_hash(chunk),
                            created_by=created_by,
                        )
                        chunk_ids.append(row["id"])
                conn.commit()
        except EmbeddingClientError as exc:
            raise KnowledgeManagementError("Embedding service is unavailable") from exc
        source = self.get_source(source_id)
        if source is None:
            raise KnowledgeManagementError("Knowledge source could not be read after write")
        return KnowledgeSourceWriteData(source=source, chunk_ids=chunk_ids)

    @staticmethod
    def _source_from_row(row: dict) -> KnowledgeSourceData:
        roles = row.get("allowed_roles") if isinstance(row.get("allowed_roles"), list) else []
        return KnowledgeSourceData(
            source_id=row["source_id"],
            title=row["title"],
            source_uri=row["source_uri"],
            category=row["category"] or "",
            activity_name=row["activity_name"],
            allowed_roles=roles,
            chunk_count=int(row["chunk_count"]),
            created_by=row["created_by"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            content=row.get("content") or "",
        )


def normalize_allowed_roles(roles: list[str]) -> list[str]:
    if not isinstance(roles, list):
        raise ValueError("allowed_roles must be a list")
    unknown = sorted({role for role in roles if role not in ALLOWED_KNOWLEDGE_ROLES})
    if unknown:
        raise ValueError("Unknown allowed role")
    return sorted({"manager", *roles})


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
