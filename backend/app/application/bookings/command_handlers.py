from __future__ import annotations

from uuid import uuid4

from psycopg import errors
from psycopg.rows import dict_row

from backend.app.application.bookings.commands import (
    ChangeDateCommand,
    ChangeLocationCommand,
    ChangeParticipantCountCommand,
    ChangePriceCommand,
    ChangeStatusCommand,
    AssignInstructorCommand,
    CreateBookingCommand,
    RemoveInstructorCommand,
    UpdateNotesCommand,
)
from backend.app.db.connection import get_connection
from backend.app.domain.bookings.aggregate import BookingAggregate
from backend.app.domain.bookings.events import (
    booking_created,
    field_changed,
    instructor_assigned,
    instructor_removed,
    location_changed,
)
from backend.app.domain.bookings.status import parse_booking_status
from backend.app.infrastructure.repositories import booking_event_repository as events_repo
from backend.app.infrastructure.repositories import booking_projection_repository as projection_repo


class BookingNotFoundError(Exception):
    pass


class BookingConcurrencyError(Exception):
    pass


class BookingValidationError(Exception):
    pass


def _load_aggregate(cur, booking_id) -> BookingAggregate:
    events = events_repo.list_events(cur, booking_id)
    if not events:
        raise BookingNotFoundError
    return BookingAggregate.replay(booking_id, events)


def _append_and_project(cur, aggregate: BookingAggregate, event, actor_user_id, correlation_id) -> dict:
    next_version = aggregate.version + 1
    try:
        events_repo.append_event(
            cur,
            aggregate_id=aggregate.id,
            aggregate_version=next_version,
            event_type=event.event_type,
            event_data=event.payload(),
            actor_user_id=actor_user_id,
            correlation_id=correlation_id,
        )
    except errors.UniqueViolation as exc:
        raise BookingConcurrencyError from exc
    aggregate.apply(event.event_type, event.payload())
    aggregate.version = next_version
    projection = projection_repo.upsert_projection(cur, aggregate.to_projection())
    projection_repo.sync_instructor_projection(cur, aggregate.id, aggregate.active_instructor_assignments)
    return projection


def _handle_update(command, build_event) -> dict:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            aggregate = _load_aggregate(cur, command.booking_id)
            if aggregate.version != command.expected_version:
                raise BookingConcurrencyError
            try:
                event = build_event(aggregate)
            except ValueError as exc:
                raise BookingValidationError(str(exc)) from exc
            projection = _append_and_project(cur, aggregate, event, command.actor_user_id, command.correlation_id)
            conn.commit()
            return projection


def create_booking(command: CreateBookingCommand) -> dict:
    if command.participant_count <= 0:
        raise BookingValidationError("participant_count must be positive")
    if command.agreed_price < 0:
        raise BookingValidationError("agreed_price must be non-negative")
    try:
        status = parse_booking_status(command.status)
    except ValueError as exc:
        raise BookingValidationError(str(exc)) from exc

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            if not projection_repo.customer_is_active(cur, command.customer_id):
                raise BookingValidationError("Booking must reference an active customer")
            if not projection_repo.activity_is_active(cur, command.activity_id):
                raise BookingValidationError("Booking must reference an active activity")
            booking_id = uuid4()
            aggregate = BookingAggregate(id=booking_id)
            event = booking_created(
                customer_id=command.customer_id,
                activity_id=command.activity_id,
                event_at=command.event_at,
                city=command.city,
                venue=command.venue,
                participant_count=command.participant_count,
                agreed_price=command.agreed_price,
                status=status.value,
                requires_instructor=command.requires_instructor,
                notes=command.notes,
            )
            projection = _append_and_project(cur, aggregate, event, command.actor_user_id, command.correlation_id)
            conn.commit()
            return projection


def change_status(command: ChangeStatusCommand) -> dict:
    def build(aggregate: BookingAggregate):
        new_status = aggregate.validate_status_change(command.status)
        return field_changed("BookingStatusChanged", aggregate.status.value, new_status.value)

    return _handle_update(command, build)


def change_date(command: ChangeDateCommand) -> dict:
    if command.event_at is None:
        raise BookingValidationError("event_at is required")

    def build(aggregate: BookingAggregate):
        aggregate.ensure_can_update_operational_fields()
        return field_changed("BookingDateChanged", aggregate.event_at, command.event_at)

    return _handle_update(command, build)


def change_price(command: ChangePriceCommand) -> dict:
    if command.agreed_price is None or command.agreed_price < 0:
        raise BookingValidationError("agreed_price must be non-negative")

    def build(aggregate: BookingAggregate):
        aggregate.ensure_can_update_operational_fields()
        return field_changed("BookingPriceChanged", aggregate.agreed_price, command.agreed_price)

    return _handle_update(command, build)


def change_location(command: ChangeLocationCommand) -> dict:
    def build(aggregate: BookingAggregate):
        aggregate.ensure_can_update_operational_fields()
        return location_changed(
            previous_city=aggregate.city,
            previous_venue=aggregate.venue,
            new_city=command.city,
            new_venue=command.venue,
        )

    return _handle_update(command, build)


def change_participant_count(command: ChangeParticipantCountCommand) -> dict:
    if command.participant_count <= 0:
        raise BookingValidationError("participant_count must be positive")

    def build(aggregate: BookingAggregate):
        aggregate.ensure_can_update_operational_fields()
        return field_changed("BookingParticipantCountChanged", aggregate.participant_count, command.participant_count)

    return _handle_update(command, build)


def update_notes(command: UpdateNotesCommand) -> dict:
    def build(aggregate: BookingAggregate):
        aggregate.ensure_can_update_operational_fields()
        return field_changed("BookingNotesUpdated", aggregate.notes, command.notes)

    return _handle_update(command, build)


def assign_instructor(command: AssignInstructorCommand) -> dict:
    if command.booking_activity_id is None:
        raise BookingValidationError("booking_activity_id is required")
    if command.instructor_id is None:
        raise BookingValidationError("instructor_id is required")

    def build(aggregate: BookingAggregate):
        aggregate.ensure_can_update_operational_fields()
        assignment = (command.booking_activity_id, command.instructor_id)
        if assignment in aggregate.active_instructor_assignments:
            raise ValueError("Instructor is already assigned to this booking activity")
        return instructor_assigned(booking_activity_id=command.booking_activity_id, instructor_id=command.instructor_id)

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            if not projection_repo.instructor_is_active(cur, command.instructor_id):
                raise BookingValidationError("Booking must reference an active instructor")
            if not projection_repo.booking_activity_belongs_to_booking(cur, command.booking_activity_id, command.booking_id):
                raise BookingValidationError("booking_activity_id must belong to the booking")
        conn.rollback()
    return _handle_update(command, build)


def remove_instructor(command: RemoveInstructorCommand) -> dict:
    if command.booking_activity_id is None:
        raise BookingValidationError("booking_activity_id is required")
    if command.instructor_id is None:
        raise BookingValidationError("instructor_id is required")

    def build(aggregate: BookingAggregate):
        aggregate.ensure_can_update_operational_fields()
        assignment = (command.booking_activity_id, command.instructor_id)
        if assignment not in aggregate.active_instructor_assignments:
            raise ValueError("Instructor is not assigned to this booking activity")
        return instructor_removed(booking_activity_id=command.booking_activity_id, instructor_id=command.instructor_id)

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            if not projection_repo.booking_activity_belongs_to_booking(cur, command.booking_activity_id, command.booking_id):
                raise BookingValidationError("booking_activity_id must belong to the booking")
        conn.rollback()
    return _handle_update(command, build)
