from datetime import datetime
from uuid import UUID
from pydantic import BaseModel,Field

class ActiveAssignmentResponse(BaseModel):
    instructor_id:UUID; instructor_name:str; instructor_city:str|None=None; assigned_at:datetime
class BookingActivityAssignmentResponse(BaseModel):
    booking_activity_id:UUID; activity_id:UUID; activity_name:str; assignment_required:bool; assignments:list[ActiveAssignmentResponse]=Field(default_factory=list)
class BookingAssignmentsResponse(BaseModel):
    booking_id:UUID; version:int; activities:list[BookingActivityAssignmentResponse]
class OpenEventActivityResponse(BaseModel):
    booking_activity_id:UUID; activity_id:UUID; activity_name:str; assignment_required:bool
class OpenEventDetailResponse(BaseModel):
    booking_id:UUID; event_at:datetime; city:str|None=None; venue:str|None=None; status:str; requires_instructor:bool; version:int; activities:list[OpenEventActivityResponse]
