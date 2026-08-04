from __future__ import annotations

import re
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def clean(value: str | None) -> str | None:
    return value.strip() or None if value is not None else None

class InstructorBase(BaseModel):
    phone: str | None = None; email: str | None = None; city: str | None = None; notes: str | None = None; is_active: bool = True
    @field_validator("phone", "city", "notes")
    @classmethod
    def clean_text(cls, value): return clean(value)
    @field_validator("email")
    @classmethod
    def email_valid(cls, value):
        value = clean(value)
        if value and not EMAIL_PATTERN.match(value): raise ValueError("email must be a valid email address")
        return value.lower() if value else None

class InstructorCreate(InstructorBase):
    full_name: str
    @field_validator("full_name")
    @classmethod
    def name_required(cls, value):
        value=value.strip()
        if not value: raise ValueError("full_name must not be empty")
        return value

class InstructorUpdate(BaseModel):
    full_name: str | None=None; phone: str | None=None; email: str | None=None; city: str | None=None; notes: str | None=None; is_active: bool | None=None
    @field_validator("full_name")
    @classmethod
    def name_valid(cls,value):
        if value is None:return None
        value=value.strip()
        if not value:raise ValueError("full_name must not be empty")
        return value
    @field_validator("phone","city","notes")
    @classmethod
    def clean_text(cls,value):return clean(value)
    @field_validator("email")
    @classmethod
    def email_valid(cls,value):
        value=clean(value)
        if value and not EMAIL_PATTERN.match(value):raise ValueError("email must be a valid email address")
        return value.lower() if value else None


class InstructorSelfUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    city: str | None = None
    notes: str | None = None

    @field_validator("full_name")
    @classmethod
    def name_valid(cls, value):
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("full_name must not be empty")
        return value

    @field_validator("phone", "city", "notes")
    @classmethod
    def clean_text(cls, value):
        return clean(value)

class InstructorResponse(InstructorBase):
    model_config=ConfigDict(from_attributes=True)
    id: UUID; full_name: str; created_at: datetime; updated_at: datetime

class InstructorListResponse(BaseModel):
    items:list[InstructorResponse]; count:int
