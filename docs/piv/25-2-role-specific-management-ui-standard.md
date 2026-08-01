# PIV — Task 25.2 Role-Specific Management UI Standard

## Created

Customer, Instructor, and Manager management now use the same RTL page
hierarchy, list-to-details flow, semantic tables, pagination, information
cards, equal action buttons, dialog conventions, feedback, and password flow.
Instructor and Manager modules no longer use legacy split panes.

Instructor fields remain limited to name, login email, phone, city, notes,
status, and audit data. Manager details contain only name, login email, status,
and audit data. Login email is read-only during edit; passwords remain
write-only and change only through the shared password modal.

## Architecture

`ManagementWorkspace` owns reusable UI composition only. Role-specific Views
remain passive and existing Presenters orchestrate their services. Manager name
editing remains inside the user-administration service and repository boundary.
Authentication, authorization, account creation, and hashing stay centralized.

## Validation

Focused backend, Presenter, service, View, and UI-foundation tests are run with
`compileall` and `git diff --check`. No screenshots, images, diagrams, mockups,
or visual reports were generated.

## Next

Stop and wait for explicit approval before continuing to another screen.

## Final stabilization and completeness audit

- Removed the unlaid `StatePanel`/`FeedbackBanner` children previously created
  by `StatefulWidget`. Showing their loading state produced the apparent empty
  window over Instructor selection. Loading and empty states now live only in
  widgets owned by the visible page layout.
- The Dashboard is selected and its initial request is started before the
  completed Shell replaces Login. The Login Presenter no longer updates its
  deleted View after authentication, so startup exposes one intended top-level
  window and one direct Login-to-Shell transition.
- Customer, Instructor, and Manager headers and toolbar containers now use the
  same margins, spacing, typography, frame, control dimensions, and RTL order:
  Search field, Search, one immediate Sort selector, Reset.
- Instructor sorting uses existing name, city, phone, email, status, created,
  and updated fields. Manager sorting uses existing name, email, status,
  created, and updated fields. Sort values are server-whitelisted and reuse the
  existing list endpoints and repository queries.
- Every displayed management-table item now receives explicit right alignment,
  including emails and technical text. Semantic minimum widths prevent the
  important identity columns from being squeezed; horizontal scrolling remains
  available below the supported minimum.

Backend/Desktop coverage was audited as follows:

- Customer and Instructor create, read, edit, guarded delete, linked-account
  creation, password change, business fields, status display, and audit metadata
  are represented in Desktop.
- Manager create, read, name edit, activation/deactivation, password change,
  status, and audit metadata are represented in Desktop.
- Multi-contact CRUD remains intentionally outside these management screens:
  the approved MVP presents and edits one current primary contact through the
  Customer workflow instead of exposing the internal contact collection.
- Raw Customer/Instructor `is_active` mutation is intentionally not exposed as
  a standalone UI action because it would bypass linked-account state. Manager
  activation/deactivation uses the canonical account workflow.
- Instructor assignment relationships remain in Booking Management, where the
  CQRS workflow owns assignment changes; duplicating them in Instructor Details
  would violate that boundary.

Focused tests cover top-level-window lifecycle, startup replacement, module
string isolation, toolbar order and immediate sorting, explicit RTL alignment,
semantic widths, and repository sort whitelists. No screenshots or visual
assets were created.
