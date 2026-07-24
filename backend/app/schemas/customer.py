from __future__ import annotations

from datetime import datetime
import re
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _validate_required_text(value: str, field_name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{field_name} must not be empty")
    return cleaned


def _validate_email(value: str | None) -> str | None:
    cleaned = _clean_optional_text(value)
    if cleaned is not None and not EMAIL_PATTERN.match(cleaned):
        raise ValueError("email must be a valid email address")
    return cleaned


class CustomerBase(BaseModel):
    customer_type: str | None = None
    city: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    notes: str | None = None
    is_active: bool = True

    @field_validator("customer_type", "city", "address", "phone", "notes")
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        return _clean_optional_text(value)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        return _validate_email(value)


class CustomerCreate(CustomerBase):
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _validate_required_text(value, "name")


class CustomerUpdate(BaseModel):
    name: str | None = None
    customer_type: str | None = None
    city: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    notes: str | None = None
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _validate_required_text(value, "name")

    @field_validator("customer_type", "city", "address", "phone", "notes")
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        return _clean_optional_text(value)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        return _validate_email(value)


class CustomerContactBase(BaseModel):
    role_title: str | None = None
    phone: str | None = None
    email: str | None = None
    is_primary: bool = False
    notes: str | None = None
    is_active: bool = True

    @field_validator("role_title", "phone", "notes")
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        return _clean_optional_text(value)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        return _validate_email(value)


class CustomerContactCreate(CustomerContactBase):
    full_name: str

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str) -> str:
        return _validate_required_text(value, "full_name")


class CustomerContactUpdate(BaseModel):
    full_name: str | None = None
    role_title: str | None = None
    phone: str | None = None
    email: str | None = None
    is_primary: bool | None = None
    notes: str | None = None
    is_active: bool | None = None

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _validate_required_text(value, "full_name")

    @field_validator("role_title", "phone", "notes")
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        return _clean_optional_text(value)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        return _validate_email(value)


class CustomerContactResponse(CustomerContactBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_id: UUID
    full_name: str
    created_at: datetime
    updated_at: datetime


class CustomerResponse(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    contacts: list[CustomerContactResponse] = Field(default_factory=list)


class CustomerListResponse(BaseModel):
    items: list[CustomerResponse]
    count: int
