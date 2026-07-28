from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Protocol

from desktop_client.app.api.client import ApiError

from desktop_client.app.presenters.formatting import booking_details, booking_row, history_rows


class BookingsViewPort(Protocol):
    def set_loading(self, loading: bool) -> None: ...
    def show_error(self, message: str) -> None: ...
    def show_bookings(self, rows: list[dict[str, str]], *, offset: int = 0, count: int = 0, limit: int = 25, selected_id: str | None = None) -> None: ...
    def show_filter_options(self, customers: list[dict], activities: list[dict], instructors: list[dict]) -> None: ...
    def show_details(self, details: list[tuple[str, str]], history: list[dict[str, str]]) -> None: ...
    def show_success(self, message: str) -> None: ...
    def collect_create_booking(self, customers: list[dict], activities: list[dict]) -> dict[str, object] | None: ...
    def collect_booking_changes(self, booking: dict) -> dict[str, object] | None: ...
    def confirm_cancellation(self) -> bool: ...
    def confirm_completion(self) -> bool: ...
    def set_command_availability(self, status: str) -> None: ...


class BookingServicePort(Protocol):
    def list_bookings(self, filters: dict[str, object] | None = None) -> dict: ...
    def my_bookings(self, *, limit: int = 50, offset: int = 0) -> dict: ...
    def booking(self, booking_id: str) -> dict: ...
    def history(self, booking_id: str) -> list[dict]: ...
    def booking_form_options(self) -> tuple[list[dict], list[dict]]: ...
    def create_booking(self, payload: dict[str, object]) -> dict: ...
    def change_status(self, booking_id: str, status: str, expected_version: int) -> dict: ...
    def change_schedule(self, booking_id: str, event_at: str, expected_version: int) -> dict: ...
    def change_price(self, booking_id: str, agreed_price: str, expected_version: int) -> dict: ...
    def change_location(self, booking_id: str, city: str | None, venue: str | None, expected_version: int) -> dict: ...
    def change_participant_count(self, booking_id: str, participant_count: int, expected_version: int) -> dict: ...
    def update_notes(self, booking_id: str, notes: str | None, expected_version: int) -> dict: ...


class FormValidationError(ValueError):
    pass


def _required(value: object, label: str) -> str:
    cleaned = str(value or "").strip()
    if not cleaned:
        raise FormValidationError(f"יש להזין {label}.")
    return cleaned


def validate_create_booking(values: dict[str, object]) -> dict[str, object]:
    event_at = _required(values.get("event_at"), "מועד אירוע")
    try:
        datetime.fromisoformat(event_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise FormValidationError("מועד האירוע אינו תקין.") from exc
    try:
        participant_count = int(str(values.get("participant_count", "")))
    except ValueError as exc:
        raise FormValidationError("מספר המשתתפים חייב להיות מספר שלם.") from exc
    if participant_count <= 0:
        raise FormValidationError("מספר המשתתפים חייב להיות חיובי.")
    try:
        agreed_price = Decimal(str(values.get("agreed_price", "")))
    except InvalidOperation as exc:
        raise FormValidationError("המחיר המוסכם אינו תקין.") from exc
    if agreed_price < 0:
        raise FormValidationError("המחיר המוסכם אינו יכול להיות שלילי.")
    return {
        "customer_id": _required(values.get("customer_id"), "לקוח"),
        "activity_id": _required(values.get("activity_id"), "פעילות"),
        "event_at": event_at,
        "city": str(values.get("city") or "").strip() or None,
        "venue": str(values.get("venue") or "").strip() or None,
        "participant_count": participant_count,
        "agreed_price": str(agreed_price),
        "status": str(values.get("status") or "NEW"),
        "requires_instructor": bool(values.get("requires_instructor")),
        "notes": str(values.get("notes") or "").strip() or None,
    }


class BookingsPresenter:
    def __init__(
        self,
        view: BookingsViewPort,
        service: BookingServicePort,
        role: str,
        on_changed=lambda: None,
        customer_service=None,
        activity_service=None,
        instructor_service=None,
    ) -> None:
        self.view = view
        self.service = service
        self.role = role
        self.on_changed = on_changed
        self.customer_service = customer_service
        self.activity_service = activity_service
        self.instructor_service = instructor_service
        self.current_booking: dict | None = None
        self._submitting = False
        self._loading = False
        self.filters: dict[str, object] = {"limit": 25, "offset": 0}
        self.selected_id: str | None = None
        self._filter_options_loaded = False

    def load(self, filters: dict[str, object] | None = None) -> None:
        if self._loading:
            return
        if filters is not None:
            cleaned = {key: value for key, value in filters.items() if value not in (None, "")}
            for key in ("status", "customer_id", "activity_id", "instructor_id", "from_date", "to_date"):
                if key in filters and filters[key] in (None, ""):
                    self.filters.pop(key, None)
            if isinstance(cleaned.get("from_date"), str) and len(str(cleaned["from_date"])) == 10:
                cleaned["from_date"] = f"{cleaned['from_date']}T00:00:00+00:00"
            if isinstance(cleaned.get("to_date"), str) and len(str(cleaned["to_date"])) == 10:
                cleaned["to_date"] = f"{cleaned['to_date']}T23:59:59.999999+00:00"
            if cleaned.get("from_date") and cleaned.get("to_date"):
                try:
                    start = datetime.fromisoformat(str(cleaned["from_date"]).replace("Z", "+00:00"))
                    end = datetime.fromisoformat(str(cleaned["to_date"]).replace("Z", "+00:00"))
                except ValueError:
                    self.view.show_error("טווח התאריכים אינו תקין. יש להשתמש בתאריך בפורמט YYYY-MM-DD.")
                    return
                if start > end:
                    self.view.show_error("תאריך ההתחלה חייב להיות מוקדם מתאריך הסיום או שווה לו.")
                    return
            self.filters = {**self.filters, **cleaned}
            if "offset" not in cleaned:
                self.filters["offset"] = 0
        self._loading = True
        self.view.set_loading(True)
        try:
            if self.role == "manager" and not self._filter_options_loaded:
                self._load_filter_options()
            limit = int(self.filters.get("limit", 25))
            offset = max(0, int(self.filters.get("offset", 0)))
            if self.role == "customer":
                role_filters = {key: value for key, value in self.filters.items() if key in {"status", "activity_id", "from_date", "to_date", "limit", "offset"}}
                payload = self.service.list_bookings(role_filters) if any(key in role_filters for key in {"status", "activity_id", "from_date", "to_date"}) else self.service.my_bookings(limit=limit, offset=offset)
            else:
                effective_filters = dict(self.filters)
                if self.role == "instructor":
                    effective_filters.setdefault("from_date", datetime.now(UTC).isoformat())
                payload = self.service.list_bookings(effective_filters)
            ids = {str(item["id"]) for item in payload["items"]}
            if self.selected_id not in ids:
                self.selected_id = None
                self.current_booking = None
            self.view.show_bookings(
                [booking_row(item) for item in payload["items"]],
                offset=offset, count=len(payload["items"]), limit=limit, selected_id=self.selected_id,
            )
        except Exception as exc:
            self.view.show_error(str(exc))
        finally:
            self._loading = False
            self.view.set_loading(False)

    def _load_filter_options(self) -> None:
        if not all((self.customer_service, self.activity_service, self.instructor_service)):
            return
        customers = self.customer_service.list_customers({"is_active": True, "order_by": "name", "limit": 100, "offset": 0})["items"]
        activities = self.activity_service.list_activities({"is_active": True, "order_by": "name", "limit": 100, "offset": 0})["items"]
        instructors = self.instructor_service.list_instructors({"is_active": True, "order_by": "full_name", "limit": 100, "offset": 0})["items"]
        self.view.show_filter_options(customers, activities, instructors)
        self._filter_options_loaded = True

    def page(self, offset: int, limit: int) -> None:
        self.load({**self.filters, "offset": max(0, offset), "limit": limit})

    def select_booking(self, booking_id: str) -> None:
        self.view.set_loading(True)
        try:
            booking = self.service.booking(booking_id)
            self.selected_id = booking_id
            self.current_booking = booking
            if self.role == "manager":
                self.view.set_command_availability(str(booking.get("status", "")))
            history = self.service.history(booking_id) if self.role == "manager" else []
            self.view.show_details(booking_details(booking), history_rows(history))
        except Exception as exc:
            self.view.show_error(str(exc))
        finally:
            self.view.set_loading(False)

    def begin_create(self) -> None:
        if self.role != "manager" or self._submitting:
            return
        self.view.set_loading(True)
        try:
            customers, activities = self.service.booking_form_options()
            values = self.view.collect_create_booking(customers, activities)
            if values is not None:
                self.create(values)
        except Exception as exc:
            self.view.show_error(self._command_error(exc))
        finally:
            self.view.set_loading(False)

    def create(self, values: dict[str, object]) -> None:
        if self.role != "manager" or self._submitting:
            return
        try:
            payload = validate_create_booking(values)
        except FormValidationError as exc:
            self.view.show_error(str(exc))
            return
        self._run_command(lambda: self.service.create_booking(payload), "ההזמנה נוצרה בהצלחה.")

    def confirm(self) -> None:
        booking = self.current_booking
        if self.role != "manager" or not booking:
            return
        if booking.get("status") != "NEW":
            self.view.show_error("ניתן לאשר רק הזמנה חדשה.")
            return
        self._run_command(
            lambda: self.service.change_status(str(booking["id"]), "CONFIRMED", int(booking["version"])),
            "ההזמנה אושרה בהצלחה.",
        )

    def cancel(self) -> None:
        booking = self.current_booking
        if self.role != "manager" or not booking or not self.view.confirm_cancellation():
            return
        if booking.get("status") in {"COMPLETED", "CANCELLED"}:
            self.view.show_error("לא ניתן לבטל הזמנה שהושלמה או כבר בוטלה.")
            return
        self._run_command(
            lambda: self.service.change_status(str(booking["id"]), "CANCELLED", int(booking["version"])),
            "ההזמנה בוטלה.",
        )

    def complete(self) -> None:
        booking = self.current_booking
        if self.role != "manager" or not booking:
            return
        if booking.get("status") not in {"NEW", "CONFIRMED"}:
            self.view.show_error("ניתן להשלים רק הזמנה חדשה או מאושרת.")
            return
        if not self.view.confirm_completion():
            return
        self._run_command(
            lambda: self.service.change_status(str(booking["id"]), "COMPLETED", int(booking["version"])),
            "ההזמנה סומנה כהושלמה.",
        )

    def begin_edit(self) -> None:
        booking = self.current_booking
        if self.role != "manager" or not booking or self._submitting:
            return
        values = self.view.collect_booking_changes(booking)
        if values is not None:
            self.update(values)

    def update(self, values: dict[str, object]) -> None:
        booking = self.current_booking
        if self.role != "manager" or not booking or self._submitting:
            return
        try:
            normalized = validate_create_booking({**booking, **values})
        except FormValidationError as exc:
            self.view.show_error(str(exc))
            return

        def command() -> dict:
            current = booking
            booking_id = str(booking["id"])
            operations = (
                ("event_at", lambda version: self.service.change_schedule(booking_id, str(normalized["event_at"]), version)),
                ("agreed_price", lambda version: self.service.change_price(booking_id, str(normalized["agreed_price"]), version)),
                ("location", lambda version: self.service.change_location(booking_id, normalized["city"], normalized["venue"], version)),
                ("participant_count", lambda version: self.service.change_participant_count(booking_id, int(normalized["participant_count"]), version)),
                ("notes", lambda version: self.service.update_notes(booking_id, normalized["notes"], version)),
            )
            changed = False
            for field, operation in operations:
                different = (
                    (normalized["city"], normalized["venue"]) != (booking.get("city"), booking.get("venue"))
                    if field == "location"
                    else str(normalized[field] if normalized[field] is not None else "")
                    != str(booking.get(field) if booking.get(field) is not None else "")
                )
                if different:
                    current = operation(int(current["version"]))
                    changed = True
            if not changed:
                raise FormValidationError("לא נמצאו שינויים לשמירה.")
            return current

        self._run_command(command, "פרטי ההזמנה עודכנו.")

    def _run_command(self, command, success_message: str) -> None:
        if self._submitting:
            return
        self._submitting = True
        self.view.set_loading(True)
        booking_id = str(self.current_booking["id"]) if self.current_booking else None
        try:
            result = command()
            self.current_booking = result
            self.load(dict(self.filters))
            if booking_id or result.get("id"):
                self.select_booking(booking_id or str(result["id"]))
            self.on_changed()
            self.view.show_success(success_message)
        except Exception as exc:
            self.view.show_error(self._command_error(exc))
            if booking_id:
                self.select_booking(booking_id)
        finally:
            self._submitting = False
            self.view.set_loading(False)

    @staticmethod
    def _command_error(exc: Exception) -> str:
        if isinstance(exc, ApiError):
            if exc.status_code in {400, 422}:
                return f"הנתונים לא נשמרו: {exc}"
            if exc.status_code in {401, 403}:
                return "אין הרשאה לבצע פעולה זו."
            if exc.status_code == 409:
                return "ההזמנה השתנתה בינתיים. הנתונים רועננו; נסו שוב."
        return str(exc)
