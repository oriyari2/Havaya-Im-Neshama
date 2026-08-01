from __future__ import annotations

from datetime import datetime
import re
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
UserRole = Literal["manager", "instructor", "customer"]


def normalize_email(value: str) -> str:
    cleaned = value.strip().lower()
    if len(cleaned) > 254 or not EMAIL_PATTERN.match(cleaned):
        raise ValueError("email must be a valid email address")
    return cleaned


def validate_password(value: str) -> str:
    if not 8 <= len(value) <= 128:
        raise ValueError("password must contain between 8 and 128 characters")
    if value != value.strip() or any(not character.isprintable() for character in value):
        raise ValueError("password contains unsupported whitespace or control characters")
    return value


class UserCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str
    password: str
    role: UserRole
    manager_name: str | None = None
    customer_name: str | None = None
    customer_type: str | None = None
    customer_city: str | None = None
    customer_address: str | None = None
    customer_phone: str | None = None
    customer_notes: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    instructor_name: str | None = None
    instructor_phone: str | None = None
    instructor_city: str | None = None
    instructor_notes: str | None = None

    @field_validator("email")
    @classmethod
    def email_valid(cls, value: str) -> str:
        return normalize_email(value)

    @field_validator("password")
    @classmethod
    def password_valid(cls, value: str) -> str:
        return validate_password(value)

    @model_validator(mode="after")
    def role_profile_valid(self) -> "UserCreateRequest":
        customer_values = (self.customer_name, self.customer_type, self.customer_city, self.customer_address, self.customer_phone, self.customer_notes, self.contact_name, self.contact_phone)
        instructor_values = (self.instructor_name, self.instructor_phone, self.instructor_city, self.instructor_notes)
        contact_valid = bool(self.contact_name) == bool(self.contact_phone)
        valid = self.role == "manager" and bool(self.manager_name) and not any(customer_values + instructor_values)
        valid = valid or self.role == "customer" and not self.manager_name and bool(self.customer_name) and contact_valid and not any(instructor_values)
        valid = valid or self.role == "instructor" and not self.manager_name and bool(self.instructor_name) and not any(customer_values)
        if not valid:
            raise ValueError("role and new profile fields do not match")
        return self

    @field_validator("manager_name", "customer_name", "customer_type", "customer_city", "customer_address", "customer_phone", "customer_notes", "contact_name", "contact_phone", "instructor_name", "instructor_phone", "instructor_city", "instructor_notes")
    @classmethod
    def profile_text_valid(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class UserEmailUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str

    @field_validator("email")
    @classmethod
    def email_valid(cls, value: str) -> str:
        return normalize_email(value)


class PasswordResetRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_valid(cls, value: str) -> str:
        return validate_password(value)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: str
    role: UserRole
    display_name: str | None = None
    is_active: bool
    customer_id: UUID | None = None
    customer_name: str | None = None
    customer_email: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    instructor_id: UUID | None = None
    instructor_name: str | None = None
    instructor_email: str | None = None
    instructor_phone: str | None = None
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    items: list[UserResponse]
    count: int = Field(ge=0)
