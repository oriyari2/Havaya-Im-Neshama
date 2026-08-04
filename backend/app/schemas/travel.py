from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class BookingTravelEstimateResponse(BaseModel):
    booking_id: UUID
    origin_address: str
    origin_resolved_address: str
    destination_address: str
    destination_resolved_address: str
    distance_km: float = Field(ge=0)
    duration_minutes: int = Field(ge=1)
    provider: str
    uses_live_traffic: bool = False
