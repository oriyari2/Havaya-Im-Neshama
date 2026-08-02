from __future__ import annotations

from desktop_client.app.api.client import ApiClient


class AIChatService:
    def __init__(self, api_client: ApiClient) -> None:
        self.api_client = api_client

    def consult(self, prompt: str) -> dict:
        post = getattr(self.api_client, "post_ai", self.api_client.post)
        response = post("/api/ai/consult", {"prompt": prompt})
        return response if isinstance(response, dict) else {"answer": ""}
