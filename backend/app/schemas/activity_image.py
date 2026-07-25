from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ActivityImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    activity_id: UUID
    public_id: str
    secure_url: str
    original_filename: str | None = None
    content_type: str | None = None
    width: int | None = None
    height: int | None = None
    bytes: int | None = None
    is_primary: bool
    created_at: datetime
    updated_at: datetime


class ActivityImageListResponse(BaseModel):
    items: list[ActivityImageResponse]
    count: int

