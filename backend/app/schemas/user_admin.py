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
    customer_id: UUID | None = None
    instructor_id: UUID | None = None

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
        valid = (
            self.role == "manager" and self.customer_id is None and self.instructor_id is None
        ) or (
            self.role == "customer" and self.customer_id is not None and self.instructor_id is None
        ) or (
            self.role == "instructor" and self.customer_id is None and self.instructor_id is not None
        )
        if not valid:
            raise ValueError("role and profile link do not match")
        return self


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
    is_active: bool
    customer_id: UUID | None = None
    customer_name: str | None = None
    instructor_id: UUID | None = None
    instructor_name: str | None = None
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    items: list[UserResponse]
    count: int = Field(ge=0)


class EligibleCustomerProfile(BaseModel):
    id: UUID
    name: str


class EligibleInstructorProfile(BaseModel):
    id: UUID
    full_name: str


class EligibleProfilesResponse(BaseModel):
    customers: list[EligibleCustomerProfile]
    instructors: list[EligibleInstructorProfile]
