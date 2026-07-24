from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _validate_required_text(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} must not be empty")
    return cleaned


class ActivityBase(BaseModel):
    description: str | None = None
    target_audience: str | None = None
    duration_minutes: int | None = Field(default=None, gt=0)
    recommended_capacity: int | None = Field(default=None, gt=0)
    pricing_rule: str | None = None
    required_equipment: str | None = None
    preparation_notes: str | None = None
    season: str | None = None
    tags: str | None = None
    is_active: bool = True

    @field_validator(
        "description",
        "target_audience",
        "pricing_rule",
        "required_equipment",
        "preparation_notes",
        "season",
        "tags",
    )
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        return _clean_optional_text(value)


class ActivityCreate(ActivityBase):
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _validate_required_text(value, "name")


class ActivityUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    target_audience: str | None = None
    duration_minutes: int | None = Field(default=None, gt=0)
    recommended_capacity: int | None = Field(default=None, gt=0)
    pricing_rule: str | None = None
    required_equipment: str | None = None
    preparation_notes: str | None = None
    season: str | None = None
    tags: str | None = None
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _validate_required_text(value, "name")

    @field_validator(
        "description",
        "target_audience",
        "pricing_rule",
        "required_equipment",
        "preparation_notes",
        "season",
        "tags",
    )
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        return _clean_optional_text(value)


class ActivityResponse(ActivityBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime


class ActivityListResponse(BaseModel):
    items: list[ActivityResponse]
    count: int
