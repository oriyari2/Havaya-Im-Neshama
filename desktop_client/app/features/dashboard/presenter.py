from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from desktop_client.app.models.operation import OperationExecutor, PresenterOperations
from desktop_client.app.features.bookings.formatting import booking_row


class DashboardViewPort(Protocol):
    def set_loading(self, loading: bool) -> None: ...
    def show_error(self, message: str) -> None: ...
    def show_summary(self, summary: dict[str, int]) -> None: ...
    def show_sections(self, first_title: str, first_rows: list[dict[str, str]], second_title: str, second_rows: list[dict[str, str]]) -> None: ...
    def set_registration_loading(self, booking_activity_id: str, loading: bool) -> None: ...
    def set_registration_pending(self, booking_activity_id: str) -> None: ...


class DashboardServicePort(Protocol):
    def dashboard(self) -> dict: ...
    def list_bookings(self, filters: dict[str, object] | None = None) -> dict: ...
    def my_bookings(self, *, limit: int = 50, offset: int = 0) -> dict: ...
    def open_events(self) -> list[dict]: ...
    def request_assignment(self, booking_id: str, booking_activity_id: str) -> dict: ...


class DashboardPresenter:
    def __init__(self, view: DashboardViewPort, service: DashboardServicePort, role: str, navigate=lambda _key, _filters=None: None, create_booking=lambda: None, executor: OperationExecutor | None = None) -> None:
        self.view = view
        self.service = service
        self.role = role
        self.navigate = navigate
        self.create_booking = create_booking
        self._operations = PresenterOperations(executor, "dashboard")
        self._has_rendered = False
        self._assignment_submitting = False

    def invalidate_requests(self) -> None:
        self._operations.invalidate()
        self.view.set_loading(False)

    def drill_down(self, target: str) -> None:
        status_filters = {"pending_count": "NEW", "confirmed_count": "CONFIRMED", "cancelled_count": "CANCELLED"}
        if target in status_filters:
            self.navigate("my_bookings" if self.role == "customer" else "bookings", {"status": status_filters[target]})
        elif target == "unassigned_count":
            self.navigate("bookings", {"queue": "unassigned"})
        elif target in {"upcoming_count", "assigned_count"}:
            destination = "my_bookings" if self.role == "customer" else "bookings"
            filters = {"from_date": datetime.now(UTC).isoformat()}
            if self.role == "instructor" and target == "assigned_count":
                filters["assignment_state"] = "assigned"
            self.navigate(destination, filters)
        else:
            self.navigate(target, None)


    def request_assignment(self, row: dict) -> None:
        if self.role != "instructor" or self._assignment_submitting:
            return
        booking_id = str(row.get("booking_id") or row.get("id") or "")
        booking_activity_id = str(row.get("booking_activity_id") or "")
        if not booking_id or not booking_activity_id:
            self.view.show_error("לא ניתן לזהות את האירוע לבקשת השיבוץ.")
            return

        context = self._operations.begin("assignment_request")
        if context is None:
            return
        self._assignment_submitting = True
        self.view.set_registration_loading(booking_activity_id, True)

        def succeeded(_request) -> None:
            if self._operations.is_current(context):
                # The POST already returned success, so reflect the new state
                # immediately instead of waiting for a second dashboard fetch.
                # This also prevents a brief flash back to "הירשם לאירוע".
                self.view.set_registration_pending(booking_activity_id)

        def failed(_exc: Exception) -> None:
            if self._operations.is_current(context):
                self.view.show_error("לא ניתן לשלוח את בקשת השיבוץ. נסו שוב.")

        def finished() -> None:
            if self._operations.finish(context):
                self._assignment_submitting = False
                self.view.set_registration_loading(booking_activity_id, False)

        self._operations.executor.submit(
            context,
            lambda: self.service.request_assignment(booking_id, booking_activity_id),
            succeeded,
            failed,
            finished,
        )

    def load(self) -> None:
        context = self._operations.replace("load")
        if not self._has_rendered:
            self.view.set_loading(True)

        def operation():
            errors: list[str] = []
            summary: dict = {}
            first_title = second_title = ""
            first: list[dict] = []
            second: list[dict] = []
            try:
                summary = self.service.dashboard()
            except Exception:
                errors.append("לא ניתן לטעון את נתוני הסיכום.")
            try:
                if self.role == "customer":
                    first = self.service.my_bookings(limit=10, offset=0)["items"]
                    first_title = "ההזמנות הקרובות שלי"
                elif self.role == "instructor":
                    first = self.service.list_bookings({"limit": 10, "from_date": datetime.now(UTC).isoformat()})["items"]
                    invalidate = getattr(self.service, "invalidate_open_events", None)
                    if callable(invalidate):
                        invalidate()
                    second = self.service.open_events()
                    first_title, second_title = "אירועים משויכים", "אירועים פתוחים"
                else:
                    first = self.service.list_bookings({"limit": 10, "from_date": datetime.now(UTC).isoformat()})["items"]
                    invalidate = getattr(self.service, "invalidate_open_events", None)
                    if callable(invalidate):
                        invalidate()
                    second = self.service.open_events()
                    first_title, second_title = "הזמנות קרובות", "דורשים שיבוץ"
            except Exception:
                errors.append("לא ניתן לטעון את רשימות לוח הבקרה.")
            return summary, first_title, first, second_title, second, errors

        def succeeded(result) -> None:
            if not self._operations.is_current(context):
                return
            summary, first_title, first, second_title, second, errors = result
            if summary:
                self.view.show_summary(summary)
            self.view.show_sections(first_title, [booking_row(item) for item in first], second_title, [booking_row(item) for item in second])
            self._has_rendered = True
            if errors:
                self.view.show_error(" | ".join(errors))

        def failed(_exc: Exception) -> None:
            if self._operations.is_current(context):
                self.view.show_error("לא ניתן לטעון את לוח הבקרה. נסו שוב.")

        def finished() -> None:
            if self._operations.finish(context):
                self.view.set_loading(False)

        self._operations.executor.submit(context, operation, succeeded, failed, finished)
