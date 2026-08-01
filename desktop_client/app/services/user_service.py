from __future__ import annotations

from desktop_client.app.api.client import ApiClient


class UserService:
    def __init__(self, api_client: ApiClient) -> None:
        self.api_client = api_client

    def list_users(self, filters: dict[str, object]) -> dict:
        return self.api_client.get("/users", filters)

    def invalidate_list(self, filters: dict[str, object]) -> None:
        self.api_client.invalidate_cached_get("/users", filters)

    def user(self, user_id: str) -> dict:
        return self.api_client.get(f"/users/{user_id}")

    def create_user(self, payload: dict[str, object]) -> dict:
        return self.api_client.post("/users", payload)

    def update_email(self, user_id: str, email: str) -> dict:
        return self.api_client.put(f"/users/{user_id}", {"email": email})

    def update_manager(self, user_id: str, manager_name: str) -> dict:
        return self.api_client.put(f"/users/{user_id}", {"manager_name": manager_name})

    def activate(self, user_id: str) -> dict:
        return self.api_client.post(f"/users/{user_id}/activate", {})

    def deactivate(self, user_id: str) -> dict:
        return self.api_client.post(f"/users/{user_id}/deactivate", {})

    def reset_password(self, user_id: str, new_password: str) -> None:
        self.api_client.post(f"/users/{user_id}/reset-password", {"new_password": new_password})
