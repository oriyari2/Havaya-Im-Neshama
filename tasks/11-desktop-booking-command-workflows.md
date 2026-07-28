# Task 11 - Desktop Booking Command Workflows

## Goal

Extend the Task 10 read-only booking UI with the manager booking mutations
already supported by the event-sourced FastAPI command API.

## PRD Requirements

- `FR-BKG-01` - create a booking through the desktop client.
- `FR-BKG-02` - confirm and cancel using supported domain statuses.
- `FR-BKG-03` - use event-sourced command endpoints for every change.
- `FR-BKG-06` - send the current projection version with updates.
- The Create and Manage a Booking journey in PRD section 8.1.

## Scope

- manager-only create-booking dialog with active customer/activity selectors
- manager-only confirmation and cancellation commands
- manager-only editing of schedule, price, location, participant count, and notes
- cancellation confirmation
- optimistic-version propagation across granular edit commands
- duplicate-submission prevention
- loading, success, validation, authorization, conflict, and connection errors
- refresh of booking list, selected details/history, and dashboard after success
- Hebrew RTL controls within the existing functional visual style

Cancellation uses the existing status command with `CANCELLED`. The backend
does not currently expose a separate cancellation-reason command.

## Out of Scope

- instructor assignment/removal UI
- customer or activity management UI
- instructor profile management
- activity images
- AI/RAG
- schema changes or a visual redesign

## Acceptance Checklist

- [x] Only managers see booking command controls.
- [x] Creation uses `POST /bookings` and active lookup records.
- [x] Confirmation and cancellation use the status command endpoint.
- [x] Supported field edits use their existing granular endpoints.
- [x] Every update carries `expected_version`.
- [x] Cancellation requires explicit confirmation.
- [x] Duplicate submissions are ignored while a command is active.
- [x] Successful commands refresh read projections and dashboard data.
- [x] Validation, authorization, conflict, connection, and success states are visible.
- [x] Views remain passive and presenters remain free of PySide imports.
- [x] Focused presenter, service, permission, form, retry, and offscreen tests exist.

