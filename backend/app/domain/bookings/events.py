from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID


SCHEMA_VERSION = 1


@dataclass(frozen=True)
class BookingEvent:
    event_type: str
    data: dict[str, Any]

    def payload(self) -> dict[str, Any]:
        return {"schema_version": SCHEMA_VERSION, **self.data}


def booking_created(
    *,
    customer_id: UUID,
    activity_id: UUID,
    event_at: datetime,
    city: str | None,
    venue: str | None,
    participant_count: int,
    agreed_price: Decimal,
    status: str,
    requires_instructor: bool,
    notes: str | None,
) -> BookingEvent:
    return BookingEvent(
        "BookingCreated",
        {
            "customer_id": str(customer_id),
            "activity_id": str(activity_id),
            "event_at": event_at.isoformat(),
            "city": city,
            "venue": venue,
            "participant_count": participant_count,
            "agreed_price": str(agreed_price),
            "status": status,
            "requires_instructor": requires_instructor,
            "notes": notes,
        },
    )


def field_changed(event_type: str, previous: Any, new: Any) -> BookingEvent:
    if isinstance(previous, Decimal):
        previous = str(previous)
    if isinstance(new, Decimal):
        new = str(new)
    if isinstance(previous, datetime):
        previous = previous.isoformat()
    if isinstance(new, datetime):
        new = new.isoformat()
    return BookingEvent(event_type, {"previous": previous, "new": new})


def location_changed(
    *,
    previous_city: str | None,
    previous_venue: str | None,
    new_city: str | None,
    new_venue: str | None,
) -> BookingEvent:
    return BookingEvent(
        "BookingLocationChanged",
        {
            "previous_city": previous_city,
            "previous_venue": previous_venue,
            "new_city": new_city,
            "new_venue": new_venue,
        },
    )


def instructor_assigned(*, booking_activity_id: UUID, instructor_id: UUID) -> BookingEvent:
    return BookingEvent(
        "BookingInstructorAssigned",
        {"booking_activity_id": str(booking_activity_id), "instructor_id": str(instructor_id)},
    )


def instructor_removed(*, booking_activity_id: UUID, instructor_id: UUID) -> BookingEvent:
    return BookingEvent(
        "BookingInstructorRemoved",
        {"booking_activity_id": str(booking_activity_id), "instructor_id": str(instructor_id)},
    )
