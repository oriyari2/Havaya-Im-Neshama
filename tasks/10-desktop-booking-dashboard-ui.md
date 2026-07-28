# Task 10 - Desktop Booking and Dashboard UI

## Goal

Implement the PySide6 desktop shell and read-only booking/dashboard experience
on top of the completed Task 09 query APIs.

## PRD Requirements

- `FR-AUTH-03` - role-appropriate desktop navigation.
- `FR-AUTH-04` - customer booking ownership through the authenticated API.
- `FR-BKG-04` - manager booking-history presentation.
- `FR-BKG-07` - manager booking filters.
- `FR-INS-02` - instructor assigned-booking view.
- `FR-INS-03` - instructor eligible open-event view.
- `FR-DASH-01` to `FR-DASH-03` - role-specific desktop dashboards.

## Scope

- sign-in and authenticated API session
- Hebrew RTL shell with role-based navigation
- role-aware dashboard summary and shortcuts
- manager/instructor assigned booking list
- customer `my-bookings` list
- role-appropriate booking details
- manager booking history
- instructor/manager open-events list
- manager filters supported by Task 09
- loading, empty, and error states
- presenter/view/service separation

## Out of Scope

- booking creation or mutation forms
- instructor assignment mutation UI
- customer/activity CRUD screens
- activity image UI
- AI/RAG functionality

## Acceptance Checklist

- [x] Desktop authenticates through the FastAPI backend.
- [x] Navigation is limited by role.
- [x] Dashboard is role-aware.
- [x] Booking and details screens use Task 09 APIs.
- [x] Customers use the ownership-scoped my-bookings API.
- [x] Instructors see assigned and eligible open events without commercial fields.
- [x] Manager history is displayed chronologically as returned by the API.
- [x] Views are passive and presenters contain no PySide code.
- [x] Loading, empty, and error states exist.
- [x] Focused desktop tests and PIV documentation exist.
