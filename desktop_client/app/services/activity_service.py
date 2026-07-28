from __future__ import annotations

from desktop_client.app.api.client import ApiClient


class ActivityService:
    def __init__(self, api_client: ApiClient) -> None:
        self.api_client = api_client

    def list_activities(self, filters: dict[str, object]) -> dict:
        return self.api_client.get("/activities", filters)

    def activity(self, activity_id: str) -> dict:
        return self.api_client.get(f"/activities/{activity_id}")

    def create_activity(self, payload: dict[str, object]) -> dict:
        return self.api_client.post("/activities", payload)

    def update_activity(self, activity_id: str, payload: dict[str, object]) -> dict:
        return self.api_client.put(f"/activities/{activity_id}", payload)

    def deactivate_activity(self, activity_id: str) -> dict:
        return self.api_client.delete(f"/activities/{activity_id}")

    def reactivate_activity(self, activity_id: str) -> dict:
        return self.update_activity(activity_id, {"is_active": True})
