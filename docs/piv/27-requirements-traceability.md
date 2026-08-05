# Task 27 Requirements Traceability — Dashboard Yearly Event Trend

## Scope

This matrix maps only Task 27 requirements to implementation and validation
evidence. The global product matrix remains in `requirements-traceability.md`.

| Task 27 requirement | Implementation evidence | Validation evidence | Status |
|---|---|---|---|
| Remove two Dashboard tables without removing workflows | `desktop_client/app/features/dashboard/view.py`; dedicated feature screens unchanged | Focused View tests and manual preserved-workflow check | Complete |
| Qt Charts line chart | `MonthlyTrendCard`, `QLineSeries`, `QChartView` | Qt Charts import and focused UI tests | Complete |
| Twelve months with zero filling | Repository `generate_series(1, 12)` and response schema | Backend SQL test and 12-point UI tests | Complete |
| Use actual scheduled event date | Aggregation reads `bookings.event_at` | SQL test excludes `created_at` | Complete |
| Fixed selector range | `SELECTABLE_YEARS = tuple(range(2015, 2051))` | UI asserts 2015, 2050, current year and exactly 36 values | Complete |
| Current-year default and empty year | Selector initialization plus zero-filled `show_data` | UI zero-series/default-selection tests | Complete |
| Manager-only Dashboard composition | Manager-only Dashboard `FeatureDescriptor` | Registry and workspace composition tests | Complete |
| Instructor default My Events | `default_page_for_role("instructor") == "bookings"` | Navigation/default-page tests | Complete |
| Customer default My Bookings | `default_page_for_role("customer") == "my_bookings"` | Navigation/default-page tests | Complete |
| No non-manager Dashboard API reads | Dashboard feature is not mounted; booking reads avoid Dashboard for non-manager | Workspace service-call assertions | Complete |
| Year change refreshes chart only | `DashboardPresenter.load_chart` uses independent operation key | Presenter service-call assertion | Complete |
| Loading, empty, retry, permission, connection and server states | Presenter error mapping and `MonthlyTrendCard` state widgets | Presenter/UI tests and manual failure flow | Complete |
| Repository → Service → Presenter → Passive View | Repository, handler/router, `BookingService`, Qt-free presenter, passive View | Architecture boundary scans | Complete |
| RTL, compact and scrollable selector | Dashboard View direction, max-visible items and scoped QSS | Focused UI tests and manual acceptance | Complete |
| No third-party chart library | Pinned PySide6 supplies `PySide6.QtCharts` | Import verification | Complete |
| No image assets generated | No Task 27 image file in changed inventory | Git changed-file audit | Complete |

## Related Task 27 evidence

- Implementation/PIV: `docs/piv/27-dashboard-yearly-event-trend.md`
- Manual acceptance: `docs/manual-testing-task-27.md`
- Validation report: `docs/piv/27-validation.md`
