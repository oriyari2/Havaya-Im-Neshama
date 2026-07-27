from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class CreateBookingCommand:
    customer_id: UUID
    activity_id: UUID
    event_at: datetime
    city: str | None
    venue: str | None
    participant_count: int
    agreed_price: Decimal
    status: str
    requires_instructor: bool
    notes: str | None
    actor_user_id: UUID
    correlation_id: UUID | None = None


@dataclass(frozen=True)
class UpdateBookingCommand:
    booking_id: UUID
    expected_version: int
    actor_user_id: UUID
    correlation_id: UUID | None = None


@dataclass(frozen=True)
class ChangeStatusCommand(UpdateBookingCommand):
    status: str = ""


@dataclass(frozen=True)
class ChangeDateCommand(UpdateBookingCommand):
    event_at: datetime | None = None


@dataclass(frozen=True)
class ChangePriceCommand(UpdateBookingCommand):
    agreed_price: Decimal | None = None


@dataclass(frozen=True)
class ChangeLocationCommand(UpdateBookingCommand):
    city: str | None = None
    venue: str | None = None


@dataclass(frozen=True)
class ChangeParticipantCountCommand(UpdateBookingCommand):
    participant_count: int = 0


@dataclass(frozen=True)
class UpdateNotesCommand(UpdateBookingCommand):
    notes: str | None = None


@dataclass(frozen=True)
class AssignInstructorCommand(UpdateBookingCommand):
    booking_activity_id: UUID | None = None
    instructor_id: UUID | None = None


@dataclass(frozen=True)
class RemoveInstructorCommand(UpdateBookingCommand):
    booking_activity_id: UUID | None = None
    instructor_id: UUID | None = None
