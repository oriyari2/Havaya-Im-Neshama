from __future__ import annotations

from typing import Annotated, NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.application.bookings import command_handlers, query_handlers
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
    ExpectedVersionRequest,
)


router = APIRouter(tags=["bookings"])
RequireManager = Depends(require_roles("manager"))


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
    raise exc


@router.post("/bookings", response_model=BookingResponse, status_code=201)
def create_booking(payload: BookingCreate, current_user: dict = RequireManager) -> BookingResponse:
    try:
        booking = command_handlers.create_booking(
            CreateBookingCommand(actor_user_id=current_user["id"], **payload.model_dump())
        )
    except Exception as exc:
        _raise_command_error(exc)
    return BookingResponse(**booking)


@router.get("/bookings", response_model=BookingListResponse)
def list_bookings(
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    current_user: dict = Depends(get_current_user),
) -> BookingListResponse:
    try:
        bookings = query_handlers.list_bookings(current_user, status, limit, offset)
    except Exception as exc:
        _raise_query_error(exc)
    return BookingListResponse(items=[BookingResponse(**booking) for booking in bookings], count=len(bookings))


@router.get("/bookings/{booking_id}", response_model=BookingResponse)
def get_booking(booking_id: UUID, current_user: dict = Depends(get_current_user)) -> BookingResponse:
    try:
        booking = query_handlers.get_booking(booking_id, current_user)
    except Exception as exc:
        _raise_query_error(exc)
    return BookingResponse(**booking)


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
