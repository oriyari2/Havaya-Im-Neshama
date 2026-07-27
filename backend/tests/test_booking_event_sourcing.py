from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
import unittest
from unittest.mock import patch
from uuid import uuid4

from backend.app.application.bookings import command_handlers
from backend.app.application.bookings.commands import AssignInstructorCommand, ChangeStatusCommand, RemoveInstructorCommand
from backend.app.domain.bookings.aggregate import BookingAggregate
from backend.app.domain.bookings.events import (
    booking_created,
    field_changed,
    instructor_assigned,
    instructor_removed,
    location_changed,
)
from backend.app.infrastructure.repositories import booking_projection_repository


def _event(version: int, event_type: str, data: dict) -> dict:
    return {
        "aggregate_version": version,
        "event_type": event_type,
        "event_data": data,
    }


class BookingEventSourcingTests(unittest.TestCase):
    def test_replay_reconstructs_booking_projection(self) -> None:
        booking_id = uuid4()
        customer_id = uuid4()
        activity_id = uuid4()
        created = booking_created(
            customer_id=customer_id,
            activity_id=activity_id,
            event_at=datetime(2026, 8, 15, 10, 0, tzinfo=UTC),
            city="Jerusalem",
            venue="School hall",
            participant_count=80,
            agreed_price=Decimal("2400"),
            status="NEW",
            requires_instructor=True,
            notes="Demo booking",
        )
        events = [
            _event(1, created.event_type, created.payload()),
            _event(2, "BookingStatusChanged", field_changed("BookingStatusChanged", "NEW", "CONFIRMED").payload()),
            _event(
                3,
                "BookingLocationChanged",
                location_changed(
                    previous_city="Jerusalem",
                    previous_venue="School hall",
                    new_city="Beit Shemesh",
                    new_venue="Community center",
                ).payload(),
            ),
            _event(
                4,
                "BookingPriceChanged",
                field_changed("BookingPriceChanged", Decimal("2400"), Decimal("2600")).payload(),
            ),
            _event(
                5,
                "BookingParticipantCountChanged",
                field_changed("BookingParticipantCountChanged", 80, 90).payload(),
            ),
            _event(6, "BookingNotesUpdated", field_changed("BookingNotesUpdated", "Demo booking", "Updated").payload()),
        ]

        projection = BookingAggregate.replay(booking_id, events).to_projection()

        self.assertEqual(projection["id"], booking_id)
        self.assertEqual(projection["customer_id"], customer_id)
        self.assertEqual(projection["activity_id"], activity_id)
        self.assertEqual(projection["city"], "Beit Shemesh")
        self.assertEqual(projection["venue"], "Community center")
        self.assertEqual(projection["status"], "CONFIRMED")
        self.assertEqual(projection["agreed_price"], Decimal("2600"))
        self.assertEqual(projection["participant_count"], 90)
        self.assertEqual(projection["notes"], "Updated")
        self.assertEqual(projection["version"], 6)

    def test_replay_reconstructs_active_instructors(self) -> None:
        booking_id = uuid4()
        booking_activity_id = uuid4()
        first_instructor_id = uuid4()
        second_instructor_id = uuid4()
        events = [
            _event(1, "BookingCreated", self._created_event().payload()),
            _event(
                2,
                "BookingInstructorAssigned",
                instructor_assigned(
                    booking_activity_id=booking_activity_id,
                    instructor_id=first_instructor_id,
                ).payload(),
            ),
            _event(
                3,
                "BookingInstructorAssigned",
                instructor_assigned(
                    booking_activity_id=booking_activity_id,
                    instructor_id=second_instructor_id,
                ).payload(),
            ),
            _event(
                4,
                "BookingInstructorRemoved",
                instructor_removed(
                    booking_activity_id=booking_activity_id,
                    instructor_id=first_instructor_id,
                ).payload(),
            ),
        ]

        aggregate = BookingAggregate.replay(booking_id, events)

        self.assertEqual(aggregate.active_instructor_assignments, {(booking_activity_id, second_instructor_id)})
        self.assertEqual(aggregate.version, 4)

    def test_assign_instructor_to_booking_activity_appends_assigned_event(self) -> None:
        booking_id = uuid4()
        booking_activity_id = uuid4()
        instructor_id = uuid4()
        appended = self._run_handler_with_mocks(
            command_handlers.assign_instructor,
            AssignInstructorCommand(
                booking_id=booking_id,
                booking_activity_id=booking_activity_id,
                instructor_id=instructor_id,
                expected_version=1,
                actor_user_id=uuid4(),
            ),
            events=[_event(1, "BookingCreated", self._created_event().payload())],
            instructor_is_active=True,
        )

        self.assertEqual(appended["event_type"], "BookingInstructorAssigned")
        self.assertEqual(appended["aggregate_version"], 2)
        self.assertEqual(appended["event_data"]["booking_activity_id"], str(booking_activity_id))
        self.assertEqual(appended["event_data"]["instructor_id"], str(instructor_id))

    def test_remove_instructor_from_booking_activity_appends_removed_event(self) -> None:
        booking_id = uuid4()
        booking_activity_id = uuid4()
        instructor_id = uuid4()
        appended = self._run_handler_with_mocks(
            command_handlers.remove_instructor,
            RemoveInstructorCommand(
                booking_id=booking_id,
                booking_activity_id=booking_activity_id,
                instructor_id=instructor_id,
                expected_version=2,
                actor_user_id=uuid4(),
            ),
            events=[
                _event(1, "BookingCreated", self._created_event().payload()),
                _event(
                    2,
                    "BookingInstructorAssigned",
                    instructor_assigned(
                        booking_activity_id=booking_activity_id,
                        instructor_id=instructor_id,
                    ).payload(),
                ),
            ],
        )

        self.assertEqual(appended["event_type"], "BookingInstructorRemoved")
        self.assertEqual(appended["aggregate_version"], 3)
        self.assertEqual(appended["event_data"]["booking_activity_id"], str(booking_activity_id))
        self.assertEqual(appended["event_data"]["instructor_id"], str(instructor_id))

    def test_assign_same_instructor_again_after_removal_appends_assigned_event(self) -> None:
        booking_id = uuid4()
        booking_activity_id = uuid4()
        instructor_id = uuid4()
        appended = self._run_handler_with_mocks(
            command_handlers.assign_instructor,
            AssignInstructorCommand(
                booking_id=booking_id,
                booking_activity_id=booking_activity_id,
                instructor_id=instructor_id,
                expected_version=3,
                actor_user_id=uuid4(),
            ),
            events=[
                _event(1, "BookingCreated", self._created_event().payload()),
                _event(
                    2,
                    "BookingInstructorAssigned",
                    instructor_assigned(
                        booking_activity_id=booking_activity_id,
                        instructor_id=instructor_id,
                    ).payload(),
                ),
                _event(
                    3,
                    "BookingInstructorRemoved",
                    instructor_removed(
                        booking_activity_id=booking_activity_id,
                        instructor_id=instructor_id,
                    ).payload(),
                ),
            ],
            instructor_is_active=True,
        )

        self.assertEqual(appended["event_type"], "BookingInstructorAssigned")
        self.assertEqual(appended["aggregate_version"], 4)
        self.assertEqual(appended["event_data"]["booking_activity_id"], str(booking_activity_id))
        self.assertEqual(appended["event_data"]["instructor_id"], str(instructor_id))

    def test_remove_rejects_booking_activity_from_other_booking(self) -> None:
        booking_activity_id = uuid4()
        instructor_id = uuid4()

        with self.assertRaisesRegex(command_handlers.BookingValidationError, "booking_activity_id must belong"):
            self._run_handler_with_mocks(
                command_handlers.remove_instructor,
                RemoveInstructorCommand(
                    booking_id=uuid4(),
                    booking_activity_id=booking_activity_id,
                    instructor_id=instructor_id,
                    expected_version=2,
                    actor_user_id=uuid4(),
                ),
                events=[
                    _event(1, "BookingCreated", self._created_event().payload()),
                    _event(
                        2,
                        "BookingInstructorAssigned",
                        instructor_assigned(
                            booking_activity_id=booking_activity_id,
                            instructor_id=instructor_id,
                        ).payload(),
                    ),
                ],
                booking_activity_belongs_to_booking=False,
            )

    def test_replay_reconstructs_instructor_active_after_assign_remove_assign(self) -> None:
        booking_id = uuid4()
        booking_activity_id = uuid4()
        instructor_id = uuid4()
        events = [
            _event(1, "BookingCreated", self._created_event().payload()),
            _event(
                2,
                "BookingInstructorAssigned",
                instructor_assigned(booking_activity_id=booking_activity_id, instructor_id=instructor_id).payload(),
            ),
            _event(
                3,
                "BookingInstructorRemoved",
                instructor_removed(booking_activity_id=booking_activity_id, instructor_id=instructor_id).payload(),
            ),
            _event(
                4,
                "BookingInstructorAssigned",
                instructor_assigned(booking_activity_id=booking_activity_id, instructor_id=instructor_id).payload(),
            ),
        ]

        aggregate = BookingAggregate.replay(booking_id, events)

        self.assertEqual(aggregate.active_instructor_assignments, {(booking_activity_id, instructor_id)})
        self.assertEqual(aggregate.version, 4)

    def test_projection_sync_reactivates_assignment_with_new_assigned_at(self) -> None:
        class FakeCursor:
            def __init__(self):
                self.statements: list[str] = []
                self.params: list[object] = []

            def execute(self, sql, params=None):
                self.statements.append(sql)
                self.params.append(params)

        cur = FakeCursor()
        booking_activity_id = uuid4()
        instructor_id = uuid4()

        booking_projection_repository.sync_instructor_projection(
            cur,
            booking_id=uuid4(),
            active_assignments={(booking_activity_id, instructor_id)},
        )

        upsert_sql = cur.statements[-1]
        self.assertIn("assigned_at = now()", upsert_sql)
        self.assertIn("active = true", upsert_sql)
        self.assertIn("removed_at = NULL", upsert_sql)
        self.assertEqual(cur.params[-1], (booking_activity_id, instructor_id))

    def test_stale_expected_version_raises_conflict(self) -> None:
        with self.assertRaises(command_handlers.BookingConcurrencyError):
            self._run_handler_with_mocks(
                command_handlers.change_status,
                ChangeStatusCommand(booking_id=uuid4(), status="CONFIRMED", expected_version=0, actor_user_id=uuid4()),
                events=[_event(1, "BookingCreated", self._created_event().payload())],
            )

    def test_completed_booking_cannot_move_back_to_earlier_status(self) -> None:
        aggregate = self._aggregate_with_status("COMPLETED")

        with self.assertRaisesRegex(ValueError, "Completed or cancelled"):
            aggregate.validate_status_change("CONFIRMED")

    def test_cancelled_booking_rejects_operational_updates(self) -> None:
        aggregate = self._aggregate_with_status("CANCELLED")

        with self.assertRaisesRegex(ValueError, "Cancelled bookings"):
            aggregate.ensure_can_update_operational_fields()

    def _aggregate_with_status(self, status: str) -> BookingAggregate:
        booking_id = uuid4()
        created = self._created_event(status=status)
        return BookingAggregate.replay(booking_id, [_event(1, created.event_type, created.payload())])

    def _created_event(self, status: str = "NEW"):
        return booking_created(
            customer_id=uuid4(),
            activity_id=uuid4(),
            event_at=datetime(2026, 8, 15, 10, 0, tzinfo=UTC),
            city=None,
            venue=None,
            participant_count=1,
            agreed_price=Decimal("0"),
            status=status,
            requires_instructor=False,
            notes=None,
        )

    def _run_handler_with_mocks(
        self,
        handler,
        command,
        events,
        instructor_is_active=True,
        booking_activity_belongs_to_booking=True,
    ) -> dict:
        class FakeCursor:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        class FakeConnection:
            def cursor(self, **kwargs):
                return FakeCursor()

            def commit(self):
                pass

            def rollback(self):
                pass

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        appended: dict = {}

        def append_event(cur, **kwargs):
            appended.update(kwargs)
            return {"event_id": uuid4(), **kwargs}

        with (
            patch.object(command_handlers, "get_connection", return_value=FakeConnection()),
            patch.object(command_handlers.events_repo, "list_events", return_value=events),
            patch.object(command_handlers.events_repo, "append_event", side_effect=append_event),
            patch.object(command_handlers.projection_repo, "upsert_projection", side_effect=lambda cur, data: data),
            patch.object(command_handlers.projection_repo, "sync_instructor_projection"),
            patch.object(command_handlers.projection_repo, "instructor_is_active", return_value=instructor_is_active),
            patch.object(
                command_handlers.projection_repo,
                "booking_activity_belongs_to_booking",
                return_value=booking_activity_belongs_to_booking,
            ),
        ):
            handler(command)

        return appended


if __name__ == "__main__":
    unittest.main()
