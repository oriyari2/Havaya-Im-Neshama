# Task 08 - Booking Event Sourcing and CQRS Core

## What Was Created

Implemented the backend booking command/query core for the academic MVP.

- `booking_events` append-only event store for booking domain events.
- `bookings` read projection fields for current booking state.
- Booking aggregate replay logic under `backend/app/domain/bookings`.
- Booking command handlers that append immutable events and update projections.
- Booking query handlers that read projections and chronological history.
- Role-aware booking read authorization for managers, customers, and instructors. Customers can only access their own bookings, while instructors can access bookings only when they are an active assignment on the booking activity.
- Booking activity instructor assignment/removal events, commands, handlers, API endpoints, and current-assignment projection sync. Instructor reassignment after removal reactivates the projection row, clears `removed_at`, and resets `assigned_at` to the latest assignment time.
- FastAPI booking routes for create, list, detail, history, supported updates, instructor assignment/removal, and replay.
- Focused automated tests for replay, booking-activity instructor assignment/removal/reassignment events, booking-activity ownership validation on removal, projection reassignment SQL, active instructor reconstruction, terminal status rules, stale version conflicts, and role-based read authorization.

Event Sourcing applies to bookings only. Activity images remain regular Cloudinary Gateway metadata from Task 07.

Task 08 booking code uses `event_at` for booking dates. The older `event_date` column remains only as a legacy field from Task 02/schema seed compatibility and is not used by the Task 08 command/query code. The stale `idx_bookings_event_date` initialization index was removed; `idx_bookings_event_at` is the active Task 08 date index.

## PRD Requirements Advanced

- `FR-BKG-01`: manager booking creation appends `BookingCreated` and creates a projection.
- `FR-BKG-02`: supported statuses are `NEW`, `CONFIRMED`, `COMPLETED`, and `CANCELLED`; terminal transition rules are enforced.
- `FR-BKG-03`: supported booking updates append specific immutable events.
- `FR-BKG-04`: booking history is returned chronologically from event rows.
- `FR-BKG-05`: booking state can be reconstructed by replaying ordered events.
- `FR-BKG-06`: update commands require `expected_version`; stale versions return conflict.
- `FR-INS-04`: manager instructor assignment/removal is scoped to a booking activity, appends `BookingInstructorAssigned` and `BookingInstructorRemoved` events, and updates the current instructor projection.
- Booking read authorization now enforces role-specific visibility: managers see all bookings, customers see only their own bookings, and instructors see only bookings where they are an active assignment.

## Files Changed

- `backend/app/db/schema.py`
- `backend/app/main.py`
- `backend/app/domain/bookings/aggregate.py`
- `backend/app/domain/bookings/events.py`
- `backend/app/domain/bookings/status.py`
- `backend/app/application/bookings/commands.py`
- `backend/app/application/bookings/command_handlers.py`
- `backend/app/application/bookings/query_handlers.py`
- `backend/app/infrastructure/repositories/booking_event_repository.py`
- `backend/app/infrastructure/repositories/booking_projection_repository.py`
- `backend/app/schemas/booking.py`
- `backend/app/routers/bookings.py`
- `backend/tests/test_booking_event_sourcing.py`
- `docs/piv/requirements-traceability.md`

## How To Run

Initialize or update the configured PostgreSQL/Supabase database through the existing system initialization flow, then start the FastAPI app as before.

Manager booking commands:

- `POST /bookings`
- `PATCH /bookings/{booking_id}/status`
- `PATCH /bookings/{booking_id}/schedule`
- `PATCH /bookings/{booking_id}/price`
- `PATCH /bookings/{booking_id}/location`
- `PATCH /bookings/{booking_id}/participant-count`
- `PATCH /bookings/{booking_id}/notes`
- `POST /bookings/{booking_id}/instructors`
- `DELETE /bookings/{booking_id}/activities/{booking_activity_id}/instructors/{instructor_id}`

Read/replay endpoints:

- `GET /bookings`
- `GET /bookings/{booking_id}`
- `GET /bookings/{booking_id}/history`
- `POST /bookings/{booking_id}/replay`

## Validation

Automated validation:

```powershell
.\.venv\Scripts\python.exe -m compileall backend desktop_client
.\.venv\Scripts\python.exe -m unittest backend.tests.test_booking_event_sourcing
```

Actual results on 2026-07-27:

- `compileall backend desktop_client`: passed.
- `unittest backend.tests.test_booking_event_sourcing`: passed, 16 tests.

Manual API validation should use a manager token:

1. Create a booking with active customer and activity ids.
2. Confirm `BookingCreated` appears in `/bookings/{id}/history`.
3. Assign an active instructor to a `booking_activity_id` with the current `expected_version`.
4. Remove the instructor from the same booking activity with the new current `expected_version`.
5. Assign the same instructor to the same booking activity again and confirm the current-state projection is active.
6. Confirm `BookingInstructorAssigned`, `BookingInstructorRemoved`, and `BookingInstructorAssigned` appear chronologically in `/bookings/{id}/history`.
7. Repeat a mutation with the old version and confirm `409`.
8. Replay the booking and compare it with the projection.

## Out Of Scope

No desktop screens, dashboard, RAG, activity event sourcing, or image event sourcing were added.

## Next Task

Task 09 should add richer booking queries, booking history summaries, instructor visibility rules, and dashboard counts.
