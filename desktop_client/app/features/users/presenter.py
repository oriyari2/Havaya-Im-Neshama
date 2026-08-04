from __future__ import annotations

import logging
from desktop_client.app.api.client import ApiError, ApiErrorKind
from desktop_client.app.models.operation import OperationExecutor, PresenterOperations
from desktop_client.app.shared.validation.account import account_password, login_email
from desktop_client.app.shared.validation.dialogs import safe_backend_conflict


logger = logging.getLogger(__name__)
class UsersPresenter:
    def __init__(self, view, service, *, current_user_id: str, session_role: str, limit: int = 25, executor: OperationExecutor | None = None) -> None:
        self.view = view
        self.service = service
        self.current_user_id = current_user_id
        self.session_role = session_role
        self.filters = {"search": None, "role": "manager", "is_active": None, "order_by": "display_name", "limit": limit, "offset": 0}
        self.selected_id: str | None = None
        self.selected: dict | None = None
        self.loading = False
        self.submitting = False
        self._operations = PresenterOperations(executor, "users")
        self._last_list_render = None

    def reset_to_default(self) -> None:
        limit = self.filters["limit"]
        self.filters = {"search": None, "role": "manager", "is_active": None, "order_by": "display_name", "limit": limit, "offset": 0}
        self.selected_id = self.selected = None
        self._last_list_render = None
        self.view.reset_to_default()

    def invalidate_requests(self) -> None:
        self._operations.invalidate()
        self.loading = False
        self.view.set_loading(False)

    def _allowed(self) -> bool:
        if self.session_role == "manager":
            return True
        self.view.show_error("אין הרשאה לניהול מנהלים.", permission=True)
        return False

    def load(self) -> None:
        if not self._allowed():
            return
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
                self.view.show_users(
                    items,
                    offset=filters["offset"],
                    count=len(items),
                    filtered=any(filters[key] not in (None, "") for key in ("search", "is_active")),
                )
                self._last_list_render = signature
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
        self.filters.update({key: values.get(key) for key in ("search", "is_active", "order_by") if key in values})
        self.filters["role"] = "manager"
        self.filters["offset"] = 0
        self.load()

    def page(self, offset: int, limit: int) -> None:
        self.filters.update(offset=max(0, offset), limit=limit)
        self.load()

    def retry(self) -> None:
        invalidate = getattr(self.service, "invalidate_list", None)
        if invalidate is not None:
            invalidate(dict(self.filters))
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
                self.view.show_error("המנהל שנבחר אינו קיים עוד.")
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
            payload = {
                "email": login_email(values.get("email")),
                "password": account_password(values.get("password"), values.get("password_confirmation")),
                "role": "manager",
                "manager_name": self._required(values.get("manager_name"), "יש להזין שם מנהל."),
            }
        except ValueError as exc:
            form.show_error(str(exc))
            return
        self._submit(form, lambda: self.service.create_user(payload), "המנהל נוצר בהצלחה.")

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
            manager_name = self._required(values.get("manager_name"), "יש להזין שם מנהל.")
        except ValueError as exc:
            form.show_error(str(exc)); return
        self._submit(form, lambda: self.service.update_manager(self.selected_id, manager_name), "פרטי המנהל עודכנו.")

    def begin_reset_password(self) -> None:
        if self.selected:
            self.view.open_reset_password(self.selected, self.submit_reset_password)

    def submit_reset_password(self, values: dict, form) -> None:
        if not self.selected_id or self.submitting:
            return
        try:
            password = account_password(values.get("password"), values.get("password_confirmation"))
        except ValueError as exc:
            form.show_error(str(exc))
            return
        self._submit(form, lambda: (self.service.reset_password(self.selected_id, password) or self.selected), "הסיסמה שונתה בהצלחה.")

    def activate(self) -> None:
        if self.selected_id:
            self._mutate(lambda: self.service.activate(self.selected_id), "המנהל הופעל.")

    def deactivate(self) -> None:
        if not self.selected or not self.view.confirm_deactivation(self.selected["email"]):
            return
        self._mutate(lambda: self.service.deactivate(self.selected_id), "המנהל הושבת.")

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
            if exc.kind == ApiErrorKind.CONFLICT:
                return safe_backend_conflict(exc, "לא ניתן לבצע את הפעולה במצב הנוכחי.")
            return {
                ApiErrorKind.PERMISSION: "אין הרשאה לניהול מנהלים.",
                ApiErrorKind.VALIDATION: "יש לתקן את פרטי המנהל ולנסות שוב.",
                ApiErrorKind.NOT_FOUND: "המנהל שנבחר אינו קיים.",
                ApiErrorKind.CONNECTION: "לא ניתן להתחבר לשרת. נסו שוב.",
                ApiErrorKind.SERVER: "השרת לא הצליח להשלים את הפעולה. נסו שוב.",
            }.get(exc.kind, "הפעולה נכשלה.")
        return "הפעולה נכשלה. נסו שוב."
