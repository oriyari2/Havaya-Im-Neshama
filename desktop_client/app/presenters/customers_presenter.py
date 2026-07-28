from __future__ import annotations

import re
from typing import Callable, Protocol

from desktop_client.app.api.client import ApiError, ApiErrorKind
from desktop_client.app.presenters.customer_formatting import contact_row, customer_details, customer_row


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class FormPort(Protocol):
    def set_submitting(self, submitting: bool) -> None: ...
    def show_error(self, message: str) -> None: ...
    def close_success(self) -> None: ...


class CustomersViewPort(Protocol):
    def set_loading(self, loading: bool) -> None: ...
    def show_error(self, message: str, *, retriable: bool = False, permission: bool = False) -> None: ...
    def show_success(self, message: str) -> None: ...
    def show_customers(self, rows: list[dict], *, offset: int, count: int, filtered: bool) -> None: ...
    def show_details(self, details: list[tuple[str, str]], customer: dict, contacts: list[dict]) -> None: ...
    def clear_details(self) -> None: ...
    def select_customer(self, customer_id: str) -> None: ...
    def open_customer_form(self, initial: dict | None, submit: Callable) -> None: ...
    def open_contact_form(self, initial: dict | None, submit: Callable) -> None: ...
    def confirm_customer_deactivation(self, name: str) -> bool: ...
    def confirm_contact_deactivation(self, name: str) -> bool: ...


class CustomerServicePort(Protocol):
    def list_customers(self, filters: dict[str, object]) -> dict: ...
    def customer(self, customer_id: str) -> dict: ...
    def create_customer(self, payload: dict[str, object]) -> dict: ...
    def update_customer(self, customer_id: str, payload: dict[str, object]) -> dict: ...
    def deactivate_customer(self, customer_id: str) -> dict: ...
    def reactivate_customer(self, customer_id: str) -> dict: ...
    def contacts(self, customer_id: str, *, is_active: bool | None = None) -> list[dict]: ...
    def create_contact(self, customer_id: str, payload: dict[str, object]) -> dict: ...
    def update_contact(self, contact_id: str, payload: dict[str, object]) -> dict: ...
    def deactivate_contact(self, contact_id: str) -> dict: ...
    def reactivate_contact(self, contact_id: str) -> dict: ...


def validate_customer(values: dict[str, object]) -> dict[str, object]:
    name = str(values.get("name") or "").strip()
    if not name:
        raise ValueError("יש להזין שם לקוח.")
    email = str(values.get("email") or "").strip() or None
    if email and not EMAIL_PATTERN.match(email):
        raise ValueError("כתובת הדוא״ל אינה תקינה.")
    return {
        "name": name,
        "customer_type": str(values.get("customer_type") or "").strip() or None,
        "city": str(values.get("city") or "").strip() or None,
        "address": str(values.get("address") or "").strip() or None,
        "phone": str(values.get("phone") or "").strip() or None,
        "email": email,
        "notes": str(values.get("notes") or "").strip() or None,
        "is_active": bool(values.get("is_active", True)),
    }


def validate_contact(values: dict[str, object]) -> dict[str, object]:
    name = str(values.get("full_name") or "").strip()
    if not name:
        raise ValueError("יש להזין שם איש קשר.")
    email = str(values.get("email") or "").strip() or None
    if email and not EMAIL_PATTERN.match(email):
        raise ValueError("כתובת הדוא״ל של איש הקשר אינה תקינה.")
    return {
        "full_name": name, "role_title": str(values.get("role_title") or "").strip() or None,
        "phone": str(values.get("phone") or "").strip() or None, "email": email,
        "is_primary": bool(values.get("is_primary")),
        "notes": str(values.get("notes") or "").strip() or None,
        "is_active": bool(values.get("is_active", True)),
    }


class CustomersPresenter:
    def __init__(self, view: CustomersViewPort, service: CustomerServicePort, *, limit: int = 25) -> None:
        self.view, self.service = view, service
        self.filters: dict[str, object] = {"search": None, "city": None, "customer_type": None, "is_active": None, "order_by": "name", "limit": limit, "offset": 0}
        self.selected_id: str | None = None
        self.selected_customer: dict | None = None
        self._loading = False
        self._submitting = False

    def load(self) -> None:
        if self._loading:
            return
        self._loading = True
        self.view.set_loading(True)
        try:
            payload = self.service.list_customers(dict(self.filters))
            items = payload["items"]
            self.view.show_customers(
                [customer_row(item) for item in items], offset=int(self.filters["offset"]),
                count=len(items), filtered=any(self.filters[k] not in (None, "") for k in ("search", "city", "customer_type", "is_active")),
            )
            ids = {str(item["id"]) for item in items}
            if self.selected_id in ids:
                self.view.select_customer(self.selected_id)
            elif self.selected_id is not None:
                self.selected_id = self.selected_customer = None
                self.view.clear_details()
        except Exception as exc:
            self._show_error(exc)
        finally:
            self._loading = False
            self.view.set_loading(False)

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
        self.view.set_loading(True)
        try:
            customer = self.service.customer(customer_id)
            self.selected_customer = customer
            self.view.show_details(customer_details(customer), customer, [contact_row(x) for x in customer.get("contacts", [])])
        except ApiError as exc:
            if exc.kind == ApiErrorKind.NOT_FOUND:
                self.selected_id = self.selected_customer = None
                self.view.clear_details()
                self.view.show_error("הלקוח שנבחר אינו קיים עוד. הרשימה רועננה.")
                self.load()
            else:
                self._show_error(exc)
        except Exception as exc:
            self._show_error(exc)
        finally:
            self.view.set_loading(False)

    def begin_create(self) -> None:
        self.view.open_customer_form(None, self.submit_create)

    def begin_edit(self) -> None:
        if self.selected_customer:
            self.view.open_customer_form(self.selected_customer, self.submit_edit)

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
        try:
            customer = self.service.update_customer(customer_id, payload) if customer_id else self.service.create_customer(payload)
            form.close_success()
            self.selected_id = str(customer["id"])
            self.view.show_success("הלקוח נשמר בהצלחה.")
            self.load()
            self.select(self.selected_id)
        except Exception as exc:
            form.show_error(self._message(exc))
            if isinstance(exc, ApiError) and exc.kind == ApiErrorKind.CONFLICT and self.selected_id:
                self.select(self.selected_id)
        finally:
            self._submitting = False
            form.set_submitting(False)

    def deactivate(self) -> None:
        customer = self.selected_customer
        if not customer or not customer.get("is_active") or not self.view.confirm_customer_deactivation(str(customer["name"])):
            return
        self._mutate(lambda: self.service.deactivate_customer(str(customer["id"])), "הלקוח הושבת.")

    def reactivate(self) -> None:
        customer = self.selected_customer
        if not customer or customer.get("is_active"):
            return
        self._mutate(lambda: self.service.reactivate_customer(str(customer["id"])), "הלקוח הופעל מחדש.")

    def begin_contact_create(self) -> None:
        if self.selected_customer:
            self.view.open_contact_form(None, self.submit_contact_create)

    def begin_contact_edit(self, contact: dict) -> None:
        self.view.open_contact_form(contact, lambda values, form: self.submit_contact_edit(str(contact["id"]), values, form))

    def submit_contact_create(self, values: dict[str, object], form: FormPort) -> None:
        self._submit_contact(values, form, None)

    def submit_contact_edit(self, contact_id: str, values: dict[str, object], form: FormPort) -> None:
        self._submit_contact(values, form, contact_id)

    def _submit_contact(self, values: dict[str, object], form: FormPort, contact_id: str | None) -> None:
        if self._submitting or not self.selected_id:
            return
        try:
            payload = validate_contact(values)
        except ValueError as exc:
            form.show_error(str(exc))
            return
        self._submitting = True
        form.set_submitting(True)
        try:
            if contact_id:
                self.service.update_contact(contact_id, payload)
            else:
                self.service.create_contact(self.selected_id, payload)
            form.close_success()
            self.view.show_success("איש הקשר נשמר בהצלחה.")
            self.refresh_contacts()
        except Exception as exc:
            form.show_error(self._message(exc))
            if isinstance(exc, ApiError) and exc.kind == ApiErrorKind.CONFLICT:
                self.refresh_contacts()
        finally:
            self._submitting = False
            form.set_submitting(False)

    def deactivate_contact(self, contact: dict) -> None:
        if contact.get("is_active") and self.view.confirm_contact_deactivation(str(contact["full_name"])):
            self._mutate_contact(lambda: self.service.deactivate_contact(str(contact["id"])), "איש הקשר הושבת.")

    def reactivate_contact(self, contact: dict) -> None:
        if not contact.get("is_active"):
            self._mutate_contact(lambda: self.service.reactivate_contact(str(contact["id"])), "איש הקשר הופעל מחדש.")

    def refresh_contacts(self) -> None:
        if not self.selected_id:
            return
        try:
            customer = self.service.customer(self.selected_id)
            self.selected_customer = customer
            self.view.show_details(customer_details(customer), customer, [contact_row(x) for x in customer.get("contacts", [])])
        except Exception as exc:
            self._show_error(exc)

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

    def _mutate_contact(self, operation: Callable, message: str) -> None:
        if self._submitting:
            return
        self._submitting = True
        try:
            operation()
            self.view.show_success(message)
            self.refresh_contacts()
        except Exception as exc:
            self._show_error(exc)
        finally:
            self._submitting = False

    def _show_error(self, exc: Exception) -> None:
        permission = isinstance(exc, ApiError) and exc.kind == ApiErrorKind.PERMISSION
        retriable = isinstance(exc, ApiError) and exc.retriable
        self.view.show_error(self._message(exc), retriable=retriable, permission=permission)

    @staticmethod
    def _message(exc: Exception) -> str:
        if isinstance(exc, ApiError):
            if exc.kind == ApiErrorKind.PERMISSION:
                return "אין הרשאה לצפות או לשנות לקוחות."
            if exc.kind == ApiErrorKind.CONFLICT:
                return "הלקוח השתנה במקביל. הרשומה רועננה; נסו שוב."
            if exc.kind in {ApiErrorKind.VALIDATION, ApiErrorKind.NOT_FOUND}:
                return str(exc)
            if exc.kind == ApiErrorKind.CONNECTION:
                return "לא ניתן להתחבר לשרת. נסו שוב לאחר שהחיבור יחזור."
            if exc.kind == ApiErrorKind.SERVER:
                return "השרת לא הצליח להשלים את הפעולה. נסו שוב."
        return str(exc) or "הפעולה נכשלה."


class CustomerProfilePresenter:
    def __init__(self, view, service: CustomerServicePort, customer_id: str) -> None:
        self.view, self.service, self.customer_id = view, service, customer_id

    def load(self) -> None:
        self.view.set_loading(True)
        try:
            customer = self.service.customer(self.customer_id)
            self.view.show_profile(customer_details(customer), [contact_row(x) for x in customer.get("contacts", [])])
        except Exception as exc:
            retriable = isinstance(exc, ApiError) and exc.retriable
            permission = isinstance(exc, ApiError) and exc.kind == ApiErrorKind.PERMISSION
            self.view.show_error(CustomersPresenter._message(exc), retriable=retriable, permission=permission)
        finally:
            self.view.set_loading(False)

    def retry(self) -> None:
        self.load()
