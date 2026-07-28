# Task 09 - Dashboard and Booking Queries

## Goal

Implement role-aware booking queries and dashboard summaries for the Havaya Im Neshama Management System.

The goal of this task is not to build the full desktop dashboard experience. The goal is to create the backend query layer and API shape that supports role-specific booking visibility, booking summaries, and dashboard-style counts using the booking projections introduced in Task 08.

This task supports:

- `FR-DASH-01` - managers see counts of upcoming bookings by status and unassigned events.
- `FR-DASH-02` - instructors see assigned upcoming events and eligible open events.
- `FR-DASH-03` - customers see their upcoming bookings and recent statuses.
- `FR-BKG-07` - managers filter bookings by date, status, customer, activity, and instructor.
- Course requirement - visibly demonstrate role-aware dashboard-style read behavior.

## Branch

Use this branch name:

```text
task-09-dashboard-booking-queries
```

## Required Context

Before implementing, read:

- `AGENTS.md`
- `docs/PRD.md`
- `docs/piv/requirements-traceability.md`
- `tasks/08-booking-event-sourcing-cqrs-core.md`
- Existing booking event-sourcing, projection, and router patterns
- Existing authentication and RBAC helpers from previous tasks

If implementation details conflict, follow the PRD and `AGENTS.md`.

## Current State

The project should already have:

- FastAPI backend.
- PostgreSQL/Supabase-compatible persistence.
- Authentication and RBAC.
- Booking event sourcing and CQRS core from Task 08.
- Booking projections and booking history endpoints from Task 08.

The project does not yet have:

- dashboard-style summary endpoints
- richer booking list filters
- role-specific booking query behavior beyond the basic Task 08 access rules
- desktop dashboard screens

## Objective

Deliver a small but complete backend query slice that makes bookings usable for real operational workflows.

The implementation should allow:

- managers to view filtered booking lists and summary counts
- instructors to view only bookings relevant to them
- customers to view only their own bookings and their current statuses
- the system to expose these query results through API endpoints that can later support the desktop dashboard and booking views

## Scope

Implement backend query behavior for the following areas:

- filtered booking list retrieval
- role-aware booking summaries and counts
- instructor-relevant booking views
- customer-relevant booking views
- API endpoints for dashboard and booking query support
- focused backend tests
- PIV documentation

Keep the task backend-focused. Do not build the full desktop dashboard UI in this task.

## Out of Scope

Do not implement:

- full PySide6 dashboard screens
- advanced charts/visual widgets
- AI or RAG features
- booking creation or mutation workflows beyond those already provided in Task 08
- image upload or activity image UI
- payment, invoice, or CRM integrations
- production-grade analytics or reporting

## User Stories

### Manager

As a manager, I want to:

- view all bookings with filters for status, date, customer, activity, and instructor
- see summary counts such as upcoming bookings by status
- see how many bookings are still unassigned or require instructor attention
- open the booking list and details without exposing unauthorized data

### Instructor

As an instructor, I want to:

- view only bookings assigned to me
- view future bookings that require an instructor and are relevant to me
- see booking details that are appropriate for my role without seeing commercial or customer-sensitive fields
- quickly identify upcoming work that needs attention

### Customer

As a customer, I want to:

- view only my own bookings
- see the current status and recent changes for those bookings
- access a simple booking list without seeing other customers' records

## Functional Requirements

### FR-DASH-01 - Manager dashboard summaries

Managers can retrieve booking summary counts for:

- total upcoming bookings
- bookings by status
- bookings requiring instructor assignment
- bookings that are assigned and upcoming

### FR-DASH-02 - Instructor dashboard views

Instructors can retrieve:

- bookings assigned to them
- future bookings that require an instructor and are eligible for their view

### FR-DASH-03 - Customer booking views

Customers can retrieve:

- only their own bookings
- booking statuses and summary information relevant to those bookings

### FR-BKG-07 - Advanced booking filters

Managers can filter bookings by:

- date range
- status
- customer
- activity
- instructor

### Authorization Requirements

Server-side authorization is mandatory.

- `manager` can view all bookings and dashboard summaries.
- `instructor` can view only bookings relevant to their assignment and eligible instructor-facing views.
- `customer` can view only their own bookings.
- Cross-role access must be rejected with `403` or `404` without data leakage.

## Acceptance Criteria

- [x] Manager can list bookings with filters and receive correct results.
- [x] Manager can retrieve summary counts for upcoming bookings by status.
- [x] Instructor can retrieve assigned and eligible bookings only.
- [x] Customer can retrieve only their own bookings.
- [x] Unauthorized cross-role access is rejected server-side.
- [x] Booking results are based on the booking projection from Task 08.
- [x] Queries remain consistent with booking event replay semantics.
- [x] API behavior is covered by focused backend tests.
- [x] PIV documentation is created.

## API Endpoints

Add or extend endpoints using the existing FastAPI style.

### Booking list and filters

```text
GET /bookings
```

Supported query parameters:

```text
status
customer_id
activity_id
instructor_id
from_date
to_date
limit
offset
```

Behavior:

- `manager` may use all filters.
- `instructor` may use a reduced set of filters relevant to instructor visibility.
- `customer` may use no cross-customer filters.

### Dashboard summaries

```text
GET /bookings/dashboard
```

Returns the dashboard summary for the signed-in user context.

Implemented response shape:

```json
{
  "confirmed_count": 6,
  "pending_count": 4,
  "cancelled_count": 1,
  "upcoming_count": 12,
  "assigned_count": 5,
  "unassigned_count": 3
}
```

All dashboard counts apply only to future bookings. `assigned_count` counts each
instructor-required booking once when it has at least one activity and every
activity has an active instructor. `unassigned_count` counts each
instructor-required booking once when at least one activity lacks an active
instructor.

### Instructor-facing open events

```text
GET /bookings/open-events
```

Returns future bookings that require an instructor and are visible to the signed-in instructor.

Instructors may see eligible open events without already being assigned to the
booking. Open events must be future `NEW` or `CONFIRMED` bookings marked as
requiring an instructor, with at least one activity lacking an active
instructor.

Implemented response fields:

- id
- activity_id
- event_at
- city
- venue
- status
- requires_instructor
- version
- created_at
- updated_at

The open-events response does not include customer_id, agreed_price, notes, participant_count, or other commercial/customer-sensitive fields.

### Customer-facing booking summary

```text
GET /bookings/my-bookings
```

Returns the signed-in customer's bookings in a compact summary view.

The endpoint is customer-only and applies ownership filtering server-side.

### Optional detail support

```text
GET /bookings/{booking_id}
```

Existing detail endpoint may be reused and extended with a more compact response shape for role-specific views.

## Authorization Rules

Use the existing authentication and RBAC helpers from previous tasks.

Required behavior:

- Missing or invalid token returns `401`.
- Authenticated user with the wrong role returns `403`.
- Cross-role booking access returns `403` or `404`.
- Customers cannot retrieve other customers' bookings.
- Instructors cannot retrieve bookings outside their assigned/relevant scope.
- Managers can retrieve all permitted booking query results.

## Backend Architecture

Keep the implementation aligned with the existing backend structure.

### Suggested backend modules

```text
backend/app/application/bookings/query_handlers.py
backend/app/infrastructure/repositories/booking_projection_repository.py
backend/app/routers/bookings.py
backend/app/schemas/booking.py
```

### Architectural expectations

- Query logic stays in the application/query layer.
- SQL and filtering logic remain in repository/infrastructure code.
- Routers stay thin.
- Booking reads continue to use the projection built in Task 08.
- Role-based filtering should be centralized and reused across list and summary endpoints.

## Desktop Impact

The desktop client is expected to be impacted, but this task should remain backend-first.

### Expected desktop impact

- The bookings module may need a role-aware list view.
- The dashboard module may need to render summary cards or counts.
- The instructor and customer modules may need to consume new role-aware endpoints.

### Desktop scope for this task

- Do not build full desktop screens in this task.
- Do not introduce unrelated desktop architecture changes.
- The backend API shape should be ready for the desktop client to consume.

## Testing Strategy

Create focused backend tests for the new query behavior.

### Backend tests

- manager can list filtered bookings
- manager can retrieve dashboard summary counts
- instructor can retrieve only assigned/relevant bookings
- instructor cannot retrieve unrelated bookings
- customer can retrieve only their own bookings
- customer cannot retrieve other customers' bookings
- empty result sets return expected empty responses
- unauthorized roles are rejected correctly

If the current test style supports it, add tests at the query-handler or router level. Keep tests focused and avoid unnecessary scaffolding.

## Manual Validation

Manual validation should be done with seeded demo users.

1. Log in as manager.
2. Query `/bookings` with several filters and confirm the results.
3. Query `/bookings/dashboard` and confirm counts.
4. Log in as instructor and query `/bookings` and `/bookings/open-events`.
5. Log in as customer and query `/bookings/my-bookings`.
6. Confirm cross-role access is denied.
7. Confirm the response payloads are suitable for future desktop consumption.

## Implementation Order

1. Review Task 08 booking projection and existing query handlers.
2. Add or extend query methods for booking list filtering and summaries.
3. Add the API endpoints for dashboard and role-specific booking views.
4. Add role-based authorization checks.
5. Add focused backend tests.
6. Validate with compile and backend tests.
7. Create PIV documentation.

## PIV Documentation

Create:

```text
docs/piv/09-dashboard-booking-queries.md
```

Include:

- what was created
- which PRD requirements it supports
- files changed
- how to run it
- how it was validated
- what the next task should be

## Acceptance Checklist

- [x] Booking list supports manager filters.
- [x] Dashboard summary endpoint returns role-aware counts.
- [x] Instructor-facing open-event query exists.
- [x] Customer-facing booking summary exists.
- [x] Role-based authorization is enforced server-side.
- [x] Backend tests cover the new query behavior.
- [x] PIV documentation is created.
