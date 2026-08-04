from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ActiveAssignmentResponse(BaseModel):
    instructor_id: UUID
    instructor_name: str
    instructor_city: str | None = None
    assigned_at: datetime


class AssignmentRequestResponse(BaseModel):
    request_id: UUID
    booking_activity_id: UUID
    instructor_id: UUID
    instructor_name: str | None = None
    instructor_city: str | None = None
    status: str
    requested_at: datetime


class AssignmentDecisionRequest(BaseModel):
    expected_version: int = Field(ge=1)


class BookingActivityAssignmentResponse(BaseModel):
    booking_activity_id: UUID
    activity_id: UUID
    activity_name: str
    assignment_required: bool
    assignments: list[ActiveAssignmentResponse] = Field(default_factory=list)
    requests: list[AssignmentRequestResponse] = Field(default_factory=list)


class BookingAssignmentsResponse(BaseModel):
    booking_id: UUID
    version: int
    activities: list[BookingActivityAssignmentResponse]


class OpenEventActivityResponse(BaseModel):
    booking_activity_id: UUID
    activity_id: UUID
    activity_name: str
    assignment_required: bool
    my_request_id: UUID | None = None
    my_request_status: str | None = None


class OpenEventDetailResponse(BaseModel):
    booking_id: UUID
    event_at: datetime
    city: str | None = None
    venue: str | None = None
    status: str
    requires_instructor: bool
    version: int
    customer_name: str | None = None
    customer_contact_name: str | None = None
    customer_phone: str | None = None
    activities: list[OpenEventActivityResponse]
