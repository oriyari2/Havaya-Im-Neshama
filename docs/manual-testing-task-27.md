# Task 27 Manual Verification — Dashboard Yearly Event Trend

## Purpose

Verify only Task 27: the Dashboard presentation change, role-scoped annual
trend, focused refresh behaviour, and chart failure states.

## Prerequisites

1. Install `backend/requirements.txt` and `desktop_client/requirements.txt`.
2. Start the configured FastAPI backend and Desktop client using the README.
3. Use the existing Manager, Instructor, and Customer demo accounts.
4. Use existing database data; do not initialize or seed during verification.

## Automated pre-check

```powershell
.\.venv\Scripts\python.exe -m compileall backend desktop_client
.\.venv\Scripts\python.exe -m unittest discover -s backend\tests -p "test_*.py"
.\.venv\Scripts\python.exe -m unittest desktop_client.tests.test_presenters desktop_client.tests.test_services
.\.venv\Scripts\python.exe -m unittest desktop_client.tests.test_views
.\.venv\Scripts\python.exe -m unittest desktop_client.tests.test_ui_foundations.UiFoundationTests.test_dashboard_phase_two_uses_branded_sections_without_group_boxes desktop_client.tests.test_ui_foundations.UiFoundationTests.test_dashboard_chart_year_selector_emits_focused_refresh desktop_client.tests.test_ui_foundations.UiFoundationTests.test_dashboard_content_scrolls_without_clipping_manager_layout
git diff --check
```

## Manager acceptance

1. Open Dashboard and confirm the existing summary cards are unchanged.
2. Confirm neither removed operational table is rendered below the cards.
3. Confirm the annual trend card has the specified Hebrew title/subtitle, an
   RTL selector, 12 month labels, visible points, integer Y axis, and no legend.
4. Confirm the selector contains exactly 36 ascending values from 2015 through
   2050, is easy to scroll, and initially selects the current calendar year.
5. Change the year. Only the chart should enter loading state; summary cards,
   page position, and navigation must remain unchanged.
6. Select an empty year and confirm all 12 values are zero, the empty message is
   visible, and the selector never jumps to another year.

## Role visibility acceptance

1. Sign in as Instructor. Confirm Dashboard button/page is absent and My Events
   is the initially selected screen.
2. Sign in as Customer. Confirm Dashboard button/page is absent and My Bookings
   is the initially selected screen.
3. During both sessions, inspect requests and confirm neither
   `/bookings/dashboard` nor `/bookings/dashboard/yearly-trend` is requested.
4. Attempt unknown/forbidden navigation and confirm the current screen remains unchanged.

## Failure and retry acceptance

1. With Dashboard loaded, stop the backend and change the selected year.
2. Confirm the chart shows its connection message and retry action without
   clearing or reloading summary cards.
3. Restart the backend and select **נסו שוב**; the selected year should reload.
4. Verify `403` maps to the chart permission message and `5xx` maps to the
   chart server/retry message.

## Preserved workflow check

Use the sidebar to open Booking/My Events/Open Events destinations. Confirm the
Dashboard presentation removal did not remove, reroute, or change permissions
for those dedicated workflows.

## Expected result

All checks pass without a full Dashboard reload, Desktop database access,
cross-role data exposure, or generated image assets.
