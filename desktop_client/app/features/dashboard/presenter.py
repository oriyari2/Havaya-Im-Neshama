from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from desktop_client.app.api.client import ApiError, ApiErrorKind
from desktop_client.app.models.operation import OperationExecutor, PresenterOperations


class DashboardViewPort(Protocol):
    def set_loading(self, loading: bool) -> None: ...
    def show_error(self, message: str) -> None: ...
    def show_summary(self, summary: dict[str, int]) -> None: ...
    def set_chart_loading(self, loading: bool) -> None: ...
    def show_chart(self, year: int, years: list[int], months: list[dict[str, int]]) -> None: ...
    def show_chart_error(self, message: str) -> None: ...


class DashboardServicePort(Protocol):
    def dashboard(self) -> dict: ...
    def yearly_event_trend(self, year: int) -> dict: ...


class DashboardPresenter:
    def __init__(self, view: DashboardViewPort, service: DashboardServicePort, role: str, navigate=lambda _key, _filters=None: None, create_booking=lambda: None, executor: OperationExecutor | None = None) -> None:
        self.view = view
        self.service = service
        self.role = role
        self.navigate = navigate
        self.create_booking = create_booking
        self._operations = PresenterOperations(executor, "dashboard")
        self._has_rendered = False
        self._selected_year = datetime.now(UTC).year

    def invalidate_requests(self) -> None:
        self._operations.invalidate()
        self.view.set_loading(False)

    def drill_down(self, target: str) -> None:
        status_filters = {"pending_count": "NEW", "confirmed_count": "CONFIRMED", "cancelled_count": "CANCELLED"}
        if target in status_filters:
            # Dashboard status counters are defined only over upcoming bookings.
            # Carry the same time boundary into the destination list so opening
            # a card cannot show historical rows that were not included in the
            # number displayed on the card.
            self.navigate(
                "my_bookings" if self.role == "customer" else "bookings",
                {"status": status_filters[target], "from_date": datetime.now(UTC).isoformat()},
            )
        elif target == "unassigned_count":
            self.navigate("bookings", {"queue": "unassigned"})
        elif target in {"upcoming_count", "assigned_count"}:
            destination = "my_bookings" if self.role == "customer" else "bookings"
            filters = {"from_date": datetime.now(UTC).isoformat()}
            # The assigned dashboard card counts only bookings whose required
            # activities all have an active instructor. Carry that exact
            # predicate into the destination list for managers and instructors,
            # otherwise the card count and the opened list disagree.
            if target == "assigned_count" and self.role in {"manager", "instructor"}:
                filters["assignment_state"] = "assigned"
            self.navigate(destination, filters)
        else:
            self.navigate(target, None)


    def load(self) -> None:
        context = self._operations.replace("load")
        if not self._has_rendered:
            self.view.set_loading(True)

        def operation():
            return self.service.dashboard()

        def succeeded(summary) -> None:
            if not self._operations.is_current(context):
                return
            self.view.show_summary(summary)
            self._has_rendered = True

        def failed(_exc: Exception) -> None:
            if self._operations.is_current(context):
                self.view.show_error("לא ניתן לטעון את לוח הבקרה. נסו שוב.")

        def finished() -> None:
            if self._operations.finish(context):
                self.view.set_loading(False)

        self._operations.executor.submit(context, operation, succeeded, failed, finished)
        self.load_chart(self._selected_year)

    def load_chart(self, year: int | None = None) -> None:
        if year is not None:
            self._selected_year = int(year)
        context = self._operations.replace("chart")
        self.view.set_chart_loading(True)

        def succeeded(result: dict) -> None:
            if not self._operations.is_current(context):
                return
            self._selected_year = int(result.get("year", self._selected_year))
            self.view.show_chart(
                self._selected_year,
                [int(value) for value in result.get("available_years", [])],
                list(result.get("months", [])),
            )

        def failed(exc: Exception) -> None:
            if not self._operations.is_current(context):
                return
            if isinstance(exc, ApiError) and exc.kind == ApiErrorKind.PERMISSION:
                message = "אין הרשאה לצפות במגמת האירועים."
            elif isinstance(exc, ApiError) and exc.kind == ApiErrorKind.CONNECTION:
                message = "לא ניתן להתחבר לשרת. לחצו כדי לנסות שוב."
            else:
                message = "לא ניתן לטעון את מגמת האירועים. לחצו כדי לנסות שוב."
            self.view.show_chart_error(message)

        def finished() -> None:
            if self._operations.finish(context):
                self.view.set_chart_loading(False)

        self._operations.executor.submit(
            context,
            lambda: self.service.yearly_event_trend(self._selected_year),
            succeeded,
            failed,
            finished,
        )
