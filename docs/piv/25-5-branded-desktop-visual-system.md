# Task 25.5 - Branded Desktop Visual System

## Status

Phase 1 complete: inspect plus shared branded foundation only.

Dashboard, Customers, Bookings, AI Advisor, Login, and the final cross-screen
consistency pass remain pending. No screen-specific redesign was implemented in
this phase.

## Skill Used

The `havaya-desktop-ui` skill was used by reading and following
`skills/havaya-desktop-ui/SKILL.md`.

## Inspect

Inspected the PRD, traceability, Task 25.5 definition, prior Desktop/PIV
documents, all approved files under `design_reference/`, and the current Desktop
View/style implementation.

The existing reusable visual architecture is:

- `desktop_client/app/views/design_tokens.py` owns the global QSS and shared
  token constants.
- `desktop_client/app/main.py` applies the single application stylesheet.
- `desktop_client/app/views/ui_foundations.py` owns `PageScaffold`, semantic
  table sizing, request-state panels, feedback banners, focus/accessibility
  helpers, and table configuration.
- `desktop_client/app/views/management_workspace.py` owns the shared RTL
  management list-to-details composition.
- `desktop_client/app/views/management_common.py` owns shared primary-button
  roles, search toolbar, pagination, active badges, retry state, and shared
  confirmation dialogs.
- `desktop_client/app/views/shell_view.py` owns post-login shell/sidebar
  composition and navigation signal emission.

No backend/domain architecture was re-investigated or modified.

## Implement

Extended the existing shared styling system instead of creating a second QSS
system.

Implemented shared presentation rules for:

- brand, neutral, success, warning, and error palettes;
- typography hierarchy for page titles, section titles, summary/stat values,
  subtitles, metadata, labels, and body text;
- spacing, radii, subtle borders, and restrained elevation tokens;
- primary, secondary/default, and destructive button treatments;
- text inputs, combo boxes, search/filter controls, and filter chips;
- table header, row, alternating row, and selection styling;
- active/status badge styling and booking-status coloring;
- pagination through the existing shared footer button rules;
- navigation item default, hover, focus, and active states;
- page title/subtitle hooks and statistic-card primitive hook;
- AI user message, assistant message, and source/reference style hooks.

The shared post-login shell now uses the approved real logo from
`design_reference/logo.png`. Existing navigation items, role visibility inputs,
navigation signals, logged-in email display, and logout behavior were preserved.

## Files Changed

- `desktop_client/app/views/design_tokens.py`
- `desktop_client/app/views/shell_view.py`
- `desktop_client/tests/test_ui_foundations.py`
- `docs/piv/25-5-branded-desktop-visual-system.md`
- `docs/piv/requirements-traceability.md`

## Functional Boundaries Preserved

- No backend code changed.
- No API contracts changed.
- No authentication, authorization, RBAC, RAG, CQRS, Event Sourcing, Gateway, or
  database behavior changed.
- No Presenter changes were made.
- No new navigation destinations, filters, statuses, metrics, actions, or
  workflows were added.
- Desktop remains API-backed; no direct PostgreSQL/Supabase access was added.

## Validation

Focused validation:

- `QT_QPA_PLATFORM=offscreen`
- `.\.venv\Scripts\python.exe -m unittest desktop_client.tests.test_ui_foundations`
  - 29 tests passed.
- `.\.venv\Scripts\python.exe -m unittest desktop_client.tests.test_management_common desktop_client.tests.test_customer_views desktop_client.tests.test_activity_views desktop_client.tests.test_booking_workspace`
  - 40 tests passed.
- Direct Desktop DB-access scan:
  - `rg -n "psycopg|sqlalchemy|create_engine|SessionLocal|DATABASE_URL|SUPABASE|supabase|postgres|from app\.database" desktop_client`
  - no matches.

Required final validation for this phase was run after documentation updates and
produced:

- `.\.venv\Scripts\python.exe -m compileall backend desktop_client`
  - passed.
- `git diff --check`
  - passed, with only Git line-ending warnings for modified files.
- Full Desktop unittest discovery:
  - not clean. The suite reached
    `PresenterTests.test_ai_consult_503_shows_error_without_expiring_session_or_login_navigation`
    and failed because the current implementation returns the Hebrew
    AI-unavailable message while the test still expects the older English text.
    This is outside the Phase 1 styling files and was not changed here.
- Additional smaller Desktop slices passed for UI foundations, management
  common/dialog validation, customer/activity/booking/assignment/user/instructor
  views, services, and presenters except for the unrelated AI Presenter message
  expectation noted above.
- A few large mixed Qt batches exited abruptly after progress dots without a
  unittest failure summary; the individual modules relevant to this phase passed
  when run separately.

## PySide6/QSS Notes

QSS supports property selectors for reusable visual roles, so Phase 1 added
style hooks such as `buttonRole`, `statCard`, `aiMessage`, and `aiSource`.
Widgets whose dynamic properties change at runtime still need the existing
unpolish/polish pattern to refresh QSS reliably.

Qt stylesheets do not provide a portable CSS-like box shadow model. The shared
foundation therefore uses restrained borders, contrast, spacing, and color
hierarchy for elevation in this phase.

## Next Task

Task 25.5 Phase 2 should implement only the Dashboard screen styling using the
approved Dashboard reference and Dashboard hero image. All other screen-specific
phases must remain pending until explicitly requested.
