from __future__ import annotations

from desktop_client.app.api.client import ApiClient
from desktop_client.app.models.session import Session


class AuthService:
    def __init__(self, api_client: ApiClient) -> None:
        self.api_client = api_client

    def login(self, email: str, password: str) -> Session:
        payload = self.api_client.post("/auth/login", {"email": email, "password": password})
        session = Session.from_login_response(payload)
        self.api_client.set_access_token(session.access_token)
        configure_scope = getattr(self.api_client, "set_performance_scope", None)
        if configure_scope is not None:
            configure_scope(session.user_id, session.role)
        return session

    def logout(self) -> None:
        self.api_client.set_access_token(None)
        clear_scope = getattr(self.api_client, "clear_performance_scope", None)
        if clear_scope is not None:
            clear_scope()

    def expire_session(self) -> None:
        self.logout()
