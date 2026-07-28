from __future__ import annotations

from typing import Callable, Protocol

from desktop_client.app.models.session import Session


class LoginViewPort(Protocol):
    def set_loading(self, loading: bool) -> None: ...
    def show_error(self, message: str) -> None: ...


class AuthPort(Protocol):
    def login(self, email: str, password: str) -> Session: ...


class LoginPresenter:
    def __init__(self, view: LoginViewPort, auth_service: AuthPort, on_authenticated: Callable[[Session], None]) -> None:
        self.view = view
        self.auth_service = auth_service
        self.on_authenticated = on_authenticated

    def login(self, email: str, password: str) -> None:
        if not email.strip() or not password:
            self.view.show_error("יש להזין דוא״ל וסיסמה.")
            return
        self.view.set_loading(True)
        try:
            session = self.auth_service.login(email.strip(), password)
        except Exception as exc:
            self.view.show_error(str(exc))
        else:
            self.on_authenticated(session)
        finally:
            self.view.set_loading(False)
