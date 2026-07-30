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

    def contacts(self, customer_id: str, *, is_active: bool | None = None) -> list[dict]:
        return self.api_client.get(f"/customers/{customer_id}/contacts", {"is_active": is_active})

    def create_contact(self, customer_id: str, payload: dict[str, object]) -> dict:
        return self.api_client.post(f"/customers/{customer_id}/contacts", payload)

    def update_contact(self, contact_id: str, payload: dict[str, object]) -> dict:
        return self.api_client.put(f"/customer-contacts/{contact_id}", payload)

    def deactivate_contact(self, contact_id: str) -> dict:
        return self.api_client.delete(f"/customer-contacts/{contact_id}")

    def reactivate_contact(self, contact_id: str) -> dict:
        return self.update_contact(contact_id, {"is_active": True})
