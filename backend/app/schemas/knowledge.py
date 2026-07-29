from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


MAX_KNOWLEDGE_SOURCE_CONTENT_CHARS = 50000


class KnowledgeIngestRequest(BaseModel):
    source_title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=MAX_KNOWLEDGE_SOURCE_CONTENT_CHARS)
    source_uri: str | None = Field(default=None, max_length=500)
    metadata: dict = Field(default_factory=dict)

    @field_validator("source_title", "content")
    @classmethod
    def clean_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Field must not be empty")
        return cleaned

    @field_validator("source_uri")
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class KnowledgeIngestResponse(BaseModel):
    source_title: str
    chunk_count: int
    chunk_ids: list[UUID]


class KnowledgeSourceCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=MAX_KNOWLEDGE_SOURCE_CONTENT_CHARS)
    category: str = Field(..., min_length=1, max_length=100)
    activity_name: str | None = Field(default=None, max_length=200)
    source_uri: str | None = Field(default=None, max_length=500)
    allowed_roles: list[str] = Field(default_factory=list)

    @field_validator("title", "content", "category")
    @classmethod
    def clean_required_source_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Field must not be empty")
        return cleaned

    @field_validator("activity_name", "source_uri")
    @classmethod
    def clean_optional_source_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class KnowledgeSourceReplaceRequest(KnowledgeSourceCreateRequest):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    category: str | None = Field(default=None, min_length=1, max_length=100)

    @field_validator("title", "category")
    @classmethod
    def clean_optional_required_source_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Field must not be empty")
        return cleaned


class KnowledgeSourceSummary(BaseModel):
    source_id: UUID
    title: str
    source_uri: str | None
    category: str
    activity_name: str | None
    allowed_roles: list[str]
    chunk_count: int
    created_by: UUID
    created_at: datetime | None
    updated_at: datetime | None


class KnowledgeSourceDetail(KnowledgeSourceSummary):
    content: str


class KnowledgeSourceWriteResponse(BaseModel):
    source: KnowledgeSourceDetail
    chunk_ids: list[UUID]


class KnowledgeSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(..., min_length=1)
    limit: int | None = Field(default=None, ge=1, le=10)

    @field_validator("query")
    @classmethod
    def clean_query(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Query must not be empty")
        return cleaned


class KnowledgeSearchResult(BaseModel):
    chunk_id: UUID
    source_title: str
    source_uri: str | None
    chunk_index: int
    content: str
    metadata: dict
    distance: float
    score: float


class KnowledgeSearchResponse(BaseModel):
    query: str
    results: list[KnowledgeSearchResult]
