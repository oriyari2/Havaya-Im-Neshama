from datetime import UTC, datetime
from unittest import TestCase
from unittest.mock import MagicMock, patch
from uuid import uuid4

from backend.app.application.bookings import assignment_request_handlers as handlers
from backend.app.application.bookings.query_handlers import BookingAccessDeniedError
from backend.app.schemas.booking_assignment import AssignmentRequestResponse, OpenEventDetailResponse


class AssignmentRequestTests(TestCase):
    @patch.object(handlers, "get_connection")
    @patch.object(handlers.repo, "upsert_assignment_request")
    @patch.object(handlers.repo, "get_requestable_activity")
    @patch.object(handlers.repo, "instructor_is_active")
    def test_instructor_can_request_open_activity(self, active, requestable, upsert, get_connection):
        booking_id, activity_id, instructor_id, request_id = uuid4(), uuid4(), uuid4(), uuid4()
        active.return_value = True
        requestable.return_value = {"booking_activity_id": activity_id}
        upsert.return_value = {
            "request_id": request_id,
            "booking_activity_id": activity_id,
            "instructor_id": instructor_id,
            "status": "PENDING",
            "requested_at": datetime.now(UTC),
        }
        conn = MagicMock()
        cur = MagicMock()
        get_connection.return_value.__enter__.return_value = conn
        conn.cursor.return_value.__enter__.return_value = cur

        result = handlers.request_assignment(
            booking_id,
            activity_id,
            {"role": "instructor", "instructor_id": instructor_id},
        )

        self.assertEqual(result["request_id"], request_id)
        upsert.assert_called_once_with(cur, activity_id, instructor_id)
        conn.commit.assert_called_once()
        conn.rollback.assert_not_called()

    def test_only_linked_instructor_can_request_assignment(self):
        for user in ({"role": "customer"}, {"role": "instructor"}, {"role": "manager"}):
            with self.subTest(user=user), self.assertRaises(BookingAccessDeniedError):
                handlers.request_assignment(uuid4(), uuid4(), user)

    @patch.object(handlers.repo, "resolve_approved_request")
    @patch.object(handlers.repo, "get_request_for_manager")
    @patch.object(handlers.command_handlers, "assign_instructor")
    @patch.object(handlers, "get_connection")
    def test_manager_approval_reuses_event_sourced_assignment(self, get_connection, assign, get_request, resolve):
        booking_id, request_id, activity_id, instructor_id, manager_id = (
            uuid4(), uuid4(), uuid4(), uuid4(), uuid4()
        )
        get_request.return_value = {
            "request_id": request_id,
            "booking_activity_id": activity_id,
            "instructor_id": instructor_id,
            "status": "PENDING",
            "version": 7,
        }
        assign.return_value = {"id": booking_id, "version": 8}
        connections = [MagicMock(), MagicMock()]
        cursors = [MagicMock(), MagicMock()]
        for conn, cur in zip(connections, cursors):
            conn.cursor.return_value.__enter__.return_value = cur
        get_connection.side_effect = [
            _Context(connections[0]),
            _Context(connections[1]),
        ]

        result = handlers.approve_request(
            booking_id,
            request_id,
            7,
            {"role": "manager", "id": manager_id},
        )

        command = assign.call_args.args[0]
        self.assertEqual(command.booking_id, booking_id)
        self.assertEqual(command.booking_activity_id, activity_id)
        self.assertEqual(command.instructor_id, instructor_id)
        self.assertEqual(command.expected_version, 7)
        self.assertEqual(result["version"], 8)
        resolve.assert_called_once_with(cursors[1], activity_id, instructor_id, manager_id)
        connections[1].commit.assert_called_once()

    def test_assignment_response_keeps_request_and_open_event_customer_contact_safe(self):
        request = AssignmentRequestResponse(
            request_id=uuid4(),
            booking_activity_id=uuid4(),
            instructor_id=uuid4(),
            instructor_name="מדריכה",
            status="PENDING",
            requested_at=datetime.now(UTC),
        ).model_dump()
        self.assertEqual(request["status"], "PENDING")

        detail = OpenEventDetailResponse(
            booking_id=uuid4(),
            event_at=datetime.now(UTC),
            status="NEW",
            requires_instructor=True,
            version=2,
            customer_name="לקוח",
            customer_contact_name="איש קשר",
            customer_phone="050-1234567",
            activities=[],
        ).model_dump()
        self.assertEqual(detail["customer_name"], "לקוח")
        self.assertEqual(detail["customer_phone"], "050-1234567")
        for protected in ("customer_id", "agreed_price", "notes", "participant_count"):
            self.assertNotIn(protected, detail)


class _Context:
    def __init__(self, value):
        self.value = value

    def __enter__(self):
        return self.value

    def __exit__(self, exc_type, exc, tb):
        return False
