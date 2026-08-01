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
