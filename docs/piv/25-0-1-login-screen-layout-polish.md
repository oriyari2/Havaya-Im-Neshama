# PIV — Task 25.0.1 Login Screen Layout Polish

## What was created

The existing Hebrew RTL Login screen now uses a larger centered card, a clear
welcome/application/description/instruction hierarchy, stacked field labels,
wider full-width inputs and action, and deliberate vertical separation. The
feedback banner remains directly after the Password field and receives layout
space only when visible, so errors do not overlap the controls or displace the
card from its balanced composition.

No new design identity was introduced. Existing neutral colors, font tokens,
borders, radii, and control styling remain in use. A selector-specificity fix
allows the existing primary-button treatment to render in the Login panel and
keeps the button text visible.

## PRD support

- `NFR-01`: improves usability and readability of the primary Hebrew RTL
  sign-in flow.
- `NFR-09`: preserves accessible names and logical focus order while giving
  form controls explicit labels above each field and usable error placement.
- `NFR-10`: keeps the Login composition centered and balanced at the documented
  1024×640 minimum and at the 1200×760 default desktop size.
- PySide6/MVP course architecture: the change is confined to View composition
  and existing neutral styling; Presenters remain Qt-free and unchanged.

## Files changed

- `desktop_client/app/views/login_view.py`
- `desktop_client/app/views/design_tokens.py`
- `desktop_client/tests/test_ui_foundations.py`
- `tasks/25-desktop-visual-design-ui-ux-cohesion.md`
- `docs/piv/requirements-traceability.md`
- `docs/screenshots/task-25-0-1-login.png`
- `docs/screenshots/task-25-0-1-login-error.png`

## How to run

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m desktop_client.app.main
```

## Validation

```powershell
.\.venv\Scripts\python.exe -m unittest desktop_client.tests.test_ui_foundations.UiFoundationTests.test_login_accessibility_focus_rtl_and_duplicate_guard desktop_client.tests.test_ui_foundations.UiFoundationTests.test_login_layout_is_wide_stacked_and_centered
.\.venv\Scripts\python.exe -m unittest discover -s desktop_client\tests -p "test_*.py"
.\.venv\Scripts\python.exe -m compileall backend desktop_client
```

The layout test verifies the 520 px minimum card, 440 px minimum equal-width
fields, full-width button, labels above inputs, feedback between fields and
button, centered horizontal placement, and the intended information sequence.
Screenshots were captured at 1200×760 for both normal and error states.

## Screenshots

- [Normal Login state](../screenshots/task-25-0-1-login.png)
- [Login validation-error state](../screenshots/task-25-0-1-login-error.png)

## Next task

Wait for explicit product-owner direction. Do not start the next screen as part
of Task 25.0.1.
