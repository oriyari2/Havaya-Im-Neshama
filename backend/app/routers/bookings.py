from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.application.bookings import command_handlers, query_handlers
from backend.app.application.bookings import assignment_query_handlers, assignment_request_handlers
from backend.app.application.bookings.commands import (
    ChangeDateCommand,
    ChangeLocationCommand,
    ChangeParticipantCountCommand,
    ChangePriceCommand,
    ChangeStatusCommand,
    AssignInstructorCommand,
    CreateBookingCommand,
    RemoveInstructorCommand,
    UpdateNotesCommand,
)
from backend.app.core.auth import get_current_user, require_roles
from backend.app.schemas.booking import (
    BookingCreate,
    BookingDateChange,
    BookingEventResponse,
    BookingInstructorAssignment,
    BookingListResponse,
    BookingLocationChange,
    BookingNotesUpdate,
    BookingParticipantCountChange,
    BookingPriceChange,
    BookingResponse,
    BookingStatusChange,
    CustomerBookingSummaryListResponse,
    CustomerBookingSummaryResponse,
    DashboardSummaryResponse,
    ExpectedVersionRequest,
    InstructorBookingListResponse,
    InstructorBookingResponse,
    OpenEventResponse,
)
from backend.app.schemas.booking_assignment import (
    AssignmentDecisionRequest,
    AssignmentRequestResponse,
    BookingAssignmentsResponse,
    OpenEventDetailResponse,
)


router = APIRouter(tags=["bookings"])
RequireManager = Depends(require_roles("manager"))
RequireBookingCreator = Depends(require_roles("manager", "customer"))


def _raise_command_error(exc: Exception) -> NoReturn:
    if isinstance(exc, command_handlers.BookingNotFoundError):
        raise HTTPException(status_code=404, detail="Booking not found") from exc
    if isinstance(exc, command_handlers.BookingConcurrencyError):
        raise HTTPException(status_code=409, detail="Booking version conflict") from exc
    if isinstance(exc, command_handlers.BookingValidationError):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    raise exc


def _raise_query_error(exc: Exception) -> NoReturn:
    if isinstance(exc, query_handlers.BookingNotFoundError):
        raise HTTPException(status_code=404, detail="Booking not found") from exc
    if isinstance(exc, query_handlers.BookingAccessDeniedError):
        raise HTTPException(status_code=403, detail="Not authorized") from exc
    if isinstance(exc, query_handlers.BookingValidationError):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    raise exc


def _raise_assignment_request_error(exc: Exception) -> NoReturn:
    if isinstance(exc, assignment_request_handlers.AssignmentRequestConflictError):
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if isinstance(exc, command_handlers.BookingConcurrencyError):
        raise HTTPException(status_code=409, detail="Booking version conflict") from exc
    if isinstance(exc, command_handlers.BookingValidationError):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    _raise_query_error(exc)


@router.post("/bookings", response_model=BookingResponse, status_code=201)
def create_booking(payload: BookingCreate, current_user: dict = RequireBookingCreator) -> BookingResponse:
    try:
        data = payload.model_dump()
        if current_user["role"] == "customer":
            owned_customer_id = current_user.get("customer_id")
            if owned_customer_id is None:
                raise HTTPException(status_code=403, detail="Customer account is not linked")
            if payload.customer_id is not None and payload.customer_id != owned_customer_id:
                raise HTTPException(status_code=403, detail="Cannot create a booking for another customer")
            data.update(
                customer_id=owned_customer_id,
                agreed_price=0,
                status="NEW",
                requires_instructor=False,
            )
        elif payload.customer_id is None:
            raise HTTPException(status_code=422, detail="customer_id is required for managers")
        booking = command_handlers.create_booking(
            CreateBookingCommand(actor_user_id=current_user["id"], **data)
        )
    except Exception as exc:
        _raise_command_error(exc)
    return BookingResponse(**booking)


@router.get(
    "/bookings",
    response_model=BookingListResponse | InstructorBookingListResponse,
    description="Returns full booking fields to managers/customers and an operational, commercial-field-safe view to instructors.",
)
def list_bookings(
    status: Annotated[list[str] | None, Query()] = None,
    customer_id: UUID | None = None,
    activity_id: Annotated[list[UUID] | None, Query()] = None,
    instructor_id: Annotated[list[UUID] | None, Query()] = None,
    assignment_state: Annotated[list[Literal["assigned", "unassigned"]] | None, Query()] = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    order_by: Literal["event_at", "event_at_desc", "customer_name"] = "event_at",
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    current_user: dict = Depends(get_current_user),
) -> BookingListResponse | InstructorBookingListResponse:
    try:
        bookings = query_handlers.list_bookings(
            current_user,
            status,
            limit,
            offset,
            customer_id=customer_id,
            activity_id=activity_id,
            instructor_id=instructor_id,
            assignment_state=assignment_state,
            from_date=from_date,
            to_date=to_date,
            order_by=order_by,
        )
    except Exception as exc:
        _raise_query_error(exc)
    if current_user["role"] == "instructor":
        return InstructorBookingListResponse(
            items=[InstructorBookingResponse(**booking) for booking in bookings],
            count=len(bookings),
        )
    return BookingListResponse(
        items=[BookingResponse(**booking) for booking in bookings],
        count=len(bookings),
    )


@router.get("/bookings/dashboard", response_model=DashboardSummaryResponse)
def get_dashboard_summary(current_user: dict = Depends(get_current_user)) -> DashboardSummaryResponse:
    try:
        summary = query_handlers.get_dashboard_summary(current_user)
    except Exception as exc:
        _raise_query_error(exc)
    return DashboardSummaryResponse(**summary)


@router.get("/bookings/open-events", response_model=list[OpenEventResponse])
def get_open_events(current_user: dict = Depends(get_current_user)) -> list[OpenEventResponse]:
    try:
        bookings = query_handlers.get_open_events(current_user)
    except Exception as exc:
        _raise_query_error(exc)
    return [OpenEventResponse(**booking) for booking in bookings]

@router.get("/bookings/open-events/{booking_id}",response_model=OpenEventDetailResponse)
def get_open_event_detail(booking_id:UUID,current_user:dict=Depends(get_current_user)):
    try:return OpenEventDetailResponse(**assignment_query_handlers.get_open_event_detail(booking_id,current_user))
    except Exception as exc:_raise_query_error(exc)


@router.get(
    "/bookings/my-bookings",
    response_model=CustomerBookingSummaryListResponse,
    description="Returns a compact list containing only the signed-in customer's bookings.",
)
def get_my_bookings(
    order_by: Literal["event_at", "event_at_desc", "customer_name"] = "event_at",
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    current_user: dict = Depends(get_current_user),
) -> CustomerBookingSummaryListResponse:
    try:
        bookings = query_handlers.get_my_bookings(current_user, limit, offset, order_by=order_by)
    except Exception as exc:
        _raise_query_error(exc)
    return CustomerBookingSummaryListResponse(
        items=[CustomerBookingSummaryResponse(**booking) for booking in bookings],
        count=len(bookings),
    )


@router.get(
    "/bookings/{booking_id}",
    response_model=BookingResponse | InstructorBookingResponse,
    description="Returns full booking fields to managers/customers and an operational, commercial-field-safe view to instructors.",
)
def get_booking(
    booking_id: UUID,
    current_user: dict = Depends(get_current_user),
) -> BookingResponse | InstructorBookingResponse:
    try:
        booking = query_handlers.get_booking(booking_id, current_user)
    except Exception as exc:
        _raise_query_error(exc)
    if current_user["role"] == "instructor":
        return InstructorBookingResponse(**booking)
    return BookingResponse(**booking)

@router.get("/bookings/{booking_id}/assignments",response_model=BookingAssignmentsResponse)
def get_booking_assignments(booking_id:UUID,current_user:dict=Depends(get_current_user)):
    try:return BookingAssignmentsResponse(**assignment_query_handlers.get_assignments(booking_id,current_user))
    except Exception as exc:_raise_query_error(exc)


@router.post(
    "/bookings/{booking_id}/activities/{booking_activity_id}/assignment-requests",
    response_model=AssignmentRequestResponse,
    status_code=201,
)
def request_assignment(
    booking_id: UUID,
    booking_activity_id: UUID,
    current_user: dict = Depends(get_current_user),
) -> AssignmentRequestResponse:
    try:
        request = assignment_request_handlers.request_assignment(booking_id, booking_activity_id, current_user)
    except Exception as exc:
        _raise_assignment_request_error(exc)
    return AssignmentRequestResponse(**request)


@router.post(
    "/bookings/{booking_id}/assignment-requests/{request_id}/approve",
    response_model=BookingResponse,
)
def approve_assignment_request(
    booking_id: UUID,
    request_id: UUID,
    payload: AssignmentDecisionRequest,
    current_user: dict = RequireManager,
) -> BookingResponse:
    try:
        booking = assignment_request_handlers.approve_request(
            booking_id, request_id, payload.expected_version, current_user
        )
    except Exception as exc:
        _raise_assignment_request_error(exc)
    return BookingResponse(**booking)


@router.post(
    "/bookings/{booking_id}/assignment-requests/{request_id}/reject",
    response_model=AssignmentRequestResponse,
)
def reject_assignment_request(
    booking_id: UUID,
    request_id: UUID,
    current_user: dict = RequireManager,
) -> AssignmentRequestResponse:
    try:
        request = assignment_request_handlers.reject_request(booking_id, request_id, current_user)
    except Exception as exc:
        _raise_assignment_request_error(exc)
    return AssignmentRequestResponse(**request)


@router.get("/bookings/{booking_id}/history", response_model=list[BookingEventResponse])
def get_booking_history(booking_id: UUID, current_user: dict = Depends(get_current_user)) -> list[BookingEventResponse]:
    try:
        events = query_handlers.get_history(booking_id, current_user)
    except Exception as exc:
        _raise_query_error(exc)
    return [BookingEventResponse(**event) for event in events]


@router.patch("/bookings/{booking_id}/status", response_model=BookingResponse)
def change_status(
    booking_id: UUID,
    payload: BookingStatusChange,
    current_user: dict = RequireManager,
) -> BookingResponse:
    try:
        booking = command_handlers.change_status(
            ChangeStatusCommand(booking_id=booking_id, actor_user_id=current_user["id"], **payload.model_dump())
        )
    except Exception as exc:
        _raise_command_error(exc)
    return BookingResponse(**booking)


@router.patch("/bookings/{booking_id}/schedule", response_model=BookingResponse)
def change_schedule(
    booking_id: UUID,
    payload: BookingDateChange,
    current_user: dict = RequireManager,
) -> BookingResponse:
    try:
        booking = command_handlers.change_date(
            ChangeDateCommand(booking_id=booking_id, actor_user_id=current_user["id"], **payload.model_dump())
        )
    except Exception as exc:
        _raise_command_error(exc)
    return BookingResponse(**booking)


@router.patch("/bookings/{booking_id}/price", response_model=BookingResponse)
def change_price(
    booking_id: UUID,
    payload: BookingPriceChange,
    current_user: dict = RequireManager,
) -> BookingResponse:
    try:
        booking = command_handlers.change_price(
            ChangePriceCommand(booking_id=booking_id, actor_user_id=current_user["id"], **payload.model_dump())
        )
    except Exception as exc:
        _raise_command_error(exc)
    return BookingResponse(**booking)


@router.patch("/bookings/{booking_id}/location", response_model=BookingResponse)
def change_location(
    booking_id: UUID,
    payload: BookingLocationChange,
    current_user: dict = RequireManager,
) -> BookingResponse:
    try:
        booking = command_handlers.change_location(
            ChangeLocationCommand(booking_id=booking_id, actor_user_id=current_user["id"], **payload.model_dump())
        )
    except Exception as exc:
        _raise_command_error(exc)
    return BookingResponse(**booking)


@router.patch("/bookings/{booking_id}/participant-count", response_model=BookingResponse)
def change_participant_count(
    booking_id: UUID,
    payload: BookingParticipantCountChange,
    current_user: dict = RequireManager,
) -> BookingResponse:
    try:
        booking = command_handlers.change_participant_count(
            ChangeParticipantCountCommand(booking_id=booking_id, actor_user_id=current_user["id"], **payload.model_dump())
        )
    except Exception as exc:
        _raise_command_error(exc)
    return BookingResponse(**booking)


@router.patch("/bookings/{booking_id}/notes", response_model=BookingResponse)
def update_notes(
    booking_id: UUID,
    payload: BookingNotesUpdate,
    current_user: dict = RequireManager,
) -> BookingResponse:
    try:
        booking = command_handlers.update_notes(
            UpdateNotesCommand(booking_id=booking_id, actor_user_id=current_user["id"], **payload.model_dump())
        )
    except Exception as exc:
        _raise_command_error(exc)
    return BookingResponse(**booking)


@router.post("/bookings/{booking_id}/instructors", response_model=BookingResponse)
def assign_instructor(
    booking_id: UUID,
    payload: BookingInstructorAssignment,
    current_user: dict = RequireManager,
) -> BookingResponse:
    try:
        booking = command_handlers.assign_instructor(
            AssignInstructorCommand(booking_id=booking_id, actor_user_id=current_user["id"], **payload.model_dump())
        )
        assignment_request_handlers.resolve_after_assignment(
            payload.booking_activity_id, payload.instructor_id, current_user
        )
    except Exception as exc:
        _raise_command_error(exc)
    return BookingResponse(**booking)


@router.delete(
    "/bookings/{booking_id}/activities/{booking_activity_id}/instructors/{instructor_id}",
    response_model=BookingResponse,
)
def remove_instructor(
    booking_id: UUID,
    booking_activity_id: UUID,
    instructor_id: UUID,
    payload: ExpectedVersionRequest,
    current_user: dict = RequireManager,
) -> BookingResponse:
    try:
        booking = command_handlers.remove_instructor(
            RemoveInstructorCommand(
                booking_id=booking_id,
                booking_activity_id=booking_activity_id,
                instructor_id=instructor_id,
                actor_user_id=current_user["id"],
                **payload.model_dump(),
            )
        )
    except Exception as exc:
        _raise_command_error(exc)
    return BookingResponse(**booking)


@router.post("/bookings/{booking_id}/replay", response_model=BookingResponse)
def replay_booking(booking_id: UUID, current_user: dict = RequireManager) -> BookingResponse:
    try:
        booking = query_handlers.replay_booking(booking_id, current_user)
    except Exception as exc:
        _raise_query_error(exc)
    return BookingResponse(**booking)
