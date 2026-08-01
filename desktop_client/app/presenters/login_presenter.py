from __future__ import annotations

from typing import Callable, Protocol

from desktop_client.app.models.session import Session
from desktop_client.app.api.client import ApiError, ApiErrorKind
from desktop_client.app.models.operation import OperationExecutor, PresenterOperations
from desktop_client.app.models.request_state import RequestPhase, RequestState


class LoginViewPort(Protocol):
    def set_loading(self, loading: bool) -> None: ...
    def show_error(self, message: str) -> None: ...
    def render_request_state(self, state: RequestState) -> None: ...


class AuthPort(Protocol):
    def login(self, email: str, password: str) -> Session: ...


class LoginPresenter:
    def __init__(self, view: LoginViewPort, auth_service: AuthPort, on_authenticated: Callable[[Session], None], executor: OperationExecutor | None = None) -> None:
        self.view = view
        self.auth_service = auth_service
        self.on_authenticated = on_authenticated
        self._loading = False
        self._authenticated = False
        self._operations = PresenterOperations(executor, "login")

    def invalidate_requests(self) -> None:
        self._operations.invalidate()
        self._loading = False
        self._authenticated = False

    def login(self, email: str, password: str) -> None:
        if self._loading:
            return
        if not email.strip() or not password:
            self.view.show_error("יש להזין דוא״ל וסיסמה.")
            return
        context = self._operations.begin("login")
        if context is None:
            return
        self._loading = True
        self._authenticated = False
        self.view.set_loading(True)
        self.view.render_request_state(RequestState(RequestPhase.LOADING, "מתחבר…", "login", blocks_primary_action=True))
        def failed(exc: Exception) -> None:
            if not self._operations.is_current(context):
                return
            if isinstance(exc, ApiError) and exc.kind == ApiErrorKind.CONNECTION:
                message = "לא ניתן להתחבר לשרת. בדקו את החיבור ונסו שוב."
            elif isinstance(exc, ApiError) and exc.kind == ApiErrorKind.SERVER:
                message = "השרת לא הצליח להשלים את ההתחברות. נסו שוב."
            elif isinstance(exc, ApiError):
                message = "פרטי ההתחברות אינם תקינים."
            else:
                message = "לא ניתן להשלים את ההתחברות. נסו שוב."
            self.view.show_error(message)
            phase = RequestPhase.CONNECTION_ERROR if isinstance(exc, ApiError) and exc.kind == ApiErrorKind.CONNECTION else RequestPhase.SERVER_ERROR
            self.view.render_request_state(RequestState(phase, message, "login"))
        def succeeded(session: Session) -> None:
            if not self._operations.is_current(context):
                return
            self._authenticated = True
            self.on_authenticated(session)

        def finished() -> None:
            if not self._operations.finish(context):
                return
            self._loading = False
            if not self._authenticated:
                self.view.set_loading(False)

        self._operations.executor.submit(
            context,
            lambda: self.auth_service.login(email.strip(), password),
            succeeded,
            failed,
            finished,
        )
