from __future__ import annotations

from typing import Annotated, NoReturn
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from backend.app.application.services import customer_service
from backend.app.schemas.customer import (
    CustomerContactCreate,
    CustomerContactResponse,
    CustomerContactUpdate,
    CustomerCreate,
    CustomerListResponse,
    CustomerResponse,
    CustomerUpdate,
)


router = APIRouter(tags=["customers"])


def _customer_response(customer: dict, contacts: list[dict] | None = None) -> CustomerResponse:
    return CustomerResponse(**customer, contacts=contacts or [])


def _raise_not_found(exc: Exception) -> NoReturn:
    if isinstance(exc, customer_service.CustomerNotFoundError):
        raise HTTPException(status_code=404, detail="Customer not found") from exc
    if isinstance(exc, customer_service.ContactNotFoundError):
        raise HTTPException(status_code=404, detail="Contact not found") from exc
    raise exc


@router.get("/customers", response_model=CustomerListResponse)
def list_customers(
    search: str | None = None,
    city: str | None = None,
    customer_type: str | None = None,
    is_active: bool | None = None,
    order_by: Annotated[str, Query(pattern="^(name|created_at)$")] = "name",
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> CustomerListResponse:
    try:
        customers = customer_service.list_customers(
            search=search,
            city=city,
            customer_type=customer_type,
            is_active=is_active,
            order_by=order_by,
            limit=limit,
            offset=offset,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not list customers") from exc

    return CustomerListResponse(
        items=[_customer_response(customer) for customer in customers],
        count=len(customers),
    )


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: UUID) -> CustomerResponse:
    try:
        customer, contacts = customer_service.get_customer(customer_id)
    except (customer_service.CustomerNotFoundError, customer_service.ContactNotFoundError) as exc:
        _raise_not_found(exc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not get customer") from exc

    return _customer_response(customer, contacts)


@router.post("/customers", response_model=CustomerResponse, status_code=201)
def create_customer(payload: CustomerCreate) -> CustomerResponse:
    try:
        customer = customer_service.create_customer(payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not create customer") from exc

    return _customer_response(customer)


@router.put("/customers/{customer_id}", response_model=CustomerResponse)
def update_customer(customer_id: UUID, payload: CustomerUpdate) -> CustomerResponse:
    try:
        customer, contacts = customer_service.update_customer(customer_id, payload)
    except customer_service.CustomerNotFoundError as exc:
        _raise_not_found(exc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not update customer") from exc

    return _customer_response(customer, contacts)


@router.delete("/customers/{customer_id}", response_model=CustomerResponse)
def delete_customer(customer_id: UUID) -> CustomerResponse:
    try:
        customer, contacts = customer_service.soft_delete_customer(customer_id)
    except customer_service.CustomerNotFoundError as exc:
        _raise_not_found(exc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not delete customer") from exc

    return _customer_response(customer, contacts)


@router.get(
    "/customers/{customer_id}/contacts",
    response_model=list[CustomerContactResponse],
)
def list_customer_contacts(
    customer_id: UUID,
    is_active: bool | None = None,
) -> list[CustomerContactResponse]:
    try:
        contacts = customer_service.list_customer_contacts(customer_id, is_active)
    except customer_service.CustomerNotFoundError as exc:
        _raise_not_found(exc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not list contacts") from exc

    return [CustomerContactResponse(**contact) for contact in contacts]


@router.post(
    "/customers/{customer_id}/contacts",
    response_model=CustomerContactResponse,
    status_code=201,
)
def create_customer_contact(
    customer_id: UUID,
    payload: CustomerContactCreate,
) -> CustomerContactResponse:
    try:
        contact = customer_service.create_customer_contact(customer_id, payload)
    except customer_service.CustomerNotFoundError as exc:
        _raise_not_found(exc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not create contact") from exc

    return CustomerContactResponse(**contact)


@router.put(
    "/customer-contacts/{contact_id}",
    response_model=CustomerContactResponse,
)
def update_customer_contact(
    contact_id: UUID,
    payload: CustomerContactUpdate,
) -> CustomerContactResponse:
    try:
        contact = customer_service.update_customer_contact(contact_id, payload)
    except customer_service.ContactNotFoundError as exc:
        _raise_not_found(exc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not update contact") from exc

    return CustomerContactResponse(**contact)


@router.delete(
    "/customer-contacts/{contact_id}",
    response_model=CustomerContactResponse,
)
def delete_customer_contact(contact_id: UUID) -> CustomerContactResponse:
    try:
        contact = customer_service.soft_delete_customer_contact(contact_id)
    except customer_service.ContactNotFoundError as exc:
        _raise_not_found(exc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not delete contact") from exc

    return CustomerContactResponse(**contact)
