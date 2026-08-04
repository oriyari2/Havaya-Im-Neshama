from __future__ import annotations

from desktop_client.app.api.client import ApiClient


class BookingService:
    def __init__(self, api_client: ApiClient) -> None:
        self.api_client = api_client

    def dashboard(self) -> dict:
        return self.api_client.get("/bookings/dashboard")

    def list_bookings(self, filters: dict[str, object] | None = None) -> dict:
        return self.api_client.get("/bookings", filters)

    def invalidate_list(self, filters: dict[str, object] | None = None) -> None:
        self.api_client.invalidate_cached_get("/bookings", filters)

    def invalidate_open_events(self) -> None:
        self.api_client.invalidate_cached_get("/bookings/open-events")

    def my_bookings(self, *, limit: int = 50, offset: int = 0, order_by: str = "event_at") -> dict:
        return self.api_client.get("/bookings/my-bookings", {"limit": limit, "offset": offset, "order_by": order_by})

    def open_events(self) -> list[dict]:
        return self.api_client.get("/bookings/open-events")

    def open_event_detail(self, booking_id: str) -> dict:
        return self.api_client.get(f"/bookings/open-events/{booking_id}")

    def booking(self, booking_id: str) -> dict:
        return self.api_client.get(f"/bookings/{booking_id}")

    def history(self, booking_id: str) -> list[dict]:
        return self.api_client.get(f"/bookings/{booking_id}/history")

    def booking_form_options(self, *, include_customers: bool = True) -> tuple[list[dict], list[dict]]:
        customers = self.api_client.get("/customers", {"is_active": True, "limit": 50}) if include_customers else {"items": []}
        activities = self.api_client.get("/activities", {"is_active": True, "limit": 50})
        return customers["items"], activities["items"]

    def create_booking(self, payload: dict[str, object]) -> dict:
        return self.api_client.post("/bookings", payload)

    def change_status(self, booking_id: str, status: str, expected_version: int) -> dict:
        return self.api_client.patch(
            f"/bookings/{booking_id}/status",
            {"status": status, "expected_version": expected_version},
        )

    def change_schedule(self, booking_id: str, event_at: str, expected_version: int) -> dict:
        return self.api_client.patch(
            f"/bookings/{booking_id}/schedule",
            {"event_at": event_at, "expected_version": expected_version},
        )

    def change_price(self, booking_id: str, agreed_price: str, expected_version: int) -> dict:
        return self.api_client.patch(
            f"/bookings/{booking_id}/price",
            {"agreed_price": agreed_price, "expected_version": expected_version},
        )

    def change_location(self, booking_id: str, city: str | None, venue: str | None, expected_version: int) -> dict:
        return self.api_client.patch(
            f"/bookings/{booking_id}/location",
            {"city": city, "venue": venue, "expected_version": expected_version},
        )

    def change_participant_count(self, booking_id: str, participant_count: int, expected_version: int) -> dict:
        return self.api_client.patch(
            f"/bookings/{booking_id}/participant-count",
            {"participant_count": participant_count, "expected_version": expected_version},
        )

    def update_notes(self, booking_id: str, notes: str | None, expected_version: int) -> dict:
        return self.api_client.patch(
            f"/bookings/{booking_id}/notes",
            {"notes": notes, "expected_version": expected_version},
        )
