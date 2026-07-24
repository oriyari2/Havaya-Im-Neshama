from __future__ import annotations

from datetime import datetime
import re
from uuid import UUID

from pydantic import BaseModel, field_validator


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not EMAIL_PATTERN.match(cleaned):
            raise ValueError("email must be a valid email address")
        return cleaned


class UserResponse(BaseModel):
    id: UUID
    email: str
    role: str
    is_active: bool
    customer_id: UUID | None = None
    instructor_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
