# Task 27 Validation Report — Dashboard Yearly Event Trend

## Scope validated

This report covers only Task 27: removal of two Dashboard table presentations,
the role-scoped annual event trend endpoint, the Qt Charts card, year-only
refresh, failure states, and Task 27 documentation.

## Automated results — August 5, 2026

| Validation | Result |
|---|---|
| Backend discovery | 247 tests passed |
| Relevant focused Desktop/architecture commands | 48 tests passed |
| Full Desktop discovery | 286 tests run; 2 unrelated existing failures and 4 intermittent Qt resource errors |
| `compileall backend desktop_client` | Passed |
| `PySide6.QtCharts` import | Passed with pinned `PySide6==6.9.1` |
| Presenter PySide scan | Clean |
| Dashboard View dependency scan | Clean |
| OpenAPI inspection | Trend GET present; `YearlyEventTrendResponse`; validated year query |
| `git diff --check` | Passed; line-ending notices only |

The full Desktop failures were four intermittent Qt widget-allocation errors,
the existing instructor action-width assertion, and the existing feature-first
compatibility-path assertion caused by `desktop_client/app/views`. Task 27's
focused suites pass and do not alter those unrelated areas.

## Architecture checks

- Dashboard Presenter contains no PySide6 import.
- Dashboard View contains no SQL, repository, service, database, or API access.
- Router contains no aggregation SQL.
- Projection SQL is parameterized and contained in the booking repository.
- The existing `_visibility_filter` is reused for all roles.
- One query produces visible years and all 12 requested-year month counts.
- A year selection calls only `yearly_event_trend`; summary/list endpoints are
  not invoked.
- The selector is fixed to 2015–2050 and defaults to the current calendar year.
- Dashboard feature registration is Manager-only; non-manager composition has
  no Dashboard page/presenter and makes no Dashboard API request.
- Role defaults are Manager Dashboard, Instructor My Events, Customer My Bookings.
- Forbidden navigation returns without changing the active page.
- Logout/session expiry invalidate presenters, clear the presenter map, detach
  the workspace shell, and release Dashboard/chart widget state.

## Real-backend read-only verification

Authenticated Manager GET requests against the configured running backend returned:

| Request | Year | Months | Annual total |
|---|---:|---:|---:|
| Current calendar year | 2026 | 12 | 40 |
| Empty selectable year | 2015 | 12 | 0 |

This confirms current-year and zero-data-year behaviour without fabricated data.
Instructor and Customer Desktop sessions are covered by composition tests that
assert no Dashboard page/presenter and zero Dashboard service calls.
Verification performed no writes, initialization, seed, replay, or schema operation.

## Acceptance decision

Task 27 acceptance criteria are satisfied. Known limitation: the trend counts
one Booking projection per displayed `bookings.event_at`; it does not split a
multi-activity Booking into several chart points.
