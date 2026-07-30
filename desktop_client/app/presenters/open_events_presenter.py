from __future__ import annotations

from typing import Protocol

from desktop_client.app.models.operation import OperationExecutor, PresenterOperations
from desktop_client.app.presenters.formatting import booking_row


class OpenEventsViewPort(Protocol):
    def set_loading(self, loading: bool) -> None: ...
    def show_error(self, message: str) -> None: ...
    def show_events(self, rows: list[dict[str, str]]) -> None: ...


class OpenEventsServicePort(Protocol):
    def open_events(self) -> list[dict]: ...
    def open_event_detail(self, booking_id: str) -> dict: ...


class OpenEventsPresenter:
    def __init__(self, view: OpenEventsViewPort, service: OpenEventsServicePort, executor: OperationExecutor | None = None) -> None:
        self.view, self.service = view, service
        self.items: list[dict] = []
        self.query = ""
        self._operations = PresenterOperations(executor, "open_events")
        self._last_render = None

    def invalidate_requests(self) -> None:
        self._operations.invalidate()
        self.view.set_loading(False)

    def load(self) -> None:
        context = self._operations.replace("list")
        if self._last_render is None:
            self.view.set_loading(True)

        def success(items):
            if self._operations.is_current(context):
                self.items = items
                self.apply_filter(self.query)

        def failure(exc):
            if self._operations.is_current(context):
                self.view.show_error(str(exc))

        def finished():
            if self._operations.finish(context):
                self.view.set_loading(False)

        self._operations.executor.submit(context, self.service.open_events, success, failure, finished)

    def retry(self) -> None:
        invalidate = getattr(self.service, "invalidate_open_events", None)
        if invalidate is not None:
            invalidate()
        self.load()

    def apply_filter(self, query: str) -> None:
        self.query = query.strip().casefold()
        items = self.items
        if self.query:
            items = [item for item in items if self.query in " ".join(str(item.get(key) or "") for key in ("activity_name", "city", "venue", "status")).casefold()]
        signature = (self.query, items)
        if signature != self._last_render:
            self.view.show_events([booking_row(item) for item in items])
            self._last_render = signature

    def select(self, booking_id: str) -> None:
        context = self._operations.replace("detail")
        self.view.set_loading(True)

        def success(item):
            if not self._operations.is_current(context):
                return
            activities = ", ".join(value["activity_name"] + (" — נדרש שיוך" if value["assignment_required"] else "") for value in item["activities"])
            self.view.show_details([("מועד", str(item["event_at"])), ("עיר", item.get("city") or "—"), ("מקום", item.get("venue") or "—"), ("סטטוס", item["status"]), ("פעילויות", activities or "—")])

        def failure(exc):
            if self._operations.is_current(context):
                self.view.show_error(str(exc))

        def finished():
            if self._operations.finish(context):
                self.view.set_loading(False)

        self._operations.executor.submit(context, lambda: self.service.open_event_detail(booking_id), success, failure, finished)
