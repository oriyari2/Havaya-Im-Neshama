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
        return session

    def logout(self) -> None:
        self.api_client.set_access_token(None)

    def expire_session(self) -> None:
        self.logout()
