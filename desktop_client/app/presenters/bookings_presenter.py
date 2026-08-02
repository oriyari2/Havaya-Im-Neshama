from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Protocol

from desktop_client.app.api.client import ApiError
from desktop_client.app.models.operation import OperationExecutor, PresenterOperations
from desktop_client.app.presenters.formatting import booking_details, booking_row, history_rows


class BookingsViewPort(Protocol):
    def set_loading(self, loading: bool) -> None: ...
    def show_error(self, message: str) -> None: ...
    def show_bookings(self, rows, **page) -> None: ...
    def show_filter_options(self, customers, activities, instructors) -> None: ...
    def show_details(self, details, history) -> None: ...
    def show_success(self, message: str) -> None: ...
    def collect_create_booking(self, customers, activities, instructors, **kwargs): ...
    def collect_booking_changes(self, booking): ...
    def confirm_cancellation(self) -> bool: ...
    def confirm_completion(self) -> bool: ...
    def set_command_availability(self, status: str) -> None: ...


class BookingServicePort(Protocol):
    def list_bookings(self, filters=None) -> dict: ...
    def my_bookings(self, *, limit=50, offset=0, order_by="event_at") -> dict: ...
    def booking(self, booking_id: str) -> dict: ...
    def history(self, booking_id: str) -> list[dict]: ...
    def booking_form_options(self): ...
    def create_booking(self, payload): ...
    def change_status(self, booking_id, status, expected_version): ...
    def change_schedule(self, booking_id, event_at, expected_version): ...
    def change_price(self, booking_id, agreed_price, expected_version): ...
    def change_location(self, booking_id, city, venue, expected_version): ...
    def change_participant_count(self, booking_id, participant_count, expected_version): ...
    def update_notes(self, booking_id, notes, expected_version): ...


class FormValidationError(ValueError):
    pass


def _required(value: object, label: str) -> str:
    cleaned = str(value or "").strip()
    if not cleaned:
        raise FormValidationError(f"יש להזין {label}.")
    return cleaned


def validate_create_booking(values: dict[str, object], *, require_customer: bool = True) -> dict[str, object]:
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
    result = {
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
    if require_customer:
        result["customer_id"] = _required(values.get("customer_id"), "לקוח")
    return result


class BookingsPresenter:
    def __init__(self, view, service, role, on_changed=lambda: None, customer_service=None, activity_service=None, instructor_service=None, executor: OperationExecutor | None = None):
        self.view, self.service, self.role, self.on_changed = view, service, role, on_changed
        self.customer_service, self.activity_service, self.instructor_service = customer_service, activity_service, instructor_service
        self.current_booking = None
        self._submitting = False
        self._loading = False
        self.filters = {"limit": 25, "offset": 0}
        self.selected_id = None
        self._filter_options_loaded = False
        self._operations = PresenterOperations(executor, "bookings")
        self._last_list_render = None
        self._create_activity_id = None
        self.assign_after_creation = lambda _booking, _instructor_id: None

    def invalidate_requests(self):
        self._operations.invalidate()
        self._loading = False
        self.view.set_loading(False)

    def _normalize_filters(self, filters):
        if filters is None:
            return True
        cleaned = {key: value for key, value in filters.items() if value not in (None, "", [])}
        for key in ("status", "customer_id", "activity_id", "instructor_id", "assignment_state", "from_date", "to_date"):
            if key in filters and filters[key] in (None, "", []):
                self.filters.pop(key, None)
        for key, suffix in (("from_date", "T00:00:00+00:00"), ("to_date", "T23:59:59.999999+00:00")):
            if isinstance(cleaned.get(key), str) and len(cleaned[key]) == 10:
                cleaned[key] += suffix
        if cleaned.get("from_date") and cleaned.get("to_date"):
            try:
                start = datetime.fromisoformat(str(cleaned["from_date"]).replace("Z", "+00:00"))
                end = datetime.fromisoformat(str(cleaned["to_date"]).replace("Z", "+00:00"))
            except ValueError:
                self.view.show_error("טווח התאריכים אינו תקין. יש להשתמש בפורמט YYYY-MM-DD.")
                return False
            if start > end:
                self.view.show_error("תאריך ההתחלה חייב להיות מוקדם מתאריך הסיום או שווה לו.")
                return False
        self.filters = {**self.filters, **cleaned}
        if "offset" not in cleaned:
            self.filters["offset"] = 0
        return True

    def load(self, filters=None):
        if filters and filters.get("queue") == "unassigned":
            self.load_queue("unassigned")
            return
        if not self._normalize_filters(filters):
            return
        context = self._operations.replace("list")
        snapshot = dict(self.filters)
        if filters is not None:
            invalidate = getattr(self.service, "invalidate_list", None)
            if invalidate is not None and self.role != "customer":
                invalidate(snapshot)
        self._loading = True
        if self._last_list_render is None:
            self.view.set_loading(True)

        def operation():
            options = None
            if self.role == "manager" and not self._filter_options_loaded and all((self.customer_service, self.activity_service, self.instructor_service)):
                options = (
                    self.customer_service.list_customers({"is_active": True, "order_by": "name", "limit": 100, "offset": 0})["items"],
                    self.activity_service.list_activities({"is_active": True, "order_by": "name", "limit": 100, "offset": 0})["items"],
                    self.instructor_service.list_instructors({"is_active": True, "order_by": "full_name", "limit": 100, "offset": 0})["items"],
                )
            limit, offset = int(snapshot.get("limit", 25)), max(0, int(snapshot.get("offset", 0)))
            api_snapshot = {key: value for key, value in snapshot.items() if key in {"status", "customer_id", "activity_id", "instructor_id", "assignment_state", "from_date", "to_date", "order_by", "limit", "offset"}}
            if self.role == "customer":
                scoped = {key: value for key, value in snapshot.items() if key in {"status", "activity_id", "assignment_state", "from_date", "to_date", "order_by", "limit", "offset"}}
                payload = self.service.list_bookings(scoped) if any(key in scoped for key in {"status", "activity_id", "from_date", "to_date"}) else self.service.my_bookings(limit=limit, offset=offset, order_by=str(snapshot.get("order_by") or "event_at"))
            else:
                scoped = dict(api_snapshot)
                if self.role == "instructor":
                    scoped.setdefault("from_date", datetime.now(UTC).isoformat())
                payload = self.service.list_bookings(scoped)
            summary = self.service.dashboard() if self.role == "manager" else None
            return payload, options, limit, offset, summary

        def success(result):
            if not self._operations.is_current(context):
                return
            payload, options, limit, offset, summary = result
            if options is not None:
                self.view.show_filter_options(*options)
                self._filter_options_loaded = True
            items = payload["items"]
            query = str(snapshot.get("search") or "").strip().casefold()
            if query:
                items = [item for item in items if query in " ".join(str(item.get(key) or "") for key in ("id", "customer_name", "activity_name", "city", "venue")).casefold()]
            if summary is not None: self.view.show_summary(summary)
            ids = {str(item["id"]) for item in items}
            if self.selected_id not in ids:
                self.selected_id = self.current_booking = None
            signature = (snapshot, items, self.selected_id)
            if signature != self._last_list_render:
                self.view.show_bookings([booking_row(item) for item in items], offset=offset, count=len(items), limit=limit, selected_id=self.selected_id)
                self._last_list_render = signature

        def failure(_exc):
            if self._operations.is_current(context):
                self.view.show_error("לא ניתן לטעון את ההזמנות. נסו שוב.")

        def finished():
            if self._operations.finish(context):
                self._loading = False
                self.view.set_loading(False)

        self._operations.executor.submit(context, operation, success, failure, finished)

    def _load_filter_options(self):
        if not all((self.customer_service, self.activity_service, self.instructor_service)):
            return
        customers = self.customer_service.list_customers({"is_active": True, "order_by": "name", "limit": 100, "offset": 0})["items"]
        activities = self.activity_service.list_activities({"is_active": True, "order_by": "name", "limit": 100, "offset": 0})["items"]
        instructors = self.instructor_service.list_instructors({"is_active": True, "order_by": "full_name", "limit": 100, "offset": 0})["items"]
        self.view.show_filter_options(customers, activities, instructors)
        self._filter_options_loaded = True

    def page(self, offset, limit):
        self.load({**self.filters, "offset": max(0, offset), "limit": limit})

    def reset_to_default(self):
        self.filters={"limit":25,"offset":0};self.selected_id=self.current_booking=None;self._last_list_render=None;self.view.reset_to_default()

    def load_queue(self, queue):
        if queue == "pending": self.load({"status":"NEW","from_date":datetime.now(UTC).isoformat(),"limit":25,"offset":0}); return
        if queue == "approved": self.load({"status":"CONFIRMED","from_date":datetime.now(UTC).isoformat(),"limit":25,"offset":0}); return
        if queue in {"unassigned","attention"}:
            context=self._operations.replace("list");self.view.set_loading(True)
            def success(items):
                if self._operations.is_current(context):self.filters={"queue":"unassigned","limit":25,"offset":0};self.view.show_bookings([booking_row(item) for item in items],offset=0,count=len(items),limit=25,selected_id=None)
            self._operations.executor.submit(context,self.service.open_events,success,lambda _exc:self.view.show_error("לא ניתן לטעון הזמנות הממתינות לשיבוץ."),lambda:self.view.set_loading(False))

    def select_booking(self, booking_id):
        self.selected_id = booking_id
        context = self._operations.replace("detail")
        self.view.set_loading(True)

        def operation():
            return self.service.booking(booking_id), self.service.history(booking_id) if self.role == "manager" else []

        def success(result):
            if not self._operations.is_current(context) or self.selected_id != booking_id:
                return
            booking, history = result
            self.current_booking = booking
            if self.role == "manager":
                self.view.set_command_availability(str(booking.get("status", "")))
            self.view.show_details(booking_details(booking), history_rows(history))

        def failure(_exc):
            if self._operations.is_current(context):
                self.view.show_error("לא ניתן לטעון את פרטי ההזמנה. נסו שוב.")

        def finished():
            if self._operations.finish(context):
                self.view.set_loading(False)

        self._operations.executor.submit(context, operation, success, failure, finished)

    def begin_create(self, activity_id=None):
        if self.role not in {"manager", "customer"} or self._submitting:
            return
        self._create_activity_id = str(activity_id) if activity_id else None
        context = self._operations.begin("form_options")
        if context is None:
            return
        self.view.set_loading(True)

        def success(options):
            if not self._operations.is_current(context):
                return
            values = self.view.collect_create_booking(*options, role=self.role, preselected_activity_id=self._create_activity_id)
            if values is not None:
                self.create(values)

        def failure(exc):
            if self._operations.is_current(context):
                self.view.show_error(self._command_error(exc))

        def finished():
            if self._operations.finish(context):
                self.view.set_loading(False)

        def load_options():
            customers, activities = self.service.booking_form_options(include_customers=self.role == "manager")
            instructors = self.instructor_service.list_instructors({"is_active": True, "order_by": "full_name", "limit": 50, "offset": 0})["items"] if self.role == "manager" and self.instructor_service else []
            return customers, activities, instructors

        self._operations.executor.submit(context, load_options, success, failure, finished)

    def create(self, values):
        if self.role not in {"manager", "customer"} or self._submitting:
            return
        if self.role == "customer":
            values = {**values, "agreed_price": "0", "status": "NEW", "requires_instructor": False}
        instructor_id = values.pop("instructor_id", None)
        if instructor_id and self.role == "manager":
            values = {**values, "requires_instructor": True}
        try:
            payload = validate_create_booking(values, require_customer=self.role == "manager")
        except FormValidationError as exc:
            self.view.show_error(str(exc))
            return
        self._run_command(
            lambda: self.service.create_booking(payload),
            "ההזמנה נוצרה בהצלחה.",
            after_success=(lambda booking: self.assign_after_creation(booking, str(instructor_id))) if instructor_id and self.role == "manager" else None,
        )

    def confirm_after_assignment(self, booking):
        self.current_booking = booking
        self.confirm()

    def confirm(self):
        booking = self.current_booking
        if self.role != "manager" or not booking:
            return
        if booking.get("status") != "NEW":
            self.view.show_error("ניתן לאשר רק הזמנה חדשה.")
            return
        self._run_command(lambda: self.service.change_status(str(booking["id"]), "CONFIRMED", int(booking["version"])), "ההזמנה אושרה בהצלחה.")

    def cancel(self):
        booking = self.current_booking
        if self.role != "manager" or not booking or not self.view.confirm_cancellation():
            return
        if booking.get("status") in {"COMPLETED", "CANCELLED"}:
            self.view.show_error("לא ניתן לבטל הזמנה שהושלמה או כבר בוטלה.")
            return
        self._run_command(lambda: self.service.change_status(str(booking["id"]), "CANCELLED", int(booking["version"])), "ההזמנה בוטלה.")

    def complete(self):
        booking = self.current_booking
        if self.role != "manager" or not booking:
            return
        if booking.get("status") not in {"NEW", "CONFIRMED"}:
            self.view.show_error("ניתן להשלים רק הזמנה חדשה או מאושרת.")
            return
        if self.view.confirm_completion():
            self._run_command(lambda: self.service.change_status(str(booking["id"]), "COMPLETED", int(booking["version"])), "ההזמנה סומנה כהושלמה.")

    def begin_edit(self):
        if self.role == "manager" and self.current_booking and not self._submitting:
            values = self.view.collect_booking_changes(self.current_booking)
            if values is not None:
                self.update(values)

    def update(self, values):
        booking = self.current_booking
        if self.role != "manager" or not booking or self._submitting:
            return
        try:
            normalized = validate_create_booking({**booking, **values})
        except FormValidationError as exc:
            self.view.show_error(str(exc))
            return

        def command():
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
                different = (normalized["city"], normalized["venue"]) != (booking.get("city"), booking.get("venue")) if field == "location" else str(normalized[field] if normalized[field] is not None else "") != str(booking.get(field) if booking.get(field) is not None else "")
                if different:
                    current = operation(int(current["version"]))
                    changed = True
            if not changed:
                raise FormValidationError("לא נמצאו שינויים לשמירה.")
            return current

        self._run_command(command, "פרטי ההזמנה עודכנו.")

    def _run_command(self, command, success_message, after_success=None):
        if self._submitting:
            return
        context = self._operations.begin("mutation")
        if context is None:
            return
        self._submitting = True
        self.view.set_loading(True)
        booking_id = str(self.current_booking["id"]) if self.current_booking else None

        def success(result):
            if not self._operations.is_current(context):
                return
            self.current_booking = result
            selected = booking_id or str(result["id"])
            self.load(dict(self.filters))
            self.select_booking(selected)
            self.on_changed()
            self.view.show_success(success_message)
            if after_success is not None:
                after_success(result)

        def failure(exc):
            if not self._operations.is_current(context):
                return
            self.view.show_error(self._command_error(exc))
            if booking_id and isinstance(exc, ApiError) and exc.status_code == 409:
                self.select_booking(booking_id)

        def finished():
            if self._operations.finish(context):
                self._submitting = False
                self.view.set_loading(False)

        self._operations.executor.submit(context, command, success, failure, finished)

    @staticmethod
    def _command_error(exc):
        if isinstance(exc, ApiError):
            if exc.status_code in {400, 422}:
                return f"הנתונים לא נשמרו: {exc}"
            if exc.status_code in {401, 403}:
                return "אין הרשאה לבצע פעולה זו."
            if exc.status_code == 409:
                return "ההזמנה השתנתה בינתיים. הנתונים רועננו; נסו שוב."
        if isinstance(exc, FormValidationError):
            return str(exc)
        return str(exc)
