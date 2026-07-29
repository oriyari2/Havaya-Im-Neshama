from __future__ import annotations

from pydantic import BaseModel, Field


class AIConsultRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000)


class AIConsultSource(BaseModel):
    chunk_id: str
    source_title: str
    source_uri: str | None


class AIConsultResponse(BaseModel):
    answer: str
    answer_basis: str
    sources: list[AIConsultSource] = Field(default_factory=list)
