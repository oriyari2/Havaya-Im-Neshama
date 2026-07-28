# Task 09 - Dashboard and Booking Queries

## What Was Created

This task adds a backend query slice for the booking projection introduced in Task 08.

It now exposes:

- manager-friendly booking list filtering by customer, activity, instructor, date range, and status
- dashboard-style summary counts for the signed-in role context at `GET /bookings/dashboard`
- instructor-facing eligible open-event queries that do not require an existing assignment
- a compact, customer-only booking summary at `GET /bookings/my-bookings`
- server-side authorization checks that keep customers scoped to their own bookings
- role-specific instructor serialization that excludes customer and commercial fields

The task remains backend-first and prepares the API surface for later desktop dashboard screens.

## PRD Requirements Advanced

This task supports:

- `FR-DASH-01` - managers can retrieve booking summary counts for upcoming work and status buckets.
- `FR-DASH-02` - instructors can query open and relevant future bookings through the same booking projection.
- `FR-DASH-03` - customers can retrieve only their own bookings without crossing into other customer data.
- `FR-BKG-07` - managers can filter bookings by date, status, customer, activity, and instructor.

## Scope

This task covers:

- role-aware booking list retrieval
- booking filtering for managers
- dashboard summary counts
- instructor-relevant open-event queries
- focused backend tests
- task documentation

## Files Changed

Backend files updated:

- `backend/app/application/bookings/query_handlers.py`
- `backend/app/infrastructure/repositories/booking_projection_repository.py`
- `backend/app/routers/bookings.py`
- `backend/app/schemas/booking.py`
- `backend/tests/test_booking_queries.py`

## How To Run

This task extends the existing FastAPI booking API.

Expected endpoints:

- `GET /bookings`
- `GET /bookings/dashboard`
- `GET /bookings/open-events`
- `GET /bookings/my-bookings`

Implemented dashboard response shape:

- `confirmed_count` counts upcoming `CONFIRMED` bookings.
- `pending_count` counts upcoming `NEW` bookings.
- `cancelled_count` counts upcoming `CANCELLED` bookings.
- `upcoming_count` counts every upcoming booking regardless of status, including `COMPLETED`.
- `assigned_count` counts future bookings marked `requires_instructor` that have at least one activity and active instructor coverage for every activity.
- `unassigned_count` counts future bookings marked `requires_instructor` when at least one activity has no active instructor.

Assignment counts use correlated existence checks against the booking projection,
so each booking contributes at most once and cannot be double-counted between
the assigned and unassigned buckets. Bookings without activities are in neither
assignment bucket.

Implemented open-events response fields:

- `id`
- `activity_id`
- `event_at`
- `city`
- `venue`
- `status`
- `requires_instructor`
- `version`
- `created_at`
- `updated_at`

The open-events response does not include customer_id, agreed_price, notes, participant_count, or other commercial/customer-sensitive fields.

Instructor list and detail responses also omit `customer_id`, `agreed_price`,
and `notes`. They retain `participant_count` because instructors need the group
size for operational preparation. Manager and customer booking responses retain
their existing full fields.

`GET /bookings/my-bookings` is restricted to customers and returns compact
summaries for the authenticated customer's bookings only.

Manual validation should be done with the existing seeded demo users.

## Validation

### Automated validation

Run:

```powershell
./.venv/Scripts/python.exe -m unittest discover -s backend\tests -v
./.venv/Scripts/python.exe -m compileall backend desktop_client
```

### Manual validation

1. Sign in as manager and query `/bookings` with filters to verify the response shape and access scope.
2. Query `/bookings/dashboard` as a manager and confirm the summary counts.
3. Sign in as instructor and verify `/bookings` and `/bookings/open-events` are limited to relevant bookings.
4. Sign in as customer and verify `/bookings/my-bookings` stays scoped to the signed-in customer.
5. Confirm cross-role access is rejected with `403` or `404`.

## Out Of Scope

This task does not include:

- full desktop dashboard UI
- advanced charts or reporting widgets
- AI/RAG behavior
- booking mutation workflows beyond the existing Task 08 scope

## Next Task

The next task should implement the corresponding desktop dashboard and booking views so the new backend queries can be consumed by the PySide6 client.
