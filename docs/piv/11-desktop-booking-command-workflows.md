# Task 11 - Desktop Booking Command Workflows

## What Was Created

Task 11 adds manager booking operations to the existing PySide6 booking screen:

- create a `NEW` booking using active customer and activity choices
- confirm a new booking
- cancel a non-terminal booking after explicit confirmation
- edit event time, agreed price, city/venue, participant count, and notes
- refresh the list, selected detail/history, and dashboard after commands
- present success, validation, authorization, concurrency, and connection errors

All mutations call the Task 08 event-sourced command endpoints. The desktop
does not update projections or connect to the database directly.

## Command Flow

1. A passive dialog collects values.
2. `BookingsPresenter` performs presentation-level parsing and prevents a
   second submission while the first is active.
3. `BookingService` maps the action to the existing backend endpoint.
4. Updates include the selected booking's `expected_version`.
5. Multi-field edits call granular commands in a stable order and carry the
   returned version into the next command.
6. The presenter reloads list, detail/history, and dashboard projections.

Backend validation remains authoritative. A later-command failure after an
earlier successful granular edit is not hidden: the presenter reports the
error and reloads the current projection before retry.

## Role Behavior

- Manager: sees and can use create, edit, confirm, and cancel controls.
- Instructor: retains read-only assigned-booking and open-event screens.
- Customer: retains read-only owned-booking screens.

Server-side authorization remains authoritative even though unauthorized
desktop controls are absent.

## Files Changed

- `desktop_client/app/api/client.py`
- `desktop_client/app/services/booking_service.py`
- `desktop_client/app/presenters/bookings_presenter.py`
- `desktop_client/app/views/bookings_view.py`
- `desktop_client/app/views/booking_dialogs.py`
- `desktop_client/app/main.py`
- `desktop_client/tests/`
- `tasks/11-desktop-booking-command-workflows.md`
- `docs/piv/11-desktop-booking-command-workflows.md`
- `docs/piv/requirements-traceability.md`
- `README.md`
- `ARCHITECTURE.md`

## How To Run

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
.\.venv\Scripts\python.exe -m desktop_client.app.main
```

Sign in as the seeded manager to use booking commands. Instructor and customer
accounts remain read-only for bookings.

## Validation

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\Scripts\python.exe -m unittest discover -s desktop_client/tests -v
.\.venv\Scripts\python.exe -m compileall backend desktop_client
git diff --check
```

## PRD Requirements Advanced

- `FR-BKG-01`
- `FR-BKG-02`
- `FR-BKG-03`
- `FR-BKG-06`
- PRD journey 8.1 for manager booking creation and supported edits

## Remaining Booking Work

- manager instructor assignment/removal UI (`FR-INS-04`)
- a dedicated cancellation-reason event/API, if separately scheduled
- customer/activity management screens needed for the complete manager journey

These are not part of Task 11.

