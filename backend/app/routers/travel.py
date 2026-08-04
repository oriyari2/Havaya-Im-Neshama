from __future__ import annotations

from typing import NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from backend.app.application.bookings import assignment_query_handlers, query_handlers
from backend.app.application.gateways.route_gateway import RouteGateway
from backend.app.application.services import booking_travel_service, instructor_service
from backend.app.core.auth import require_roles
from backend.app.infrastructure.gateways.providers import get_route_gateway
from backend.app.schemas.travel import BookingTravelEstimateResponse


router = APIRouter(tags=["travel"])
RequireTravelUser = Depends(require_roles("manager", "instructor"))


def _raise_booking_error(exc: Exception) -> NoReturn:
    if isinstance(exc, query_handlers.BookingNotFoundError):
        raise HTTPException(status_code=404, detail="Booking not found") from exc
    if isinstance(exc, query_handlers.BookingAccessDeniedError):
        raise HTTPException(status_code=403, detail="Not authorized") from exc
    raise exc


@router.get(
    "/bookings/{booking_id}/travel-estimate",
    response_model=BookingTravelEstimateResponse,
)
def get_booking_travel_estimate(
    booking_id: UUID,
    current_user: dict = RequireTravelUser,
    gateway: RouteGateway = Depends(get_route_gateway),
) -> BookingTravelEstimateResponse:
    try:
        origin_address = None
        if current_user.get("role") == "instructor":
            profile = instructor_service.get_my_profile(current_user)
            city = str(profile.get("city") or "").strip()
            if not city:
                raise booking_travel_service.TravelEstimateValidationError(
                    "Instructor city is missing"
                )
            origin_address = city if "ישראל" in city or "israel" in city.casefold() else f"{city}, ישראל"
            try:
                booking = query_handlers.get_booking(booking_id, current_user)
            except query_handlers.BookingAccessDeniedError:
                # Instructors may also calculate travel for a currently-open
                # event that they are considering before requesting assignment.
                booking = assignment_query_handlers.get_open_event_detail(booking_id, current_user)
        else:
            booking = query_handlers.get_booking(booking_id, current_user)
        estimate = booking_travel_service.estimate_booking_travel(
            booking, gateway, origin_address=origin_address
        )
    except (query_handlers.BookingNotFoundError, query_handlers.BookingAccessDeniedError) as exc:
        _raise_booking_error(exc)
    except instructor_service.InstructorAccessDeniedError as exc:
        raise HTTPException(status_code=403, detail="Not authorized") from exc
    except instructor_service.InstructorNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Instructor profile not found") from exc
    except booking_travel_service.TravelEstimateValidationError as exc:
        detail = (
            "לא ניתן לחשב מסלול. יש לעדכן עיר בפרופיל המדריך ולוודא שבהזמנה קיימים עיר ומקום מלאים."
            if str(exc) == "Instructor city is missing"
            else "לא ניתן לחשב מסלול. יש לוודא שבהזמנה קיימים עיר ומקום מלאים."
        )
        raise HTTPException(status_code=422, detail=detail) from exc
    except booking_travel_service.TravelEstimateConfigurationError as exc:
        raise HTTPException(status_code=503, detail="Travel service is not configured") from exc
    except booking_travel_service.TravelEstimateProviderError as exc:
        raise HTTPException(status_code=502, detail="Travel service is unavailable") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Could not calculate travel estimate") from exc

    return BookingTravelEstimateResponse(**estimate)
