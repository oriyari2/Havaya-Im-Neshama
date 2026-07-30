from __future__ import annotations

import re
from typing import Callable, Protocol

from desktop_client.app.api.client import ApiError, ApiErrorKind
from desktop_client.app.models.request_state import RequestIdentity, RequestPhase, RequestState
from desktop_client.app.models.operation import ImmediateOperationExecutor, OperationExecutor, PresenterOperations
from desktop_client.app.presenters.customer_formatting import contact_row, customer_details, customer_row


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class FormPort(Protocol):
    def set_submitting(self, submitting: bool) -> None: ...
    def show_error(self, message: str) -> None: ...
    def close_success(self) -> None: ...


class CustomersViewPort(Protocol):
    def set_loading(self, loading: bool) -> None: ...
    def set_detail_loading(self, loading: bool) -> None: ...
    def render_request_state(self, state: RequestState) -> None: ...
    def show_error(self, message: str, *, retriable: bool = False, permission: bool = False) -> None: ...
    def show_success(self, message: str) -> None: ...
    def show_customers(self, rows: list[dict], *, offset: int, count: int, filtered: bool) -> None: ...
    def show_details(self, details: list[tuple[str, str]], customer: dict, contacts: list[dict]) -> None: ...
    def clear_details(self) -> None: ...
    def select_customer(self, customer_id: str) -> None: ...
    def open_customer_form(self, initial: dict | None, submit: Callable) -> None: ...
    def confirm_customer_deletion(self, name: str) -> bool: ...


class CustomerServicePort(Protocol):
    def list_customers(self, filters: dict[str, object]) -> dict: ...
    def customer(self, customer_id: str) -> dict: ...
    def create_customer(self, payload: dict[str, object]) -> dict: ...
    def update_customer(self, customer_id: str, payload: dict[str, object]) -> dict: ...
    def delete_customer(self, customer_id: str) -> None: ...
    def create_contact(self, customer_id: str, payload: dict[str, object]) -> dict: ...
    def update_contact(self, contact_id: str, payload: dict[str, object]) -> dict: ...


def validate_customer(values: dict[str, object]) -> dict[str, object]:
    name = str(values.get("name") or "").strip()
    if not name:
        raise ValueError("יש להזין שם לקוח.")
    email = str(values.get("email") or "").strip() or None
    if email and not EMAIL_PATTERN.match(email):
        raise ValueError("כתובת הדוא״ל אינה תקינה.")
    contact_name = str(values.get("contact_name") or "").strip()
    if not contact_name:
        raise ValueError("יש להזין שם איש קשר.")
    contact_phone = str(values.get("contact_phone") or "").strip()
    if not contact_phone:
        raise ValueError("יש להזין טלפון איש קשר.")
    return {
        "name": name,
        "customer_type": str(values.get("customer_type") or "").strip() or None,
        "city": str(values.get("city") or "").strip() or None,
        "address": str(values.get("address") or "").strip() or None,
        "phone": str(values.get("phone") or "").strip() or None,
        "email": email,
        "notes": str(values.get("notes") or "").strip() or None,
        "contact_name": contact_name,
        "contact_phone": contact_phone,
    }


class CustomersPresenter:
    def __init__(self, view: CustomersViewPort, service: CustomerServicePort, *, limit: int = 25, executor: OperationExecutor | None = None) -> None:
        self.view, self.service = view, service
        self.filters: dict[str, object] = {"search": None, "city": None, "customer_type": None, "is_active": None, "order_by": "name", "limit": limit, "offset": 0}
        self.selected_id: str | None = None
        self.selected_customer: dict | None = None
        self._loading = False
        self._submitting = False
        self._generation = 0
        self._session_epoch = 0
        self._current_requests: dict[str, RequestIdentity] = {}
        self._executor = executor or ImmediateOperationExecutor()

    def _begin_request(self, operation_key: str, resource_id: str | None = None) -> RequestIdentity:
        self._generation += 1
        identity = RequestIdentity(self._session_epoch, "customers", operation_key, self._generation, resource_id)
        self._current_requests[operation_key] = identity
        return identity

    def _is_current(self, identity: RequestIdentity) -> bool:
        current = self._current_requests.get(identity.operation_key)
        return current is not None and identity.is_current(current)

    def invalidate_requests(self) -> None:
        self._session_epoch += 1
        self._current_requests.clear()
        self._loading = False
        self._submitting = False

    def _render_state(self, state: RequestState) -> None:
        self.view.render_request_state(state)

    def load(self) -> None:
        self._loading = True
        identity = self._begin_request("list")
        self._render_state(RequestState(RequestPhase.LOADING, "טוען לקוחות…", "list", blocks_primary_action=True))
        self.view.set_loading(True)
        filters = dict(self.filters)

        def succeeded(payload: dict) -> None:
            if not self._is_current(identity):
                return
            items = payload["items"]
            self.view.show_customers(
                [customer_row(item) for item in items], offset=int(filters["offset"]),
                count=len(items), filtered=any(filters[k] not in (None, "") for k in ("search", "city", "customer_type", "is_active")),
            )
            ids = {str(item["id"]) for item in items}
            if self.selected_id in ids:
                self.view.select_customer(self.selected_id)
            elif self.selected_id is not None:
                self.selected_id = self.selected_customer = None
                self.view.clear_details()
            self._render_state(RequestState(RequestPhase.EMPTY if not items else RequestPhase.IDLE, "אין לקוחות להצגה." if not items else "", "list"))
        def failed(exc: Exception) -> None:
            if self._is_current(identity):
                self._show_error(exc)

        def finished() -> None:
            if not self._is_current(identity):
                return
            self._current_requests.pop("list", None)
            self._loading = False
            self.view.set_loading(False)

        self._executor.submit(identity, lambda: self.service.list_customers(filters), succeeded, failed, finished)

    def apply_filters(self, values: dict[str, object]) -> None:
        self.filters.update(values)
        self.filters["offset"] = 0
        self.load()

    def page(self, offset: int, limit: int) -> None:
        self.filters.update(offset=max(0, offset), limit=limit)
        self.load()

    def retry(self) -> None:
        self.load()

    def select(self, customer_id: str) -> None:
        self.selected_id = customer_id
        identity = self._begin_request("detail", customer_id)
        self._render_state(RequestState(RequestPhase.LOADING, "טוען פרטי לקוח…", "detail", blocks_primary_action=True))
        self.view.set_detail_loading(True)
        def succeeded(customer: dict) -> None:
            if not self._is_current(identity) or self.selected_id != customer_id:
                return
            self.selected_customer = customer
            self.view.show_details(customer_details(customer), customer, [contact_row(x) for x in customer.get("contacts", [])])
            self._render_state(RequestState(RequestPhase.IDLE, operation_key="detail"))
        def failed(exc: Exception) -> None:
            if not self._is_current(identity):
                return
            if isinstance(exc, ApiError) and exc.kind == ApiErrorKind.NOT_FOUND:
                self.selected_id = self.selected_customer = None
                self.view.clear_details()
                self.view.show_error("הלקוח שנבחר אינו קיים עוד. הרשימה רועננה.")
                self.load()
            elif isinstance(exc, ApiError):
                self._show_error(exc)
            else:
                self._show_error(exc)

        def finished() -> None:
            if self._is_current(identity):
                self._current_requests.pop("detail", None)
                self.view.set_detail_loading(False)

        self._executor.submit(identity, lambda: self.service.customer(customer_id), succeeded, failed, finished)

    def begin_create(self) -> None:
        self.view.open_customer_form(None, self.submit_create)

    def begin_edit(self) -> None:
        if self.selected_customer:
            initial = dict(self.selected_customer)
            contact = self._current_contact(self.selected_customer)
            initial["contact_name"] = contact.get("full_name") if contact else ""
            initial["contact_phone"] = contact.get("phone") if contact else ""
            self.view.open_customer_form(initial, self.submit_edit)

    def submit_create(self, values: dict[str, object], form: FormPort) -> None:
        self._submit_customer(values, form, None)

    def submit_edit(self, values: dict[str, object], form: FormPort) -> None:
        self._submit_customer(values, form, self.selected_id)

    def _submit_customer(self, values: dict[str, object], form: FormPort, customer_id: str | None) -> None:
        if self._submitting:
            return
        try:
            payload = validate_customer(values)
        except ValueError as exc:
            form.show_error(str(exc))
            return
        self._submitting = True
        form.set_submitting(True)
        identity = self._begin_request("submit", customer_id)

        def operation():
            contact_name = str(payload.pop("contact_name"))
            contact_phone = str(payload.pop("contact_phone"))
            customer = self.service.update_customer(customer_id, payload) if customer_id else self.service.create_customer(payload)
            contact = self._current_contact(self.selected_customer) if customer_id else None
            contact_payload = {
                "full_name": contact_name,
                "role_title": None,
                "phone": contact_phone,
                "email": None,
                "is_primary": True,
                "notes": None,
                "is_active": True,
            }
            if contact:
                self.service.update_contact(str(contact["id"]), contact_payload)
            else:
                self.service.create_contact(str(customer["id"]), contact_payload)
            return customer

        def succeeded(customer: dict) -> None:
            if not self._is_current(identity):
                return
            form.close_success()
            self.selected_id = str(customer["id"])
            self.view.show_success("הלקוח נשמר בהצלחה.")
            self.load()
            self.select(self.selected_id)
        def failed(exc: Exception) -> None:
            if not self._is_current(identity):
                return
            form.show_error(self._message(exc))
            if isinstance(exc, ApiError) and exc.kind == ApiErrorKind.CONFLICT and self.selected_id:
                self.select(self.selected_id)
        def finished() -> None:
            if not self._is_current(identity):
                return
            self._current_requests.pop("submit", None)
            self._submitting = False
            form.set_submitting(False)

        self._executor.submit(identity, operation, succeeded, failed, finished)

    @staticmethod
    def _current_contact(customer: dict | None) -> dict | None:
        contacts = list((customer or {}).get("contacts", []))
        return next(
            (contact for contact in contacts if contact.get("is_primary") and contact.get("is_active")),
            next((contact for contact in contacts if contact.get("is_active")), None),
        )

    def delete(self) -> None:
        customer = self.selected_customer
        if not customer or not self.view.confirm_customer_deletion(str(customer["name"])):
            return
        if self._submitting:
            return
        customer_id = str(customer["id"])
        self._submitting = True
        self.view.set_loading(True)
        identity = self._begin_request("delete", customer_id)

        def succeeded(_result: object) -> None:
            if not self._is_current(identity):
                return
            self.selected_id = self.selected_customer = None
            self.view.clear_details()
            self.view.show_success("הלקוח נמחק בהצלחה.")
            self.load()
        def failed(exc: Exception) -> None:
            if not self._is_current(identity):
                return
            if isinstance(exc, ApiError) and exc.kind == ApiErrorKind.NOT_FOUND:
                self.selected_id = self.selected_customer = None
                self.view.clear_details()
                self.load()
            elif isinstance(exc, ApiError) and exc.kind == ApiErrorKind.CONFLICT:
                self.view.show_error("לא ניתן למחוק את הלקוח כל עוד קיימות רשומות תלויות.")
                self.select(customer_id)
            else:
                self._show_error(exc)

        def finished() -> None:
            if not self._is_current(identity):
                return
            self._current_requests.pop("delete", None)
            self._submitting = False
            self.view.set_loading(False)

        self._executor.submit(identity, lambda: self.service.delete_customer(customer_id), succeeded, failed, finished)

    def _mutate(self, operation: Callable, message: str) -> None:
        if self._submitting:
            return
        self._submitting = True
        self.view.set_loading(True)
        try:
            customer = operation()
            self.selected_id = str(customer["id"])
            self.view.show_success(message)
            self.load()
            if self.selected_id:
                self.select(self.selected_id)
        except Exception as exc:
            self._show_error(exc)
        finally:
            self._submitting = False
            self.view.set_loading(False)

    def _show_error(self, exc: Exception) -> None:
        permission = isinstance(exc, ApiError) and exc.kind == ApiErrorKind.PERMISSION
        retriable = isinstance(exc, ApiError) and exc.retriable
        message = self._message(exc)
        phase = RequestPhase.AUTHORIZATION_ERROR if permission else RequestPhase.CONNECTION_ERROR if isinstance(exc, ApiError) and exc.kind == ApiErrorKind.CONNECTION else RequestPhase.SERVER_ERROR
        self._render_state(RequestState(phase, message, "customers", retryable=retriable))
        self.view.show_error(message, retriable=retriable, permission=permission)

    @staticmethod
    def _message(exc: Exception) -> str:
        if isinstance(exc, ApiError):
            if exc.kind == ApiErrorKind.PERMISSION:
                return "אין הרשאה לצפות או לשנות לקוחות."
            if exc.kind == ApiErrorKind.CONFLICT:
                return "הלקוח השתנה במקביל. הרשומה רועננה; נסו שוב."
            if exc.kind == ApiErrorKind.VALIDATION:
                return "הנתונים שנשלחו אינם תקינים. בדקו את השדות ונסו שוב."
            if exc.kind == ApiErrorKind.NOT_FOUND:
                return "הרשומה המבוקשת אינה זמינה עוד."
            if exc.kind == ApiErrorKind.CONNECTION:
                return "לא ניתן להתחבר לשרת. נסו שוב לאחר שהחיבור יחזור."
            if exc.kind == ApiErrorKind.SERVER:
                return "השרת לא הצליח להשלים את הפעולה. נסו שוב."
        if isinstance(exc, ValueError):
            return str(exc)
        return "לא ניתן להשלים את הפעולה. נסו שוב."


class CustomerProfilePresenter:
    def __init__(self, view, service: CustomerServicePort, customer_id: str, executor: OperationExecutor | None = None) -> None:
        self.view, self.service, self.customer_id = view, service, customer_id
        self._operations = PresenterOperations(executor, "customer_profile")

    def invalidate_requests(self) -> None:
        self._operations.invalidate()

    def load(self) -> None:
        context = self._operations.replace("load")
        self.view.set_loading(True)

        def success(customer):
            if not self._operations.is_current(context):
                return
            self.view.show_profile(customer_details(customer), [contact_row(x) for x in customer.get("contacts", [])])

        def failure(exc):
            if not self._operations.is_current(context):
                return
            retriable = isinstance(exc, ApiError) and exc.retriable
            permission = isinstance(exc, ApiError) and exc.kind == ApiErrorKind.PERMISSION
            self.view.show_error(CustomersPresenter._message(exc), retriable=retriable, permission=permission)

        def finished():
            if self._operations.finish(context):
                self.view.set_loading(False)

        self._operations.executor.submit(context, lambda: self.service.customer(self.customer_id), success, failure, finished)

    def retry(self) -> None:
        self.load()
