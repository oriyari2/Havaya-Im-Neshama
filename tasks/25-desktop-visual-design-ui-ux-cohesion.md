# Task 25 — Desktop Visual Design and UI/UX Cohesion

## Status

**25.0.1 COMPLETE — LOGIN SCREEN LAYOUT POLISH**

The wider Task 25 visual-design phase has not started. Subtask 25.0.1 is the
layout-only preparation of the Login screen before colors, branding, icons,
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

## Next task

Do not begin another screen automatically. Continue Task 25 only after the
product owner explicitly selects the next bounded screen or visual-design
subtask.
