from __future__ import annotations

from uuid import UUID

from psycopg.rows import dict_row

from backend.app.db.connection import get_connection
from backend.app.infrastructure.repositories import customer_repository as repo
from backend.app.schemas.customer import (
    CustomerContactCreate,
    CustomerContactUpdate,
    CustomerCreate,
    CustomerUpdate,
)


class CustomerNotFoundError(Exception):
    pass


class ContactNotFoundError(Exception):
    pass


class CustomerAccessDeniedError(Exception):
    pass


def _can_read_customer(current_user: dict, customer_id: UUID) -> bool:
    if current_user["role"] == "manager":
        return True
    if current_user["role"] == "customer":
        return current_user.get("customer_id") == customer_id
    return False


def _require_customer(cur, customer_id: UUID) -> dict:
    customer = repo.get_customer(cur, customer_id)
    if customer is None:
        raise CustomerNotFoundError
    return customer


def _require_contact(cur, contact_id: UUID) -> dict:
    contact = repo.get_contact(cur, contact_id)
    if contact is None:
        raise ContactNotFoundError
    return contact


def _require_customer_access(current_user: dict, customer_id: UUID) -> None:
    if not _can_read_customer(current_user, customer_id):
        raise CustomerAccessDeniedError


def list_customers(
    search: str | None,
    city: str | None,
    customer_type: str | None,
    is_active: bool | None,
    order_by: str,
    limit: int,
    offset: int,
    current_user: dict,
) -> list[dict]:
    if current_user["role"] != "manager":
        raise CustomerAccessDeniedError

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            return repo.list_customers(
                cur=cur,
                search=search,
                city=city,
                customer_type=customer_type,
                is_active=is_active,
                order_by=order_by,
                limit=limit,
                offset=offset,
            )


def get_customer(customer_id: UUID) -> tuple[dict, list[dict]]:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            customer = _require_customer(cur, customer_id)
            contacts = repo.list_contacts(cur, customer_id)
    return customer, contacts


def get_customer_for_user(customer_id: UUID, current_user: dict) -> tuple[dict, list[dict]]:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            customer = _require_customer(cur, customer_id)
            _require_customer_access(current_user, customer["id"])
            contacts = repo.list_contacts(cur, customer_id)
    return customer, contacts


def create_customer(payload: CustomerCreate) -> dict:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            customer = repo.create_customer(cur, payload.model_dump())
            conn.commit()
    return customer


def update_customer(customer_id: UUID, payload: CustomerUpdate) -> tuple[dict, list[dict]]:
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return get_customer(customer_id)

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            _require_customer(cur, customer_id)
            customer = repo.update_customer(cur, customer_id, update_data)
            contacts = repo.list_contacts(cur, customer_id)
            conn.commit()
    return customer, contacts


def soft_delete_customer(customer_id: UUID) -> tuple[dict, list[dict]]:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            _require_customer(cur, customer_id)
            customer = repo.soft_delete_customer(cur, customer_id)
            contacts = repo.list_contacts(cur, customer_id)
            conn.commit()
    return customer, contacts


def list_customer_contacts(customer_id: UUID, is_active: bool | None) -> list[dict]:
    return list_customer_contacts_for_user(customer_id, is_active, {"role": "manager"})


def list_customer_contacts_for_user(
    customer_id: UUID,
    is_active: bool | None,
    current_user: dict,
) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            _require_customer(cur, customer_id)
            _require_customer_access(current_user, customer_id)
            return repo.list_contacts(cur, customer_id, True if is_active is None else is_active)


def create_customer_contact(customer_id: UUID, payload: CustomerContactCreate) -> dict:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            _require_customer(cur, customer_id)
            if payload.is_primary:
                repo.clear_primary_contacts(cur, customer_id)
            contact = repo.create_contact(cur, customer_id, payload.model_dump())
            conn.commit()
    return contact


def get_customer_contact(contact_id: UUID) -> dict:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            return _require_contact(cur, contact_id)


def update_customer_contact(contact_id: UUID, payload: CustomerContactUpdate) -> dict:
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return get_customer_contact(contact_id)

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            existing = _require_contact(cur, contact_id)
            if update_data.get("is_primary") is True:
                repo.clear_primary_contacts(cur, existing["customer_id"], contact_id)
            contact = repo.update_contact(cur, contact_id, update_data)
            conn.commit()
    return contact


def soft_delete_customer_contact(contact_id: UUID) -> dict:
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            _require_contact(cur, contact_id)
            contact = repo.soft_delete_contact(cur, contact_id)
            conn.commit()
    return contact
