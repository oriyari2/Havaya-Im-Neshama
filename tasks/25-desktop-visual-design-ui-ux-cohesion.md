# Task 25 — Desktop Visual Design and UI/UX Cohesion

## Status

**25.0.1 COMPLETE — LOGIN SCREEN LAYOUT POLISH**

**25.1 COMPLETE — CUSTOMER SCREEN PROFESSIONAL DESKTOP UX**

Task 25 is proceeding screen by screen. Subtasks 25.0.1 and 25.1 improve
composition and professional Desktop UX before colors, branding, icons,
shadows, gradients, corner treatments, typography, and theme are designed.

## Task 25.0.1 scope

- Increase and center the Login card for large desktop windows.
- Establish the sequence: welcome, application name, short description, and
  sign-in instruction.
- Place Email and Password labels above their controls.
- Give both inputs and the Login button a consistent, comfortable width.
- Separate the introduction, fields, feedback, and primary action vertically.
- Keep feedback directly below the fields without overlap or compression.

## Implementation

The Login card is constrained to 520–560 px and centered within a root layout
that retains space on all sides. Its content uses a single vertical reading
flow with 32 px card padding and spacing selected from the existing neutral
tokens. Inputs have a 440 px minimum content width and expanding horizontal
policies; the Login button follows the same available width. The existing
primary-button colors are unchanged; selector specificity was corrected only
so the already-defined primary treatment and text remain visible in the Login
panel.

No authentication, Presenter, backend, service, validation, localization,
role, session, or navigation behavior changed. Passive View, MVP boundaries,
and Qt-free Presenters remain intact.

## Files

- `desktop_client/app/views/login_view.py`
- `desktop_client/app/views/design_tokens.py`
- `desktop_client/tests/test_ui_foundations.py`
- `docs/piv/25-0-1-login-screen-layout-polish.md`
- `docs/piv/requirements-traceability.md`
- `docs/screenshots/task-25-0-1-login.png`
- `docs/screenshots/task-25-0-1-login-error.png`

## Validation

- Focused Login accessibility/behavior test.
- Focused Login layout geometry test at 1200×760.
- Full Desktop test suite.
- `python -m compileall backend desktop_client`.
- Normal and error-state screenshot inspection.

## Task 25.1 — Customer screen redesign

The Customer screen is now a reference pattern for management-screen
interaction:

1. Browse and search a spacious Customer list.
2. Single-click to select without leaving the list.
3. Open details by double-click, Enter, or the dedicated **View details**
   action.
4. Edit or delete only from the dedicated internal Customer Details page.
5. Return to the unchanged list, search text, filters, page, and selection.

The list keeps only the decision-making columns: Customer name, type, city,
and status. Phone, email, contact, notes, address, and audit dates remain
available in Customer Details. Search is always visible; sort, city, Customer
type, and active status are progressively disclosed under Advanced Filters.
No filter functionality was removed.

Final Task 25.1 polish compacts the Customer-specific header and scaffold,
places the RTL search field first in the reading flow, makes Search use the
existing primary-action treatment, groups optional filters with explanatory
text, gives the table more height and stronger name/city weighting, and centers
a bounded pagination control. Customer Details now separates Customer,
Contact, and System information. Create and Edit Customer dialogs now share an
in-dialog heading, grouped fields, required-field guidance, consistent
geometry, a bounded notes field, equal-size actions, and an existing-theme
primary Create/Save action.

The completed polish also replaces Refresh with a true Reset action that
clears every filter and sort through the existing View-to-Presenter filter
signal, simplifies the advanced-filter label to `סינון לפי`, removes nested
list/detail frames, formats counts as `לקוחות • N`, and supplies dedicated
first-use and no-results states with contextual Create or Reset actions. The
Customer dialog uses a wider two-column RTL layout so its normal 820×650
Desktop presentation requires no scrolling.

Customer creation remains a single signal into the existing
`CustomersPresenter.begin_create` / `submit_create` use case. The Customer-role
path in User Administration remains its distinct atomic user-provisioning use
case; no second standalone Customer-creation implementation was introduced.

No Presenter, service, backend, authorization, cache, CQRS, Event Sourcing, or
business-rule implementation changed.

Task 25.1 evidence is recorded in
`docs/piv/25-1-customer-screen-redesign.md`, with before/after list, filters,
details, create-dialog, and edit-dialog screenshots under `docs/screenshots/`.

## Next task

Do not begin another screen automatically. Continue Task 25 only after the
product owner explicitly selects the next bounded screen or visual-design
subtask.

## Task 25.2 — role-specific management UI standard (COMPLETE)

Customers, Instructors, and Managers now share one professional RTL management
language: grouped title/subtitle headers, independent creation actions,
search/reset toolbars, semantic resizable tables, centered pagination,
list-to-details navigation, information cards, equal detail actions, shared
dialogs, and the shared write-only password workflow.

Instructor and Manager screens no longer use the legacy split-pane layout.
Login email is read-only during edit. Manager edit changes the manager name
while the permanent login identifier remains unchanged. No screenshots or
visual artifacts were created for Task 25.2.
