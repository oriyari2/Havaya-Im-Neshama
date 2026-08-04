from __future__ import annotations

from typing import Annotated, NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from backend.app.application.services import customer_service
from backend.app.application.services import user_admin_service
from backend.app.core.auth import get_current_user, require_roles
from backend.app.schemas.customer import (
    CustomerContactCreate,
    CustomerContactResponse,
    CustomerContactUpdate,
    CustomerCreate,
    CustomerListResponse,
    CustomerResponse,
    CustomerSelfUpdate,
    CustomerUpdate,
)
from backend.app.schemas.user_admin import PasswordResetRequest


router = APIRouter(tags=["customers"])
RequireManager = Depends(require_roles("manager"))


def _customer_response(customer: dict, contacts: list[dict] | None = None) -> CustomerResponse:
    return CustomerResponse(**customer, contacts=contacts or [])


def _raise_not_found(exc: Exception) -> NoReturn:
    if isinstance(exc, customer_service.CustomerNotFoundError):
        raise HTTPException(status_code=404, detail="Customer not found") from exc
    if isinstance(exc, customer_service.ContactNotFoundError):
        raise HTTPException(status_code=404, detail="Contact not found") from exc
    raise exc


def _raise_access_denied(exc: Exception) -> NoReturn:
    if isinstance(exc, customer_service.CustomerAccessDeniedError):
        raise HTTPException(status_code=403, detail="Not authorized") from exc
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
    current_user: dict = Depends(get_current_user),
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
            current_user=current_user,
        )
    except customer_service.CustomerAccessDeniedError as exc:
        _raise_access_denied(exc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not list customers") from exc

    return CustomerListResponse(
        items=[_customer_response(customer) for customer in customers],
        count=len(customers),
    )


@router.put("/customers/me", response_model=CustomerResponse)
def update_my_profile(
    payload: CustomerSelfUpdate,
    current_user: dict = Depends(get_current_user),
) -> CustomerResponse:
    try:
        customer, contacts = customer_service.update_my_profile(payload, current_user)
    except customer_service.CustomerAccessDeniedError as exc:
        _raise_access_denied(exc)
    except customer_service.CustomerNotFoundError as exc:
        _raise_not_found(exc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not update customer profile") from exc
    return _customer_response(customer, contacts)


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: UUID,
    current_user: dict = Depends(get_current_user),
) -> CustomerResponse:
    try:
        customer, contacts = customer_service.get_customer_for_user(customer_id, current_user)
    except (customer_service.CustomerNotFoundError, customer_service.ContactNotFoundError) as exc:
        _raise_not_found(exc)
    except customer_service.CustomerAccessDeniedError as exc:
        _raise_access_denied(exc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not get customer") from exc

    return _customer_response(customer, contacts)


@router.post("/customers", response_model=CustomerResponse, status_code=201)
def create_customer(payload: CustomerCreate, _current_user: dict = RequireManager) -> CustomerResponse:
    try:
        customer, contacts = customer_service.create_customer(payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not create customer") from exc

    return _customer_response(customer, contacts)


@router.put("/customers/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: UUID,
    payload: CustomerUpdate,
    _current_user: dict = RequireManager,
) -> CustomerResponse:
    try:
        customer, contacts = customer_service.update_customer(customer_id, payload)
    except customer_service.CustomerNotFoundError as exc:
        _raise_not_found(exc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not update customer") from exc

    return _customer_response(customer, contacts)


@router.delete(
    "/customers/{customer_id}",
    status_code=204,
    responses={404: {"description": "Customer not found"}, 409: {"description": "Protected dependencies prevent deletion"}},
)
def delete_customer(customer_id: UUID, _current_user: dict = RequireManager) -> Response:
    try:
        customer_service.delete_customer(customer_id)
    except customer_service.CustomerNotFoundError as exc:
        _raise_not_found(exc)
    except customer_service.CustomerDeleteConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not delete customer") from exc
    return Response(status_code=204)


@router.post("/customers/{customer_id}/reset-password", status_code=204)
def reset_customer_password(
    customer_id: UUID,
    payload: PasswordResetRequest,
    _current_user: dict = RequireManager,
) -> Response:
    try:
        user_admin_service.reset_profile_password("customer", customer_id, payload)
    except user_admin_service.UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Customer account not found") from exc
    return Response(status_code=204)


@router.post("/customers/{customer_id}/activate", response_model=CustomerResponse)
def activate_customer(customer_id: UUID, _current_user: dict = RequireManager) -> CustomerResponse:
    try:
        customer = user_admin_service.set_profile_active("customer", customer_id, True)
        _, contacts = customer_service.get_customer(customer_id)
        return _customer_response(customer, contacts)
    except user_admin_service.UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Customer account not found") from exc
    except user_admin_service.UserConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/customers/{customer_id}/deactivate", response_model=CustomerResponse)
def deactivate_customer(customer_id: UUID, _current_user: dict = RequireManager) -> CustomerResponse:
    try:
        customer = user_admin_service.set_profile_active("customer", customer_id, False)
        _, contacts = customer_service.get_customer(customer_id)
        return _customer_response(customer, contacts)
    except user_admin_service.UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Customer account not found") from exc
    except user_admin_service.UserConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get(
    "/customers/{customer_id}/contacts",
    response_model=list[CustomerContactResponse],
)
def list_customer_contacts(
    customer_id: UUID,
    is_active: bool | None = None,
    current_user: dict = Depends(get_current_user),
) -> list[CustomerContactResponse]:
    try:
        contacts = customer_service.list_customer_contacts_for_user(customer_id, is_active, current_user)
    except customer_service.CustomerNotFoundError as exc:
        _raise_not_found(exc)
    except customer_service.CustomerAccessDeniedError as exc:
        _raise_access_denied(exc)
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
    _current_user: dict = RequireManager,
) -> CustomerContactResponse:
    try:
        contact = customer_service.create_customer_contact(customer_id, payload)
    except customer_service.CustomerNotFoundError as exc:
        _raise_not_found(exc)
    except customer_service.ContactConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
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
    _current_user: dict = RequireManager,
) -> CustomerContactResponse:
    try:
        contact = customer_service.update_customer_contact(contact_id, payload)
    except customer_service.ContactNotFoundError as exc:
        _raise_not_found(exc)
    except customer_service.ContactConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not update contact") from exc

    return CustomerContactResponse(**contact)


@router.delete(
    "/customer-contacts/{contact_id}",
    response_model=CustomerContactResponse,
)
def delete_customer_contact(
    contact_id: UUID,
    _current_user: dict = RequireManager,
) -> CustomerContactResponse:
    try:
        contact = customer_service.soft_delete_customer_contact(contact_id)
    except customer_service.ContactNotFoundError as exc:
        _raise_not_found(exc)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not delete contact") from exc

    return CustomerContactResponse(**contact)
