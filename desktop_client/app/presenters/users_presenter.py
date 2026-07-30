from __future__ import annotations

import logging
import re

from desktop_client.app.api.client import ApiError, ApiErrorKind
from desktop_client.app.models.operation import OperationExecutor, PresenterOperations


logger = logging.getLogger(__name__)
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _email(value: object) -> str:
    cleaned = str(value or "").strip().lower()
    if len(cleaned) > 254 or not EMAIL.match(cleaned):
        raise ValueError("כתובת הדוא״ל אינה תקינה.")
    return cleaned


def _password(value: object, confirmation: object) -> str:
    password = str(value or "")
    if not 8 <= len(password) <= 128 or password != password.strip() or any(not character.isprintable() for character in password):
        raise ValueError("הסיסמה חייבת להכיל 8 עד 128 תווים ללא רווחים בתחילה או בסוף.")
    if password != str(confirmation or ""):
        raise ValueError("אימות הסיסמה אינו תואם.")
    return password


class UsersPresenter:
    def __init__(self, view, service, *, current_user_id: str, session_role: str, limit: int = 25, executor: OperationExecutor | None = None) -> None:
        self.view = view
        self.service = service
        self.current_user_id = current_user_id
        self.session_role = session_role
        self.filters = {"search": None, "role": None, "is_active": None, "limit": limit, "offset": 0}
        self.selected_id: str | None = None
        self.selected: dict | None = None
        self.loading = False
        self.submitting = False
        self._operations = PresenterOperations(executor, "users")

    def invalidate_requests(self) -> None:
        self._operations.invalidate()
        self.loading = self.submitting = False

    def _allowed(self) -> bool:
        if self.session_role == "manager":
            return True
        self.view.show_error("אין הרשאה לניהול משתמשים.", permission=True)
        return False

    def load(self) -> None:
        if not self._allowed():
            return
        context = self._operations.replace("list")
        filters = dict(self.filters)
        self.loading = True
        self.view.set_loading(True)
        def success(payload):
            if not self._operations.is_current(context):
                return
            items = payload["items"]
            self.view.show_users(items, offset=filters["offset"], count=len(items), filtered=any(filters[key] not in (None, "") for key in ("search", "role", "is_active")))
            ids = {str(item["id"]) for item in items}
            if self.selected_id in ids:
                self.view.select_user(self.selected_id)
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

        self._operations.executor.submit(context, lambda: self.service.list_users(filters), success, failure, finished)

    def apply_filters(self, values: dict) -> None:
        self.filters.update({key: values.get(key) for key in ("search", "role", "is_active") if key in values})
        self.filters["offset"] = 0
        self.load()

    def page(self, offset: int, limit: int) -> None:
        self.filters.update(offset=max(0, offset), limit=limit)
        self.load()

    def retry(self) -> None:
        self.load()

    def select(self, user_id: str) -> None:
        if not self._allowed():
            return
        self.selected_id = user_id
        context = self._operations.replace("detail")
        self.view.set_detail_loading(True)

        def success(user):
            if not self._operations.is_current(context):
                return
            if self.selected_id != user_id:
                return
            self.selected = user
            self.view.show_details(user, current_user_id=self.current_user_id)
        def failure(exc):
            if not self._operations.is_current(context):
                return
            if isinstance(exc, ApiError) and exc.kind == ApiErrorKind.NOT_FOUND:
                self.selected_id = self.selected = None
                self.view.clear_details()
                self.view.show_error("המשתמש שנבחר אינו קיים עוד.")
                self.load()
            else:
                self._error(exc)

        def finished():
            if self._operations.finish(context):
                self.view.set_detail_loading(False)

        self._operations.executor.submit(context, lambda: self.service.user(user_id), success, failure, finished)

    def begin_create(self) -> None:
        if not self._allowed() or self.submitting:
            return
        self.view.open_create(self.submit_create)

    def submit_create(self, values: dict, form) -> None:
        if self.submitting:
            return
        try:
            role = str(values.get("role") or "")
            if role not in {"manager", "customer", "instructor"}:
                raise ValueError("יש לבחור תפקיד.")
            payload = {
                "email": _email(values.get("email")),
                "password": _password(values.get("password"), values.get("password_confirmation")),
                "role": role,
            }
            if role == "manager":
                payload["manager_name"] = self._required(values.get("manager_name"), "יש להזין שם מנהל.")
            elif role == "customer":
                payload.update(
                    customer_name=self._required(values.get("customer_name"), "יש להזין שם לקוח."),
                    customer_type=self._required(values.get("customer_type"), "יש להזין סוג לקוח."),
                    customer_city=self._required(values.get("customer_city"), "יש להזין עיר לקוח."),
                    contact_name=self._required(values.get("contact_name"), "יש להזין שם איש קשר."),
                    contact_phone=self._required(values.get("contact_phone"), "יש להזין טלפון איש קשר."),
                )
            elif role == "instructor":
                payload.update(
                    instructor_name=self._required(values.get("instructor_name"), "יש להזין שם מדריך."),
                    instructor_phone=str(values.get("instructor_phone") or "").strip() or None,
                    instructor_city=self._required(values.get("instructor_city"), "יש להזין עיר מדריך."),
                )
        except ValueError as exc:
            form.show_error(str(exc))
            return
        self._submit(form, lambda: self.service.create_user(payload), "המשתמש נוצר בהצלחה.")

    @staticmethod
    def _required(value: object, message: str) -> str:
        cleaned = str(value or "").strip()
        if not cleaned:
            raise ValueError(message)
        return cleaned

    def begin_edit(self) -> None:
        if self.selected:
            self.view.open_edit(self.selected, self.submit_edit)

    def submit_edit(self, values: dict, form) -> None:
        if not self.selected_id or self.submitting:
            return
        try:
            email = _email(values.get("email"))
        except ValueError as exc:
            form.show_error(str(exc))
            return
        self._submit(form, lambda: self.service.update_email(self.selected_id, email), "כתובת הדוא״ל עודכנה.")

    def begin_reset_password(self) -> None:
        if self.selected:
            self.view.open_reset_password(self.selected, self.submit_reset_password)

    def submit_reset_password(self, values: dict, form) -> None:
        if not self.selected_id or self.submitting:
            return
        try:
            password = _password(values.get("password"), values.get("password_confirmation"))
        except ValueError as exc:
            form.show_error(str(exc))
            return
        self._submit(form, lambda: (self.service.reset_password(self.selected_id, password) or self.selected), "הסיסמה אופסה בהצלחה.")

    def activate(self) -> None:
        if self.selected_id:
            self._mutate(lambda: self.service.activate(self.selected_id), "המשתמש הופעל.")

    def deactivate(self) -> None:
        if not self.selected or not self.view.confirm_deactivation(self.selected["email"]):
            return
        self._mutate(lambda: self.service.deactivate(self.selected_id), "המשתמש הושבת.")

    def _submit(self, form, operation, message: str) -> None:
        if self.submitting:
            return
        context = self._operations.begin("submit")
        if context is None:
            return
        self.submitting = True
        form.set_submitting(True)

        def success(result):
            if not self._operations.is_current(context):
                return
            if result and result.get("id"):
                self.selected_id = str(result["id"])
            form.close_success()
            self.view.show_success(message)
            self.load()
            if self.selected_id:
                self.select(self.selected_id)
        def failure(exc):
            if self._operations.is_current(context):
                form.show_error(self.message(exc))

        def finished():
            if self._operations.finish(context):
                self.submitting = False
                form.set_submitting(False)

        self._operations.executor.submit(context, operation, success, failure, finished)

    def _mutate(self, operation, message: str) -> None:
        if self.submitting:
            return
        context = self._operations.begin("mutate")
        if context is None:
            return
        self.submitting = True
        self.view.set_loading(True)

        def success(result):
            if not self._operations.is_current(context):
                return
            self.selected_id = str(result["id"])
            self.selected = result
            self.view.show_success(message)
            self.load()
            self.select(self.selected_id)
        def failure(exc):
            if self._operations.is_current(context):
                self._error(exc)

        def finished():
            if self._operations.finish(context):
                self.submitting = False
                self.view.set_loading(False)

        self._operations.executor.submit(context, operation, success, failure, finished)

    def _error(self, exc: Exception) -> None:
        if not isinstance(exc, ApiError):
            logger.error("Unexpected user administration failure", exc_info=(type(exc), exc, exc.__traceback__))
        self.view.show_error(self.message(exc), retriable=isinstance(exc, ApiError) and exc.retriable, permission=isinstance(exc, ApiError) and exc.kind == ApiErrorKind.PERMISSION)

    @staticmethod
    def message(exc: Exception) -> str:
        if isinstance(exc, ApiError):
            return {
                ApiErrorKind.PERMISSION: "אין הרשאה לניהול משתמשים.",
                ApiErrorKind.CONFLICT: "הדוא״ל או הפרופיל כבר משויכים למשתמש אחר, או שהפעולה אינה מותרת.",
                ApiErrorKind.VALIDATION: "יש לתקן את פרטי המשתמש ולנסות שוב.",
                ApiErrorKind.NOT_FOUND: "המשתמש או הפרופיל שנבחרו אינם קיימים.",
                ApiErrorKind.CONNECTION: "לא ניתן להתחבר לשרת. נסו שוב.",
                ApiErrorKind.SERVER: "השרת לא הצליח להשלים את הפעולה. נסו שוב.",
            }.get(exc.kind, "הפעולה נכשלה.")
        return "הפעולה נכשלה. נסו שוב."
