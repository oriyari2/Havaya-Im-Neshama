# Task 27 PIV — Dashboard Yearly Event Trend

## What was created

Task 27 removes two duplicate operational tables from the Dashboard visual
composition while leaving their dedicated Booking and Open Events workflows
unchanged. A full-width RTL card now renders a Qt Charts
line series for the 12 calendar months with visible points, anti-aliasing,
native series animation, integer Y axis, and the established branded styling.

The compact year selector contains exactly the ascending 2015–2050 range and
selects the current calendar year by default. It does not switch away when that
year has no data. A selection change invokes only the trend endpoint.
The card owns visual loading/empty/error/retry states while the Qt-free
presenter owns request orchestration and error classification.

## Architecture and PRD support

The read path is `booking_projection_repository -> query_handlers -> bookings
router -> BookingService -> DashboardPresenter -> DashboardView`. One
parameterized PostgreSQL query applies the existing booking visibility filter,
groups by `bookings.event_at`, generates all 12 months, and derives scoped
years without N+1 reads. The Desktop composes Dashboard only for Managers;
Instructor starts on My Events and Customer starts on My Bookings without a
Dashboard page, button, presenter, or API read. This advances the PRD Dashboard,
RBAC, CQRS projection, RTL Desktop, MVP, and graph-presentation requirements.

## Files changed

Backend:

- `backend/app/schemas/booking.py`
- `backend/app/routers/bookings.py`
- `backend/app/application/bookings/query_handlers.py`
- `backend/app/infrastructure/repositories/booking_projection_repository.py`
- `backend/tests/test_booking_queries.py`

Desktop:

- `desktop_client/app/features/bookings/service.py`
- `desktop_client/app/features/dashboard/presenter.py`
- `desktop_client/app/features/dashboard/registration.py`
- `desktop_client/app/features/dashboard/view.py`
- `desktop_client/app/features/registry.py`
- `desktop_client/app/main.py`
- `desktop_client/app/shared/navigation.py`
- `desktop_client/app/shared/ui/design_tokens.py`
- `desktop_client/tests/test_microfrontends.py`
- `desktop_client/tests/test_presenters.py`
- `desktop_client/tests/test_services.py`
- `desktop_client/tests/test_views.py`
- `desktop_client/tests/test_ui_foundations.py`

Task 27 and current-state documentation:

- `tasks/27-dashboard-yearly-event-trend.md`
- `docs/piv/27-dashboard-yearly-event-trend.md`
- `docs/piv/27-requirements-traceability.md`
- `docs/manual-testing-task-27.md`
- `docs/piv/27-validation.md`
- `docs/piv/00-index.md`
- `docs/piv/requirements-traceability.md`
- `README.md`
- `ARCHITECTURE.md`

## Acceptance criteria

- The Dashboard does not render Upcoming Events or Events Requiring Assignment tables.
- Dedicated navigation and workflows for those datasets remain operational.
- The chart shows January through December and zero-fills missing months.
- Counts use the scheduled event date, never creation or status dates.
- Only Manager registers and requests Dashboard; non-manager defaults are role screens.
- The selector contains exactly 36 ascending values from 2015 through 2050.
- Current year remains selected even when all twelve values are zero.
- A year change refreshes only the chart.
- Loading, empty, permission, connection, server failure, and retry are supported.
- Presenters remain Qt-free and the View remains passive.

## Run

Install `desktop_client/requirements.txt` (the pinned PySide6 package already
includes `PySide6.QtCharts`), start the FastAPI backend, then start the Desktop
using the README commands. No additional chart library is required.

## Validation

Observed on August 5, 2026: all 247 backend tests and 48 relevant focused
Desktop/architecture tests passed. The full 286-test Desktop discovery retained
unrelated existing Qt lifecycle resource failures, an existing instructor
button-width failure, and the pre-existing feature-first compatibility-directory
scan failure; these are recorded in `docs/piv/27-validation.md`. `compileall`,
architecture scans, dependency scans, OpenAPI inspection, Qt Charts import, and
`git diff --check` passed.

Authenticated read-only Manager requests against the configured backend returned
12 months for current year 2026 (total 40) and empty year 2015 (total 0).
The backend authorization contract remains unchanged. Desktop composition tests
verify that Instructor and Customer never register Dashboard and never issue
either Dashboard request.

Detailed manual steps are in `docs/manual-testing-task-27.md`; complete
automated and live-backend evidence is in `docs/piv/27-validation.md`.
Requirement-to-evidence mapping is in
`docs/piv/27-requirements-traceability.md`.

## Known limitations

The chart counts one booking/event projection per scheduled event date. It does
not split a multi-activity booking into multiple points because the user-facing
booking schedule and existing dashboard semantics use `bookings.event_at`.

## Next task

Task 27 is complete. Do not begin a later task without explicit approval.
