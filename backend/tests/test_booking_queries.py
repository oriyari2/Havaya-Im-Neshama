from __future__ import annotations

from datetime import UTC, datetime
import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi import HTTPException

from backend.app.application.bookings import query_handlers
from backend.app.db.seed_demo_data import BOOKINGS
from backend.app.domain.bookings.status import BookingStatus
from backend.app.infrastructure.repositories import booking_projection_repository
from backend.app.schemas.booking import (
    BookingResponse,
    CustomerBookingSummaryResponse,
    InstructorBookingResponse,
    OpenEventResponse,
)


class _DummyCursor:
    def __enter__(self) -> "_DummyCursor":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class _DummyConnection:
    def __enter__(self) -> "_DummyConnection":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def cursor(self, row_factory=None) -> _DummyCursor:
        return _DummyCursor()


class _CaptureCursor:
    def __init__(self) -> None:
        self.executed_sql = ""
        self.params: list[object] = []

    def execute(self, query: str, params: list[object]) -> None:
        self.executed_sql = query
        self.params = params

    def fetchall(self) -> list[dict]:
        return []

    def fetchone(self) -> dict:
        return {}


class BookingQueryTests(unittest.TestCase):
    def test_manager_can_list_bookings_with_filters(self) -> None:
        current_user = {"role": "manager"}
        customer_id = uuid4()
        activity_id = uuid4()
        instructor_id = uuid4()
        from_date = datetime(2026, 1, 1, tzinfo=UTC)
        to_date = datetime(2026, 1, 31, tzinfo=UTC)

        with patch("backend.app.application.bookings.query_handlers.get_connection", return_value=_DummyConnection()):
            with patch("backend.app.application.bookings.query_handlers.projection_repo.list_bookings", return_value=[]) as list_bookings_mock:
                query_handlers.list_bookings(
                    current_user,
                    None,
                    10,
                    2,
                    customer_id=customer_id,
                    activity_id=activity_id,
                    instructor_id=instructor_id,
                    from_date=from_date,
                    to_date=to_date,
                )

        list_bookings_mock.assert_called_once()
        args, kwargs = list_bookings_mock.call_args
        self.assertEqual(args[0], unittest.mock.ANY)
        self.assertEqual(kwargs["role"], "manager")
        self.assertEqual(kwargs["customer_filter_id"], customer_id)
        self.assertEqual(kwargs["activity_id"], activity_id)
        self.assertEqual(kwargs["instructor_filter_id"], instructor_id)
        self.assertEqual(kwargs["status"], None)
        self.assertEqual(kwargs["from_date"], from_date)
        self.assertEqual(kwargs["to_date"], to_date)
        self.assertEqual(kwargs["limit"], 10)
        self.assertEqual(kwargs["offset"], 2)

    def test_customer_rejects_customer_id_filter(self) -> None:
        current_user = {"role": "customer", "customer_id": uuid4()}

        with self.assertRaises(query_handlers.BookingValidationError):
            query_handlers.list_bookings(current_user, None, 50, 0, customer_id=uuid4())

    def test_customer_rejects_instructor_id_filter(self) -> None:
        current_user = {"role": "customer", "customer_id": uuid4()}

        with self.assertRaises(query_handlers.BookingValidationError):
            query_handlers.list_bookings(current_user, None, 50, 0, instructor_id=uuid4())

    def test_instructor_rejects_customer_id_filter(self) -> None:
        current_user = {"role": "instructor", "instructor_id": uuid4()}

        with self.assertRaises(query_handlers.BookingValidationError):
            query_handlers.list_bookings(current_user, None, 50, 0, customer_id=uuid4())

    def test_instructor_rejects_instructor_id_filter(self) -> None:
        current_user = {"role": "instructor", "instructor_id": uuid4()}

        with self.assertRaises(query_handlers.BookingValidationError):
            query_handlers.list_bookings(current_user, None, 50, 0, instructor_id=uuid4())

    def test_dashboard_summary_calls_repository_with_visibility_scope(self) -> None:
        current_user = {"role": "instructor", "instructor_id": uuid4()}

        with patch("backend.app.application.bookings.query_handlers.get_connection", return_value=_DummyConnection()):
            with patch("backend.app.application.bookings.query_handlers.projection_repo.get_dashboard_summary", return_value={}) as summary_mock:
                query_handlers.get_dashboard_summary(current_user)

        summary_mock.assert_called_once()
        args, kwargs = summary_mock.call_args
        self.assertEqual(args[0], unittest.mock.ANY)
        self.assertEqual(kwargs["role"], "instructor")
        self.assertEqual(kwargs["customer_id"], None)
        self.assertEqual(kwargs["instructor_id"], current_user["instructor_id"])
        self.assertIn("now", kwargs)

    def test_dashboard_sql_counts_only_upcoming_domain_statuses(self) -> None:
        cursor = _CaptureCursor()
        now = datetime(2026, 7, 1, tzinfo=UTC)

        booking_projection_repository.get_dashboard_summary(
            cursor,
            role="manager",
            customer_id=None,
            instructor_id=None,
            now=now,
        )

        normalized_sql = " ".join(cursor.executed_sql.split())
        self.assertIn(
            "COUNT(*) FILTER (WHERE status = %s AND event_at >= %s) AS confirmed_count",
            normalized_sql,
        )
        self.assertIn(
            "COUNT(*) FILTER (WHERE status = %s AND event_at >= %s) AS pending_count",
            normalized_sql,
        )
        self.assertIn(
            "COUNT(*) FILTER (WHERE status = %s AND event_at >= %s) AS cancelled_count",
            normalized_sql,
        )
        self.assertIn(
            "COUNT(*) FILTER (WHERE event_at >= %s) AS upcoming_count",
            normalized_sql,
        )
        self.assertEqual(
            cursor.params,
            [
                BookingStatus.CONFIRMED.value,
                now,
                BookingStatus.NEW.value,
                now,
                BookingStatus.CANCELLED.value,
                now,
                now,
                now,
                now,
            ],
        )
        self.assertNotIn(BookingStatus.COMPLETED.value, cursor.params)
        self.assertNotIn("confirmed", cursor.params)
        self.assertNotIn("pending", cursor.params)
        self.assertNotIn("cancelled", cursor.params)
        self.assertIn("AS assigned_count", normalized_sql)
        self.assertIn("AS unassigned_count", normalized_sql)
        self.assertIn("FROM bookings b", normalized_sql)
        self.assertIn("ba.booking_id = b.id", normalized_sql)
        self.assertEqual(normalized_sql.count("event_at >= %s"), 6)

    def test_dashboard_assignment_buckets_count_bookings_without_join_duplicates(self) -> None:
        cursor = _CaptureCursor()

        booking_projection_repository.get_dashboard_summary(
            cursor,
            role="manager",
            customer_id=None,
            instructor_id=None,
            now=datetime(2026, 7, 1, tzinfo=UTC),
        )

        normalized_sql = " ".join(cursor.executed_sql.split())
        self.assertIn("COUNT(*) FILTER", normalized_sql)
        self.assertNotIn("FROM bookings b JOIN booking_activities", normalized_sql)
        self.assertIn("AND EXISTS (SELECT 1 FROM booking_activities", normalized_sql)
        self.assertIn("AND NOT EXISTS ( SELECT 1 FROM booking_activities", normalized_sql)

    def test_demo_booking_statuses_use_only_domain_values(self) -> None:
        supported_statuses = {status.value for status in BookingStatus}
        seeded_statuses = {booking[10] for booking in BOOKINGS}

        self.assertEqual(
            seeded_statuses,
            {BookingStatus.NEW.value, BookingStatus.CONFIRMED.value},
        )
        self.assertTrue(seeded_statuses <= supported_statuses)

    def test_open_events_rejects_customer_role(self) -> None:
        current_user = {"role": "customer", "customer_id": uuid4()}

        with self.assertRaises(query_handlers.BookingAccessDeniedError):
            query_handlers.get_open_events(current_user)

    def test_open_events_uses_visibility_scope_for_manager(self) -> None:
        current_user = {"role": "manager"}

        with patch("backend.app.application.bookings.query_handlers.get_connection", return_value=_DummyConnection()):
            with patch("backend.app.application.bookings.query_handlers.projection_repo.get_open_events", return_value=[]) as open_events_mock:
                query_handlers.get_open_events(current_user)

        open_events_mock.assert_called_once_with(
            unittest.mock.ANY,
            role="manager",
            customer_id=None,
            instructor_id=None,
            now=unittest.mock.ANY,
        )

    def test_instructor_open_events_does_not_require_existing_assignment(self) -> None:
        cursor = _CaptureCursor()
        instructor_id = uuid4()
        now = datetime(2026, 7, 1, tzinfo=UTC)

        booking_projection_repository.get_open_events(
            cursor,
            role="instructor",
            customer_id=None,
            instructor_id=instructor_id,
            now=now,
        )

        self.assertEqual(cursor.params, [now])
        self.assertNotIn("bi.instructor_id = %s", cursor.executed_sql)
        self.assertIn("status IN ('NEW', 'CONFIRMED')", cursor.executed_sql)
        self.assertIn("requires_instructor = true", cursor.executed_sql)
        self.assertIn("event_at >= %s", cursor.executed_sql)
        self.assertIn("active = true", cursor.executed_sql)
        self.assertIn("FROM bookings b", cursor.executed_sql)
        self.assertIn("ba.booking_id = b.id", cursor.executed_sql)
        self.assertNotIn("bookings.id", cursor.executed_sql)

    def test_list_query_uses_correct_aliases_and_combined_filters(self) -> None:
        cursor = _CaptureCursor()
        customer_id = uuid4()
        activity_id = uuid4()
        instructor_id = uuid4()
        from_date = datetime(2026, 7, 1, tzinfo=UTC)
        to_date = datetime(2026, 8, 1, tzinfo=UTC)

        booking_projection_repository.list_bookings(
            cursor,
            role="manager",
            customer_filter_id=customer_id,
            instructor_filter_id=instructor_id,
            activity_id=activity_id,
            status=BookingStatus.CONFIRMED.value,
            from_date=from_date,
            to_date=to_date,
            limit=25,
            offset=5,
        )

        self.assertIn("FROM bookings b", cursor.executed_sql)
        self.assertNotIn("bookings.id", cursor.executed_sql)
        self.assertIn("ba.booking_id = b.id", cursor.executed_sql)
        self.assertEqual(
            cursor.params,
            [customer_id, instructor_id, activity_id, BookingStatus.CONFIRMED.value, from_date, to_date, 25, 5],
        )

    def test_instructor_detail_query_uses_booking_alias(self) -> None:
        cursor = _CaptureCursor()
        booking_id = uuid4()
        instructor_id = uuid4()

        booking_projection_repository.get_booking(
            cursor,
            booking_id,
            role="instructor",
            instructor_id=instructor_id,
        )

        self.assertIn("FROM bookings b", cursor.executed_sql)
        self.assertIn("ba.booking_id = b.id", cursor.executed_sql)
        self.assertNotIn("bookings.id", cursor.executed_sql)
        self.assertEqual(cursor.params, [booking_id, instructor_id])

    def test_open_event_response_schema_omits_sensitive_fields(self) -> None:
        payload = {
            "id": uuid4(),
            "activity_id": uuid4(),
            "event_at": datetime(2026, 7, 10, 9, 0, tzinfo=UTC),
            "city": "Jerusalem",
            "venue": "Hall",
            "status": "NEW",
            "requires_instructor": True,
            "version": 2,
            "created_at": datetime(2026, 7, 1, 10, 0, tzinfo=UTC),
            "updated_at": datetime(2026, 7, 2, 11, 0, tzinfo=UTC),
            "customer_id": uuid4(),
            "agreed_price": "100",
            "notes": "private",
            "participant_count": 10,
        }

        response = OpenEventResponse(**payload)
        self.assertEqual(response.activity_id, payload["activity_id"])
        self.assertNotIn("customer_id", response.model_dump())
        self.assertNotIn("agreed_price", response.model_dump())
        self.assertNotIn("notes", response.model_dump())
        self.assertNotIn("participant_count", response.model_dump())

    def test_instructor_booking_schema_omits_protected_fields_but_keeps_participant_count(self) -> None:
        payload = self._booking_payload()

        response = InstructorBookingResponse(**payload)
        serialized = response.model_dump()

        self.assertNotIn("customer_id", serialized)
        self.assertNotIn("agreed_price", serialized)
        self.assertNotIn("notes", serialized)
        self.assertEqual(serialized["participant_count"], payload["participant_count"])
        self.assertIn("activity_name", serialized)

    def test_booking_query_joins_readable_names_without_exposing_customer_to_instructor_schema(self) -> None:
        cursor = _CaptureCursor()
        booking_projection_repository.list_bookings(cursor, role="manager", limit=25, offset=0)
        self.assertIn("c.name AS customer_name", cursor.executed_sql)
        self.assertIn("a.name AS activity_name", cursor.executed_sql)
        payload = {**self._booking_payload(), "customer_name": "Customer", "activity_name": "Activity"}
        safe = InstructorBookingResponse(**payload).model_dump()
        self.assertEqual(safe["activity_name"], "Activity")
        self.assertNotIn("customer_name", safe)

    def test_manager_and_customer_full_booking_schema_remains_unchanged(self) -> None:
        payload = self._booking_payload()

        response = BookingResponse(**payload).model_dump()

        self.assertEqual(response["customer_id"], payload["customer_id"])
        self.assertEqual(str(response["agreed_price"]), payload["agreed_price"])
        self.assertEqual(response["notes"], payload["notes"])

    def test_router_serializes_instructor_list_and_detail_with_safe_schema(self) -> None:
        from backend.app.routers import bookings as bookings_router

        payload = self._booking_payload()
        instructor = {"role": "instructor", "instructor_id": uuid4()}
        with patch.object(query_handlers, "list_bookings", return_value=[payload]):
            listed = bookings_router.list_bookings(
                status=None,
                customer_id=None,
                activity_id=None,
                instructor_id=None,
                from_date=None,
                to_date=None,
                limit=50,
                offset=0,
                current_user=instructor,
            )
        with patch.object(query_handlers, "get_booking", return_value=payload):
            detailed = bookings_router.get_booking(payload["id"], current_user=instructor)

        self.assertIsInstance(listed.items[0], InstructorBookingResponse)
        self.assertIsInstance(detailed, InstructorBookingResponse)
        for serialized in (listed.items[0].model_dump(), detailed.model_dump()):
            self.assertNotIn("customer_id", serialized)
            self.assertNotIn("agreed_price", serialized)
            self.assertNotIn("notes", serialized)

    def test_router_keeps_manager_and_customer_full_booking_responses(self) -> None:
        from backend.app.routers import bookings as bookings_router

        payload = self._booking_payload()
        for current_user in (
            {"role": "manager"},
            {"role": "customer", "customer_id": payload["customer_id"]},
        ):
            with patch.object(query_handlers, "get_booking", return_value=payload):
                response = bookings_router.get_booking(payload["id"], current_user=current_user)
            self.assertIsInstance(response, BookingResponse)
            self.assertEqual(response.customer_id, payload["customer_id"])
            self.assertEqual(str(response.agreed_price), payload["agreed_price"])

    def test_customer_booking_summary_is_compact(self) -> None:
        response = CustomerBookingSummaryResponse(**self._booking_payload()).model_dump()

        self.assertNotIn("customer_id", response)
        self.assertNotIn("agreed_price", response)
        self.assertNotIn("notes", response)
        self.assertNotIn("participant_count", response)

    def test_raw_history_is_manager_only(self) -> None:
        booking_id = uuid4()
        for user in (
            {"role": "instructor", "instructor_id": uuid4()},
            {"role": "customer", "customer_id": uuid4()},
        ):
            with self.assertRaises(query_handlers.BookingAccessDeniedError):
                query_handlers.get_history(booking_id, user)

        with patch.object(query_handlers, "get_booking", return_value=self._booking_payload()) as booking_mock:
            with patch("backend.app.application.bookings.query_handlers.get_connection", return_value=_DummyConnection()):
                with patch.object(query_handlers.events_repo, "list_events", return_value=[{"event_type": "BookingCreated"}]):
                    result = query_handlers.get_history(booking_id, {"role": "manager"})
        self.assertEqual(result, [{"event_type": "BookingCreated"}])
        booking_mock.assert_called_once_with(booking_id, {"role": "manager"})

    def test_dashboard_route_uses_dashboard_path(self) -> None:
        from backend.app.routers import bookings as bookings_router

        routes = {route.path for route in bookings_router.router.routes}
        self.assertIn("/bookings/dashboard", routes)
        self.assertIn("/bookings/my-bookings", routes)

    def test_my_bookings_is_customer_only_and_reuses_scoped_list(self) -> None:
        customer = {"role": "customer", "customer_id": uuid4()}
        owned = [self._booking_payload(customer_id=customer["customer_id"])]

        with patch.object(query_handlers, "list_bookings", return_value=owned) as list_mock:
            result = query_handlers.get_my_bookings(customer, 20, 3)

        self.assertEqual(result, owned)
        list_mock.assert_called_once_with(customer, None, 20, 3)

        with self.assertRaises(query_handlers.BookingAccessDeniedError):
            query_handlers.get_my_bookings({"role": "manager"}, 20, 0)

    def test_my_bookings_router_returns_403_for_non_customer(self) -> None:
        from backend.app.routers import bookings as bookings_router

        with self.assertRaises(HTTPException) as raised:
            bookings_router.get_my_bookings(limit=20, offset=0, current_user={"role": "instructor"})

        self.assertEqual(raised.exception.status_code, 403)

    def test_list_bookings_returns_empty_list_for_empty_results(self) -> None:
        current_user = {"role": "manager"}

        with patch("backend.app.application.bookings.query_handlers.get_connection", return_value=_DummyConnection()):
            with patch("backend.app.application.bookings.query_handlers.projection_repo.list_bookings", return_value=[]) as list_bookings_mock:
                result = query_handlers.list_bookings(current_user, None, 50, 0)

        self.assertEqual(result, [])
        list_bookings_mock.assert_called_once()

    @staticmethod
    def _booking_payload(*, customer_id=None) -> dict:
        return {
            "id": uuid4(),
            "customer_id": customer_id or uuid4(),
            "activity_id": uuid4(),
            "event_at": datetime(2026, 8, 15, 10, 0, tzinfo=UTC),
            "city": "Jerusalem",
            "venue": "Hall",
            "participant_count": 24,
            "agreed_price": "1200",
            "status": BookingStatus.NEW.value,
            "requires_instructor": True,
            "notes": "private",
            "version": 1,
            "created_at": datetime(2026, 7, 1, tzinfo=UTC),
            "updated_at": datetime(2026, 7, 2, tzinfo=UTC),
        }
