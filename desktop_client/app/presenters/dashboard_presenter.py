from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from desktop_client.app.presenters.formatting import booking_row


class DashboardViewPort(Protocol):
    def set_loading(self, loading: bool) -> None: ...
    def show_error(self, message: str) -> None: ...
    def show_summary(self, summary: dict[str, int]) -> None: ...
    def show_sections(self, first_title: str, first_rows: list[dict[str, str]], second_title: str, second_rows: list[dict[str, str]]) -> None: ...


class DashboardServicePort(Protocol):
    def dashboard(self) -> dict: ...
    def list_bookings(self, filters: dict[str, object] | None = None) -> dict: ...
    def my_bookings(self, *, limit: int = 50, offset: int = 0) -> dict: ...
    def open_events(self) -> list[dict]: ...


class DashboardPresenter:
    def __init__(self, view: DashboardViewPort, service: DashboardServicePort, role: str, navigate=lambda _key, _filters=None: None, create_booking=lambda: None) -> None:
        self.view = view
        self.service = service
        self.role = role
        self.navigate = navigate
        self.create_booking = create_booking

    def drill_down(self, target: str) -> None:
        status_filters = {"pending_count": "NEW", "confirmed_count": "CONFIRMED", "cancelled_count": "CANCELLED"}
        if target in status_filters:
            self.navigate("my_bookings" if self.role == "customer" else "bookings", {"status": status_filters[target]})
        elif target == "unassigned_count":
            self.navigate("open_events", None)
        elif target in {"upcoming_count", "assigned_count"}:
            destination = "my_bookings" if self.role == "customer" else "bookings"
            self.navigate(destination, {"from_date": datetime.now(UTC).isoformat()})
        else:
            self.navigate(target, None)

    def load(self) -> None:
        self.view.set_loading(True)
        errors = []
        summary = {}
        first_title = second_title = ""
        first = second = []
        try:
            summary = self.service.dashboard()
        except Exception as exc:
            errors.append(str(exc))
        try:
            if self.role == "customer":
                mine = self.service.my_bookings(limit=10, offset=0)["items"]
                first_title, first = "ההזמנות הקרובות שלי", mine
                second_title, second = "", []
            elif self.role == "instructor":
                assigned = self.service.list_bookings({"limit": 10, "from_date": datetime.now(UTC).isoformat()})["items"]
                opened = self.service.open_events()
                first_title, first = "אירועים משויכים", assigned
                second_title, second = "אירועים פתוחים", opened
            else:
                upcoming = self.service.list_bookings({"limit": 10, "from_date": datetime.now(UTC).isoformat()})["items"]
                opened = self.service.open_events()
                first_title, first = "הזמנות קרובות", upcoming
                second_title, second = "דורשים שיבוץ", opened
        except Exception as exc:
            errors.append(str(exc))
        if summary:
            self.view.show_summary(summary)
        self.view.show_sections(first_title, [booking_row(item) for item in first], second_title, [booking_row(item) for item in second])
        if errors:
            self.view.show_error(" | ".join(errors))
        self.view.set_loading(False)
