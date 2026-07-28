# Task 10 - Desktop Booking and Dashboard UI

## What Was Created

Task 10 replaces the placeholder PySide6 window with the first operational
desktop MVP slice:

- authenticated login backed by `POST /auth/login`
- Hebrew RTL application shell
- role-based navigation for manager, instructor, and customer
- role-aware dashboard cards and booking shortcuts
- manager/instructor booking list and customer my-bookings list
- booking detail presentation with role-safe fields
- manager-only chronological event-history table
- manager/instructor eligible open-events screen
- manager filters for status, dates, customer, activity, and instructor
- visible loading, empty, connection-error, and API-error states

## Architecture

The desktop follows MVP boundaries:

- `views/` contains passive PySide6 widgets and emits user-intent signals.
- `presenters/` contains orchestration and presentation formatting without
  importing PySide6.
- `services/` maps desktop use cases to backend endpoints.
- `api/` owns HTTP, bearer-token, and API error behavior.
- `models/` contains the authenticated session model.
- `main.py` is the composition root that wires views, presenters, and services.

The desktop never connects directly to PostgreSQL or Supabase.

## Role Behavior

- Manager: dashboard, filtered bookings, full booking details, event history,
  and open events.
- Instructor: dashboard, assigned bookings, operational details, and eligible
  open events. Customer ID, agreed price, and notes are not rendered because
  they are absent from the instructor API schema.
- Customer: dashboard and compact `GET /bookings/my-bookings` results only.

Participant count remains visible for an assigned instructor because it is
needed for event preparation. Open events use the stricter compact schema and
do not include participant count.

## Files Changed

- `desktop_client/app/main.py`
- `desktop_client/app/api/`
- `desktop_client/app/models/`
- `desktop_client/app/services/`
- `desktop_client/app/presenters/`
- `desktop_client/app/views/`
- `desktop_client/tests/`
- `tasks/10-desktop-booking-dashboard-ui.md`
- `ARCHITECTURE.md`
- `README.md`
- `docs/piv/requirements-traceability.md`

## How To Run

Start the backend:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```

Then start the desktop client:

```powershell
.\.venv\Scripts\python.exe -m desktop_client.app.main
```

`API_BASE_URL` may override the default `http://127.0.0.1:8000` backend URL.

## Validation

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend\tests -v
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\Scripts\python.exe -m unittest discover -s desktop_client\tests -v
.\.venv\Scripts\python.exe -m compileall backend desktop_client
```

Manual-safe navigation verification instantiates the PySide6 shell offscreen
for all three roles and verifies the permitted page set without starting AI,
Cloudinary, or database operations.

## PRD Requirements Advanced

- `FR-AUTH-03`
- `FR-AUTH-04`
- `FR-BKG-04`
- `FR-BKG-07`
- `FR-INS-02`
- `FR-INS-03`
- `FR-DASH-01` to `FR-DASH-03`

## Remaining Desktop Work

- booking creation and event-sourced mutation forms
- manager instructor assignment/removal UI
- customer and activity management/catalog screens
- activity image display/upload UI
- instructor profile management
- AI/RAG screens

These remain separate future tasks.
