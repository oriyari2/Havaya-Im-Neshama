from __future__ import annotations

from typing import Protocol

from desktop_client.app.presenters.formatting import booking_row


class OpenEventsViewPort(Protocol):
    def set_loading(self, loading: bool) -> None: ...
    def show_error(self, message: str) -> None: ...
    def show_events(self, rows: list[dict[str, str]]) -> None: ...


class OpenEventsServicePort(Protocol):
    def open_events(self) -> list[dict]: ...
    def open_event_detail(self, booking_id: str) -> dict: ...


class OpenEventsPresenter:
    def __init__(self, view: OpenEventsViewPort, service: OpenEventsServicePort) -> None:
        self.view = view
        self.service = service
        self.items: list[dict] = []
        self.query = ""

    def load(self) -> None:
        self.view.set_loading(True)
        try:
            self.items = self.service.open_events()
            self.apply_filter(self.query)
        except Exception as exc:
            self.view.show_error(str(exc))
        finally:
            self.view.set_loading(False)

    def apply_filter(self, query: str) -> None:
        self.query = query.strip().casefold()
        items = self.items
        if self.query:
            items = [item for item in items if self.query in " ".join(str(item.get(key) or "") for key in ("activity_name", "city", "venue", "status")).casefold()]
        self.view.show_events([booking_row(item) for item in items])

    def select(self,booking_id:str)->None:
        self.view.set_loading(True)
        try:
            item=self.service.open_event_detail(booking_id);activities=", ".join(x["activity_name"]+(" — נדרש שיוך" if x["assignment_required"] else "") for x in item["activities"]);self.view.show_details([("מועד",str(item["event_at"])),("עיר",item.get("city") or "—"),("מקום",item.get("venue") or "—"),("סטטוס",item["status"]),("פעילויות",activities or "—")])
        except Exception as exc:self.view.show_error(str(exc))
        finally:self.view.set_loading(False)
