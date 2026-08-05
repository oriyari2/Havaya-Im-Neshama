# Task 27 — Dashboard Yearly Event Trend

## Scope

Remove only the two dashboard operational tables and add a role-scoped annual
Qt Charts line chart beneath the existing summary cards. Make the Dashboard a
manager-only operational feature. Preserve existing
navigation, endpoints, permissions, and dedicated operational screens.

## Acceptance

- Only Managers mount, navigate to, or request the Dashboard.
- Manager opens Dashboard by default; Instructor opens My Events; Customer opens My Bookings.
- Counts use the displayed scheduled event date (`bookings.event_at`).
- January through December are always returned, including zero months.
- The RTL selector contains every year from 2015 through 2050, sorted ascending.
- The current calendar year is selected by default and is never replaced automatically.
- The year selector refreshes only the chart and supports loading, empty, retry,
  authorization, connection, and server-error states.
- Desktop flow remains Service → Presenter → Passive PySide6 View; SQL remains
  in the booking projection repository.
- No screenshots or visual assets are created.
