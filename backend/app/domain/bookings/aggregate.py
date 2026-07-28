from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from backend.app.domain.bookings.status import TERMINAL_STATUSES, BookingStatus, parse_booking_status, validate_status_transition


@dataclass
class BookingAggregate:
    id: UUID
    customer_id: UUID | None = None
    activity_id: UUID | None = None
    booking_activity_id: UUID | None = None
    event_at: datetime | None = None
    city: str | None = None
    venue: str | None = None
    participant_count: int | None = None
    agreed_price: Decimal | None = None
    status: BookingStatus | None = None
    requires_instructor: bool = False
    notes: str | None = None
    version: int = 0
    active_instructor_assignments: set[tuple[UUID, UUID]] | None = None

    def __post_init__(self) -> None:
        if self.active_instructor_assignments is None:
            self.active_instructor_assignments = set()

    @classmethod
    def replay(cls, booking_id: UUID, events: list[dict]) -> "BookingAggregate":
        aggregate = cls(id=booking_id)
        for event in events:
            aggregate.apply(event["event_type"], event["event_data"])
            aggregate.version = event["aggregate_version"]
        return aggregate

    def apply(self, event_type: str, data: dict) -> None:
        if event_type == "BookingCreated":
            self.customer_id = UUID(data["customer_id"])
            self.activity_id = UUID(data["activity_id"])
            self.booking_activity_id = UUID(data["booking_activity_id"]) if data.get("booking_activity_id") else None
            self.event_at = datetime.fromisoformat(data["event_at"])
            self.city = data.get("city")
            self.venue = data.get("venue")
            self.participant_count = data["participant_count"]
            self.agreed_price = Decimal(str(data["agreed_price"]))
            self.status = parse_booking_status(data["status"])
            self.requires_instructor = data["requires_instructor"]
            self.notes = data.get("notes")
        elif event_type == "BookingStatusChanged":
            self.status = parse_booking_status(data["new"])
        elif event_type == "BookingDateChanged":
            self.event_at = datetime.fromisoformat(data["new"])
        elif event_type == "BookingPriceChanged":
            self.agreed_price = Decimal(str(data["new"]))
        elif event_type == "BookingLocationChanged":
            self.city = data.get("new_city")
            self.venue = data.get("new_venue")
        elif event_type == "BookingParticipantCountChanged":
            self.participant_count = data["new"]
        elif event_type == "BookingNotesUpdated":
            self.notes = data.get("new")
        elif event_type == "BookingInstructorAssigned":
            self.active_instructor_assignments.add((UUID(data["booking_activity_id"]), UUID(data["instructor_id"])))
        elif event_type == "BookingInstructorRemoved":
            self.active_instructor_assignments.discard((UUID(data["booking_activity_id"]), UUID(data["instructor_id"])))
        else:
            raise ValueError(f"Unsupported booking event: {event_type}")

    def ensure_can_update_operational_fields(self) -> None:
        if self.status in TERMINAL_STATUSES:
            raise ValueError("Completed or cancelled bookings cannot receive operational updates")

    def validate_status_change(self, new_status: str) -> BookingStatus:
        parsed = parse_booking_status(new_status)
        if self.status is None:
            raise ValueError("Booking has not been created")
        validate_status_transition(self.status, parsed)
        return parsed

    def to_projection(self) -> dict:
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "activity_id": self.activity_id,
            "event_at": self.event_at,
            "city": self.city,
            "venue": self.venue,
            "participant_count": self.participant_count,
            "agreed_price": self.agreed_price,
            "status": self.status.value if self.status else None,
            "requires_instructor": self.requires_instructor,
            "notes": self.notes,
            "version": self.version,
        }
