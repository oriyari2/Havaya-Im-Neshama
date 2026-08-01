from __future__ import annotations

import logging
import re

from desktop_client.app.api.client import ApiError, ApiErrorKind
from desktop_client.app.models.operation import OperationExecutor, PresenterOperations
from desktop_client.app.presenters.account_validation import account_password, login_email
from desktop_client.app.presenters.instructor_formatting import instructor_details, instructor_row


logger = logging.getLogger(__name__)
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_instructor(values):
    name = str(values.get("full_name") or "").strip()
    if not name:
        raise ValueError("יש להזין שם מדריך.")
    email = str(values.get("email") or "").strip().lower() or None
    if email and not EMAIL.match(email):
        raise ValueError("כתובת הדוא״ל אינה תקינה.")
    return {
        "full_name": name,
        "phone": str(values.get("phone") or "").strip() or None,
        "email": email,
        "city": str(values.get("city") or "").strip() or None,
        "notes": str(values.get("notes") or "").strip() or None,
    }


class InstructorsPresenter:
    def __init__(self, view, service, account_service=None, limit=25, executor: OperationExecutor | None = None):
        self.view, self.service = view, service
        self.account_service = account_service
        self.filters = {"search": None, "city": None, "is_active": None, "order_by": "full_name", "limit": limit, "offset": 0}
        self.selected_id = None
        self.selected = None
        self.loading = False
        self.submitting = False
        self._operations = PresenterOperations(executor, "instructors")
        self._last_list_render = None

    def invalidate_requests(self):
        self._operations.invalidate()
        self.loading = False
        self.view.set_loading(False)

    def load(self):
        context = self._operations.replace("list")
        filters = dict(self.filters)
        self.loading = True
        if self._last_list_render is None:
            self.view.set_loading(True)

        def success(payload):
            if not self._operations.is_current(context):
                return
            items = payload["items"]
            signature = (filters, items)
            if signature != self._last_list_render:
                self.view.show_instructors(
                    [instructor_row(item) for item in items],
                    offset=filters["offset"],
                    count=len(items),
                    filtered=any(filters[key] not in (None, "") for key in ("search", "city", "is_active")),
                )
                self._last_list_render = signature
            ids = {str(item["id"]) for item in items}
            if self.selected_id in ids:
                self.view.select_instructor(self.selected_id)
            elif self.selected_id:
                self.selected_id = self.selected = None
                self.view.clear_details()

        def failure(exc):
            if self._operations.is_current(context):
                self._error(exc)

        def finished():
            if self._operations.finish(context):
                self.loading = False
                self.view.set_loading(False)

        self._operations.executor.submit(context, lambda: self.service.list_instructors(filters), success, failure, finished)

    def apply_filters(self, values):
        self.filters.update({key: value for key, value in values.items() if key in {"search", "city", "is_active", "order_by"}})
        self.filters["offset"] = 0
        self.load()

    def page(self, offset, limit):
        self.filters.update(offset=max(0, offset), limit=limit)
        self.load()

    def retry(self):
        invalidate = getattr(self.service, "invalidate_list", None)
        if invalidate is not None:
            invalidate(dict(self.filters))
        self.load()

    def select(self, instructor_id):
        self.selected_id = instructor_id
        context = self._operations.replace("detail")
        self.view.set_loading(True)

        def success(value):
            if self._operations.is_current(context) and self.selected_id == instructor_id:
                self.selected = value
                self.view.show_details(instructor_details(value), value)

        def failure(exc):
            if not self._operations.is_current(context):
                return
            if isinstance(exc, ApiError) and exc.kind == ApiErrorKind.NOT_FOUND:
                self.selected_id = self.selected = None
                self.view.clear_details()
                self.view.show_error("המדריך שנבחר אינו קיים עוד. הרשימה רועננה.")
                self.load()
            else:
                self._error(exc)

        def finished():
            if self._operations.finish(context):
                self.view.set_loading(False)

        self._operations.executor.submit(context, lambda: self.service.instructor(instructor_id), success, failure, finished)

    def begin_create(self):
        self.view.open_form(None, self.submit_create)

    def begin_edit(self):
        if self.selected:
            self.view.open_form(self.selected, self.submit_edit)

    def begin_change_password(self):
        if self.selected:
            self.view.open_change_password(self.submit_change_password)

    def submit_change_password(self, values, form):
        if self.submitting or not self.selected_id:
            return
        try:
            password = account_password(values.get("password"), values.get("password_confirmation"))
        except ValueError as exc:
            form.show_error(str(exc))
            return
        instructor_id = self.selected_id
        context = self._operations.begin("password")
        if context is None:
            return
        self.submitting = True
        form.set_submitting(True)

        def success(_value):
            if self._operations.is_current(context):
                form.close_success()
                self.view.show_success("הסיסמה שונתה בהצלחה.")

        def failure(exc):
            if self._operations.is_current(context):
                form.show_error(self.message(exc))

        def finished():
            if self._operations.finish(context):
                self.submitting = False
                form.set_submitting(False)

        self._operations.executor.submit(context, lambda: self.service.reset_password(instructor_id, password), success, failure, finished)

    def submit_create(self, values, form):
        if self.submitting:
            return
        try:
            if self.account_service is None:
                raise ValueError("שירות יצירת החשבון אינו זמין.")
            payload = {
                "email": login_email(values.get("email")),
                "password": account_password(values.get("password"), values.get("password_confirmation")),
                "role": "instructor",
                "instructor_name": self._required(values.get("full_name"), "יש להזין שם מדריך."),
                "instructor_phone": str(values.get("phone") or "").strip() or None,
                "instructor_city": str(values.get("city") or "").strip() or None,
                "instructor_notes": str(values.get("notes") or "").strip() or None,
            }
        except ValueError as exc:
            form.show_error(str(exc))
            return
        self._submit_account(payload, form)

    def submit_edit(self, values, form):
        self._submit(values, form, self.selected_id)

    @staticmethod
    def _required(value, message):
        cleaned = str(value or "").strip()
        if not cleaned:
            raise ValueError(message)
        return cleaned

    def _submit_account(self, payload, form):
        context = self._operations.begin("submit")
        if context is None:
            return
        self.submitting = True
        form.set_submitting(True)

        def success(user):
            if not self._operations.is_current(context):
                return
            self.selected_id = str(user["instructor_id"])
            form.close_success()
            self.view.show_success("המדריך וחשבון הכניסה נוצרו בהצלחה.")
            self.load()
            self.select(self.selected_id)

        def failure(exc):
            if self._operations.is_current(context):
                form.show_error(self.message(exc))

        def finished():
            if self._operations.finish(context):
                self.submitting = False
                form.set_submitting(False)

        self._operations.executor.submit(context, lambda: self.account_service.create_user(payload), success, failure, finished)

    def _submit(self, values, form, instructor_id):
        if self.submitting:
            return
        try:
            payload = validate_instructor(values)
        except ValueError as exc:
            form.show_error(str(exc))
            return
        context = self._operations.begin("submit")
        if context is None:
            return
        self.submitting = True
        form.set_submitting(True)

        def success(value):
            if not self._operations.is_current(context):
                return
            self.selected_id = str(value["id"])
            form.close_success()
            self.view.show_success("המדריך נשמר בהצלחה.")
            self.load()
            self.select(self.selected_id)

        def failure(exc):
            if not self._operations.is_current(context):
                return
            form.show_error(self.message(exc))
            if isinstance(exc, ApiError) and exc.kind == ApiErrorKind.CONFLICT and self.selected_id:
                self.select(self.selected_id)

        def finished():
            if self._operations.finish(context):
                self.submitting = False
                form.set_submitting(False)

        operation = lambda: self.service.update_instructor(instructor_id, payload) if instructor_id else self.service.create_instructor(payload)
        self._operations.executor.submit(context, operation, success, failure, finished)

    def delete(self):
        if not self.selected or not self.view.confirm_deletion(self.selected["full_name"]) or self.submitting:
            return
        instructor_id = self.selected_id
        context = self._operations.begin("delete")
        if context is None:
            return
        self.submitting = True
        self.view.set_loading(True)

        def success(_result):
            if self._operations.is_current(context):
                self.selected_id = self.selected = None
                self.view.clear_details()
                self.view.show_success("המדריך נמחק בהצלחה.")
                self.load()

        def failure(exc):
            if not self._operations.is_current(context):
                return
            if isinstance(exc, ApiError) and exc.kind == ApiErrorKind.NOT_FOUND:
                self.selected_id = self.selected = None
                self.view.clear_details()
                self.load()
            elif isinstance(exc, ApiError) and exc.kind == ApiErrorKind.CONFLICT:
                self.view.show_error(str(exc))
                self.select(instructor_id)
            else:
                self._error(exc)

        def finished():
            if self._operations.finish(context):
                self.submitting = False
                self.view.set_loading(False)

        self._operations.executor.submit(context, lambda: self.service.delete_instructor(instructor_id), success, failure, finished)

    def _mutate(self, operation, message):
        if self.submitting:
            return
        context = self._operations.begin("mutate")
        if context is None:
            return
        self.submitting = True

        def success(value):
            if self._operations.is_current(context):
                self.selected_id = str(value["id"])
                self.view.show_success(message)
                self.load()
                self.select(self.selected_id)

        def failure(exc):
            if self._operations.is_current(context):
                self._error(exc)

        def finished():
            if self._operations.finish(context):
                self.submitting = False

        self._operations.executor.submit(context, operation, success, failure, finished)

    def _error(self, exc):
        if not isinstance(exc, ApiError):
            logger.error("Unexpected instructor failure", exc_info=(type(exc), exc, exc.__traceback__))
        self.view.show_error(self.message(exc), retriable=isinstance(exc, ApiError) and exc.retriable, permission=isinstance(exc, ApiError) and exc.kind == ApiErrorKind.PERMISSION)

    @staticmethod
    def message(exc):
        if isinstance(exc, ApiError):
            if exc.kind == ApiErrorKind.PERMISSION:
                return "אין הרשאה לצפות במדריכים או לשנות אותם."
            if exc.kind == ApiErrorKind.CONFLICT:
                return "כתובת הדוא״ל כבר משויכת למדריך אחר."
            if exc.kind == ApiErrorKind.CONNECTION:
                return "לא ניתן להתחבר לשרת. נסו שוב."
            if exc.kind == ApiErrorKind.SERVER:
                return "השרת לא הצליח להשלים את הפעולה. נסו שוב."
        return str(exc) or "הפעולה נכשלה."


class InstructorProfilePresenter:
    def __init__(self, view, service, executor: OperationExecutor | None = None):
        self.view, self.service = view, service
        self._operations = PresenterOperations(executor, "instructor_profile")

    def invalidate_requests(self):
        self._operations.invalidate()
        self.view.set_loading(False)

    def load(self):
        context = self._operations.replace("load")
        self.view.set_loading(True)

        def success(value):
            if self._operations.is_current(context):
                self.view.show_profile(instructor_details(value))

        def failure(exc):
            if self._operations.is_current(context):
                self.view.show_error(InstructorsPresenter.message(exc), retriable=isinstance(exc, ApiError) and exc.retriable, permission=isinstance(exc, ApiError) and exc.kind == ApiErrorKind.PERMISSION)

        def finished():
            if self._operations.finish(context):
                self.view.set_loading(False)

        self._operations.executor.submit(context, self.service.my_profile, success, failure, finished)

    def retry(self):
        self.load()
