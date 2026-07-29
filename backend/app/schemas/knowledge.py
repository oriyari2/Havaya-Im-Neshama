from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class KnowledgeIngestRequest(BaseModel):
    source_title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=50000)
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
