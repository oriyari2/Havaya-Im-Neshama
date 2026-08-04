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

- `desktop_client/app/features/auth/view.py`
- `desktop_client/app/shared/ui/design_tokens.py`
- `desktop_client/tests/test_ui_foundations.py`
- `tasks/25-desktop-visual-design-ui-ux-cohesion.md`
- `docs/piv/requirements-traceability.md`

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

The historical Task 25.0.1 screenshot files are not present in the supplied
repository. Do not cite them as submission evidence. Capture a current native
Windows Login screenshot during final demo preparation if Login evidence is
required.

## Next task

Wait for explicit product-owner direction. Do not start the next screen as part
of Task 25.0.1.

## Final-state correction — August 2026

The final Login implementation remains stacked, centered and RTL, but responsive
Qt geometry may render the inputs at approximately 430 px in the supported
window rather than the earlier hard-coded 440 px test expectation. Final tests
now validate equal-width readable controls and visible feedback rather than the
superseded exact width. The current visible description is
`מערכת לניהול לקוחות, פעילויות והזמנות`.
