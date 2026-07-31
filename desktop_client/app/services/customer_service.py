from __future__ import annotations

from desktop_client.app.api.client import ApiClient


class CustomerService:
    def __init__(self, api_client: ApiClient) -> None:
        self.api_client = api_client

    def list_customers(self, filters: dict[str, object]) -> dict:
        return self.api_client.get("/customers", filters)

    def invalidate_list(self, filters: dict[str, object]) -> None:
        self.api_client.invalidate_cached_get("/customers", filters)

    def customer(self, customer_id: str) -> dict:
        return self.api_client.get(f"/customers/{customer_id}")

    def create_customer(self, payload: dict[str, object]) -> dict:
        return self.api_client.post("/customers", payload)

    def update_customer(self, customer_id: str, payload: dict[str, object]) -> dict:
        return self.api_client.put(f"/customers/{customer_id}", payload)

    def delete_customer(self, customer_id: str) -> None:
        self.api_client.delete(f"/customers/{customer_id}")
