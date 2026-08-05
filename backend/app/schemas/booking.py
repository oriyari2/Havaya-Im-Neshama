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
    customer_id: UUID | None = None
    activity_id: UUID
    event_at: datetime
    city: str | None = None
    venue: str | None = None
    participant_count: int = Field(gt=0)
    agreed_price: Decimal = Field(default=Decimal("0"), ge=0)
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
    customer_name: str | None = None
    activity_id: UUID
    activity_name: str | None = None
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


class InstructorBookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    activity_id: UUID
    activity_name: str | None = None
    customer_name: str | None = None
    customer_contact_name: str | None = None
    customer_phone: str | None = None
    event_at: datetime
    city: str | None = None
    venue: str | None = None
    participant_count: int
    status: str
    requires_instructor: bool
    version: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


class InstructorBookingListResponse(BaseModel):
    items: list[InstructorBookingResponse]
    count: int


class CustomerBookingSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    activity_id: UUID
    activity_name: str | None = None
    event_at: datetime
    city: str | None = None
    venue: str | None = None
    status: str
    version: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CustomerBookingSummaryListResponse(BaseModel):
    items: list[CustomerBookingSummaryResponse]
    count: int


class DashboardSummaryResponse(BaseModel):
    confirmed_count: int = Field(description="Upcoming bookings with status CONFIRMED")
    pending_count: int = Field(description="Upcoming bookings with status NEW")
    cancelled_count: int = Field(description="Upcoming bookings with status CANCELLED")
    upcoming_count: int = Field(description="All upcoming bookings regardless of status")
    assigned_count: int = Field(description="Upcoming instructor-required bookings whose activities all have an active instructor")
    unassigned_count: int = Field(description="Upcoming instructor-required bookings with at least one activity lacking an active instructor")


class MonthlyEventCount(BaseModel):
    month: int = Field(ge=1, le=12)
    count: int = Field(ge=0)


class YearlyEventTrendResponse(BaseModel):
    year: int
    available_years: list[int]
    months: list[MonthlyEventCount]


class OpenEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    activity_id: UUID | None
    booking_activity_id: UUID | None = None
    my_request_status: str | None = None
    activity_name: str | None = None
    customer_name: str | None = None
    event_at: datetime
    city: str | None = None
    venue: str | None = None
    status: str
    requires_instructor: bool
    version: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


class BookingEventResponse(BaseModel):
    event_id: UUID
    aggregate_id: UUID
    aggregate_version: int
    event_type: str
    event_data: dict[str, Any]
    actor_user_id: UUID
    occurred_at: datetime
    correlation_id: UUID | None = None
