from __future__ import annotations

import unittest
from datetime import UTC, datetime
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.core.auth import get_current_user
from backend.app.main import app


class BookingCreationRoleTests(unittest.TestCase):
    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    @staticmethod
    def payload(**changes):
        value = {
            "activity_id": str(uuid4()),
            "event_at": datetime(2027, 1, 2, 10, tzinfo=UTC).isoformat(),
            "participant_count": 12,
            "city": "Jerusalem",
        }
        value.update(changes)
        return value

    @staticmethod
    def response(command):
        return {
            "id": uuid4(), "customer_id": command.customer_id,
            "activity_id": command.activity_id, "event_at": command.event_at,
            "city": command.city, "venue": command.venue,
            "participant_count": command.participant_count,
            "agreed_price": command.agreed_price, "status": command.status,
            "requires_instructor": command.requires_instructor,
            "notes": command.notes, "version": 1,
        }

    def test_customer_identity_and_protected_fields_are_server_controlled(self) -> None:
        customer_id, user_id = uuid4(), uuid4()
        app.dependency_overrides[get_current_user] = lambda: {
            "id": user_id, "role": "customer", "customer_id": customer_id,
        }
        with patch("backend.app.routers.bookings.command_handlers.create_booking") as create:
            create.side_effect = self.response
            response = TestClient(app).post("/bookings", json=self.payload(
                agreed_price="999", status="CONFIRMED", requires_instructor=True,
            ))
        self.assertEqual(response.status_code, 201)
        command = create.call_args.args[0]
        self.assertEqual(command.customer_id, customer_id)
        self.assertEqual(str(command.agreed_price), "0")
        self.assertEqual(command.status, "NEW")
        self.assertFalse(command.requires_instructor)

    def test_customer_cannot_tamper_with_customer_identity(self) -> None:
        app.dependency_overrides[get_current_user] = lambda: {
            "id": uuid4(), "role": "customer", "customer_id": uuid4(),
        }
        response = TestClient(app).post(
            "/bookings", json=self.payload(customer_id=str(uuid4()))
        )
        self.assertEqual(response.status_code, 403)

    def test_instructor_creation_is_denied_before_command_dispatch(self) -> None:
        app.dependency_overrides[get_current_user] = lambda: {
            "id": uuid4(), "role": "instructor", "instructor_id": uuid4(),
        }
        with patch("backend.app.routers.bookings.command_handlers.create_booking") as create:
            response = TestClient(app).post("/bookings", json=self.payload())
        self.assertEqual(response.status_code, 403)
        create.assert_not_called()

    def test_manager_must_supply_customer(self) -> None:
        app.dependency_overrides[get_current_user] = lambda: {"id": uuid4(), "role": "manager"}
        response = TestClient(app).post("/bookings", json=self.payload())
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
