# Task 08 - Booking Event Sourcing and CQRS Core

## Goal

Implement the booking command core using Event Sourcing and CQRS.

The goal of this task is not to build the full desktop booking UI. The goal is
to create the backend architecture that proves booking changes are stored as
immutable domain events, that current booking state is available through read
projections, and that booking state can be reconstructed by replaying events.

This task supports:

- `FR-BKG-01` - managers can create a booking.
- `FR-BKG-02` - booking statuses are validated by domain rules.
- `FR-BKG-03` - supported booking changes append immutable domain events.
- `FR-BKG-04` - booking history is available chronologically.
- `FR-BKG-05` - booking state is reconstructable by replay.
- `FR-BKG-06` - booking commands use optimistic concurrency.
- Course requirement - visibly demonstrate CQRS and Event Sourcing.

## Branch

Use this branch name:

```text
task-08-booking-event-sourcing-cqrs-core
```

## Required Context

Before implementing, read:

- `AGENTS.md`
- `PRD_Havaya_Im_Neshama.md`
- `docs/piv/requirements-traceability.md`
- `tasks/05-authentication-rbac.md`
- Existing backend auth, database, schema initialization, and router patterns
- Existing customer and activity repositories/services

If implementation details conflict, follow the PRD and `AGENTS.md`.

## Current State

The project should already have:

- FastAPI backend.
- PostgreSQL/Supabase-compatible persistence.
- Authentication and RBAC with a seeded manager user.
- Customer API and activity API.
- Activity image Gateway task completed.

Bookings, booking events, booking projections, and booking history are not yet
implemented.

## Scope

Implement a small but complete backend slice:

- booking event table
- booking projection table
- booking instructor projection table if assignment is included
- booking domain aggregate
- command handlers
- query handlers
- FastAPI routes
- replay/consistency tests
- PIV documentation

Keep the task backend-focused. Do not build desktop screens in this task.

## Out of Scope

Do not implement:

- PySide6 booking screens
- dashboard screens
- RAG assistant
- WhatsApp/email/calendar integration
- payment/invoice logic
- advanced instructor claim workflow
- production migration tooling if the project currently uses simple init SQL

## Required Architecture

Use CQRS separation:

- command side appends booking events and updates projections
- query side reads projection tables

Recommended structure, adjusted to the existing codebase:

```text
backend/app/domain/bookings/
  aggregate.py
  events.py
  status.py

backend/app/application/bookings/
  commands.py
  command_handlers.py
  queries.py
  query_handlers.py

backend/app/infrastructure/repositories/
  booking_event_repository.py
  booking_projection_repository.py

backend/app/api or backend/app/routers
  bookings.py
```

Routers must stay thin. Domain rules belong in the aggregate or command
handlers. SQL belongs in repositories/infrastructure.

## Database / Persistence

Add an append-only event store table:

```text
booking_events
```

Required fields:

```text
event_id
aggregate_id
aggregate_version
event_type
event_data JSONB
actor_user_id
occurred_at
correlation_id
```

Requirements:

- `aggregate_id` is the booking id.
- `(aggregate_id, aggregate_version)` must be unique.
- events must be inserted only.
- application code must not expose update/delete behavior for event rows.
- event payloads must include `schema_version`.

Add or update a rebuildable projection table:

```text
bookings
```

Suggested fields:

```text
id
customer_id
activity_id
event_at
city
venue
participant_count
agreed_price
status
requires_instructor
notes
version
created_at
updated_at
```

If instructor assignment is implemented in this task, add:

```text
booking_instructors
```

Suggested fields:

```text
booking_id
instructor_id
assigned_at
active
```

Use the existing DB initialization or migration style already used by the
project.

## Domain Events

Implement at least these events in this task:

```text
BookingCreated
BookingStatusChanged
BookingDateChanged
BookingPriceChanged
BookingLocationChanged
BookingParticipantCountChanged
BookingNotesUpdated
```

If the existing instructor table is ready, also implement:

```text
BookingGuideAssigned
BookingGuideRemoved
```

If instructor assignment would make the task too large, leave it for the next
task and document that decision in the PIV note.

## Domain Rules

Implement these minimum rules:

- A booking must reference an existing active customer.
- A booking must reference an existing active activity.
- `event_at`, `participant_count`, and `agreed_price` are required.
- `participant_count` must be positive.
- `agreed_price` must be non-negative.
- Valid statuses are:
  - `NEW`
  - `CONFIRMED`
  - `COMPLETED`
  - `CANCELLED`
- A completed booking cannot move back to an earlier status.
- A cancelled booking cannot move back to an earlier status.
- A cancelled booking cannot receive normal operational updates unless the PRD
  explicitly allows that update.

Keep rules simple and visible. This is an academic MVP, so clarity matters more
than covering every real-world edge case.

## Optimistic Concurrency

Every booking command after creation must include:

```text
expected_version
```

Behavior:

- If the current event stream version matches `expected_version`, append the new
  event and update the projection.
- If the version is stale, return HTTP `409 Conflict`.
- Creating a booking starts at version `1`.

## Required API Behavior

Add routes using the existing FastAPI style.

Suggested endpoints:

```text
POST /bookings
GET /bookings
GET /bookings/{booking_id}
GET /bookings/{booking_id}/history
PATCH /bookings/{booking_id}/status
PATCH /bookings/{booking_id}/schedule
PATCH /bookings/{booking_id}/price
PATCH /bookings/{booking_id}/location
PATCH /bookings/{booking_id}/participant-count
PATCH /bookings/{booking_id}/notes
POST /bookings/{booking_id}/replay
```

`POST /bookings/{booking_id}/replay` may be manager-only and can return the
replayed state for demonstration/testing. If the project prefers not to expose
this as an API, implement it as an application function and test it directly.

### Authorization

Minimum authorization:

- `manager` can create bookings and run booking commands.
- `manager` can read all bookings and booking history.
- `customer` can read only bookings linked to their own `customer_id`.
- `instructor` can read only assigned bookings, if instructor assignment exists.

If customer/instructor filtering depends on tables not ready yet, implement
manager-only booking endpoints in this task and document the deferred role
behavior in the PIV. Do not pretend it is implemented.

## Command Examples

Create booking request:

```json
{
  "customer_id": "uuid",
  "activity_id": "uuid",
  "event_at": "2026-08-15T10:00:00Z",
  "city": "Jerusalem",
  "venue": "School hall",
  "participant_count": 80,
  "agreed_price": 2400,
  "status": "NEW",
  "requires_instructor": true,
  "notes": "Demo booking"
}
```

Status change request:

```json
{
  "expected_version": 1,
  "status": "CONFIRMED"
}
```

## Validation Requirements

Run:

```powershell
.\.venv\Scripts\python.exe -m compileall backend desktop_client
```

If tests exist, run the relevant backend tests. If no test suite exists yet,
create focused tests for booking event sourcing.

Minimum automated validation:

- creating a booking appends `BookingCreated`
- projection is created at version `1`
- changing status appends `BookingStatusChanged`
- projection version increments
- replaying events reconstructs the same current state
- stale `expected_version` returns/reports conflict
- invalid status transition is rejected

Minimum manual API validation:

1. Login as manager.
2. Create a booking.
3. Read the booking detail.
4. Read booking history.
5. Change the booking status using the correct `expected_version`.
6. Try the same update again with the old `expected_version` and confirm `409`.
7. Replay the booking and confirm it matches the projection.

## PIV Documentation

Create:

```text
docs/piv/08-booking-event-sourcing-cqrs-core.md
```

Include:

- what was created
- which PRD requirements it supports
- files changed
- how to run it
- automated and manual validation
- what was deferred
- what the next task should be

Update:

```text
docs/piv/requirements-traceability.md
```

Mark booking Event Sourcing/CQRS as implemented only for the parts actually
completed.

## Acceptance Checklist

- [ ] `booking_events` table exists and stores immutable domain events.
- [ ] `bookings` projection exists and updates from command handlers.
- [ ] Booking aggregate can replay event streams.
- [ ] Create booking command appends `BookingCreated`.
- [ ] Supported update commands append specific events.
- [ ] `expected_version` is enforced.
- [ ] Stale command returns conflict.
- [ ] Booking history returns chronological events.
- [ ] Authorization is enforced server-side.
- [ ] `compileall` passes.
- [ ] PIV documentation is updated.

