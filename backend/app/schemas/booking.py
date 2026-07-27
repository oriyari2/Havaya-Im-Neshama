from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


class BookingCreate(BaseModel):
    customer_id: UUID
    activity_id: UUID
    event_at: datetime
    city: str | None = None
    venue: str | None = None
    participant_count: int = Field(gt=0)
    agreed_price: Decimal = Field(ge=0)
    status: str = "NEW"
    requires_instructor: bool = False
    notes: str | None = None
    correlation_id: UUID | None = None

    @field_validator("city", "venue", "notes")
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        return _clean_optional_text(value)


class ExpectedVersionRequest(BaseModel):
    expected_version: int = Field(ge=1)
    correlation_id: UUID | None = None


class BookingStatusChange(ExpectedVersionRequest):
    status: str


class BookingDateChange(ExpectedVersionRequest):
    event_at: datetime


class BookingPriceChange(ExpectedVersionRequest):
    agreed_price: Decimal = Field(ge=0)


class BookingLocationChange(ExpectedVersionRequest):
    city: str | None = None
    venue: str | None = None

    @field_validator("city", "venue")
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        return _clean_optional_text(value)


class BookingParticipantCountChange(ExpectedVersionRequest):
    participant_count: int = Field(gt=0)


class BookingNotesUpdate(ExpectedVersionRequest):
    notes: str | None = None

    @field_validator("notes")
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        return _clean_optional_text(value)


class BookingInstructorAssignment(ExpectedVersionRequest):
    booking_activity_id: UUID
    instructor_id: UUID


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: UUID
    activity_id: UUID
    event_at: datetime
    city: str | None = None
    venue: str | None = None
    participant_count: int
    agreed_price: Decimal
    status: str
    requires_instructor: bool
    notes: str | None = None
    version: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


class BookingListResponse(BaseModel):
    items: list[BookingResponse]
    count: int


class BookingEventResponse(BaseModel):
    event_id: UUID
    aggregate_id: UUID
    aggregate_version: int
    event_type: str
    event_data: dict[str, Any]
    actor_user_id: UUID
    occurred_at: datetime
    correlation_id: UUID | None = None
