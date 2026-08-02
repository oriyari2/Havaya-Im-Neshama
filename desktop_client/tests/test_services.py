from __future__ import annotations

import unittest

from desktop_client.app.services.booking_service import BookingService
from desktop_client.app.services.ai_chat_service import AIChatService


class _ApiClient:
    def __init__(self, post_response=None) -> None:
        self.calls = []
        self.post_response = post_response or {"id": "booking-id", "version": 1}

    def get(self, path, params=None):
        self.calls.append((path, params))
        return [] if path.endswith("open-events") or path.endswith("history") else {}

    def post(self, path, payload):
        self.calls.append(("POST", path, payload))
        return self.post_response

    def patch(self, path, payload):
        self.calls.append(("PATCH", path, payload))
        return {"id": "booking-id", "version": payload["expected_version"] + 1}


class BookingServiceTests(unittest.TestCase):
    def test_ai_chat_service_uses_consult_endpoint(self) -> None:
        ai_response = {
            "answer": "Grounded answer [1].",
            "answer_basis": "rag",
            "sources": [{"chunk_id": "c1", "source_title": "Task17 Equipment", "source_uri": "demo://equipment"}],
        }
        client = _ApiClient(post_response=ai_response)
        service = AIChatService(client)

        answer = service.consult("שלום")

        self.assertEqual(answer, ai_response)
        self.assertEqual(client.calls, [("POST", "/api/ai/consult", {"prompt": "שלום"})])

    def test_booking_service_uses_completed_task_09_endpoints(self) -> None:
        client = _ApiClient()
        service = BookingService(client)

        service.dashboard()
        service.list_bookings({"status": "CONFIRMED"})
        service.my_bookings(limit=20, offset=2)
        service.open_events()
        service.booking("booking-id")
        service.history("booking-id")

        self.assertEqual(
            client.calls,
            [
                ("/bookings/dashboard", None),
                ("/bookings", {"status": "CONFIRMED"}),
                ("/bookings/my-bookings", {"limit": 20, "offset": 2, "order_by": "event_at"}),
                ("/bookings/open-events", None),
                ("/bookings/booking-id", None),
                ("/bookings/booking-id/history", None),
            ],
        )

    def test_booking_service_uses_event_sourced_command_endpoints(self) -> None:
        client = _ApiClient()
        service = BookingService(client)
        service.create_booking({"status": "NEW"})
        service.change_status("b", "CONFIRMED", 1)
        service.change_schedule("b", "2026-09-01T10:00:00Z", 2)
        service.change_price("b", "1500", 3)
        service.change_location("b", "ירושלים", "אולם", 4)
        service.change_participant_count("b", 30, 5)
        service.update_notes("b", "הערה", 6)

        self.assertEqual(
            client.calls,
            [
                ("POST", "/bookings", {"status": "NEW"}),
                ("PATCH", "/bookings/b/status", {"status": "CONFIRMED", "expected_version": 1}),
                ("PATCH", "/bookings/b/schedule", {"event_at": "2026-09-01T10:00:00Z", "expected_version": 2}),
                ("PATCH", "/bookings/b/price", {"agreed_price": "1500", "expected_version": 3}),
                ("PATCH", "/bookings/b/location", {"city": "ירושלים", "venue": "אולם", "expected_version": 4}),
                ("PATCH", "/bookings/b/participant-count", {"participant_count": 30, "expected_version": 5}),
                ("PATCH", "/bookings/b/notes", {"notes": "הערה", "expected_version": 6}),
            ],
        )


if __name__ == "__main__":
    unittest.main()
