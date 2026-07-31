# Task 24: End-to-End Booking Request and Creation Workflow

## Status

Implemented and validated. The requested commit and push close the task.

## Goal

Complete `FR-BKG-01` and `FR-BKG-01A` through one role-aware desktop workflow
over the existing `POST /bookings` CQRS/Event Sourcing path.

## Scope and fields

- Entry from Bookings and a selected Activity using one form and Presenter.
- Manager: Customer, Activity, date/time, city, venue, participants, agreed
  price, instructor requirement, and notes.
- Customer: Activity, date/time, city, venue, participants, and notes. Customer
  identity, price, status, and instructor controls are absent.
- Server-derived Customer ownership and server-controlled `NEW`, zero price,
  and no instructor requirement for Customer requests.
- Existing immutable `BookingCreated` append and transactional projection.

## Authorization

| Capability | Manager | Customer | Instructor |
|---|---|---|---|
| Create from Bookings/Activity | Any active Customer | Authenticated Customer only | Denied |
| Set price/instructor requirement | Existing fields | No | No |
| Set status | Existing API | Forced `NEW` | No |

## Architecture

`View -> Qt-free BookingsPresenter -> BookingService -> ApiClient -> FastAPI ->
CreateBookingCommand -> BookingAggregate -> BookingCreated -> event store and
projection in one transaction`. Rejected requests dispatch no command/event.
Task 22/23 mutation ownership, stale suppression, session isolation, and targeted
Bookings/history/assignments/open-events/dashboard invalidation are preserved.

## Validation and errors

Activity, Customer (Manager), valid date, and positive participants are
required. Active identifiers are revalidated server-side. Existing friendly
400/422, 403, 409, session-expiry, and transport handling remains.

## Out of scope

Assignment approval, notifications, new statuses, migrations, historical-event
changes, pricing redesign, Task 25, and global refresh.

## Acceptance

- Customer cannot choose or tamper with Customer identity.
- Manager must select a Customer; Activity entry protects the selected Activity.
- Instructor has no action and receives HTTP 403.
- Exactly one immutable creation event and projection are committed.
- Successful Manager/Customer creation is immediately reconciled into Bookings.
- Existing read scoping, duplicate guards, and native lifecycle safety remain.

## Final assignment handoff

Creation remains unassigned. Manager assignment is the existing Activity-scoped
workflow in Booking Details; Task 24.2 clarifies its labels without adding a
second command or creation-time assignment.
