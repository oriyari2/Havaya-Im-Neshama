# Task 25.5 - Branded Desktop Visual System

## Status

Phase 2 complete: Dashboard only.

Phase 1 remains the completed shared branded foundation. Customers, Bookings,
AI Advisor, Login, and the final cross-screen consistency pass remain pending.
No Customer, Booking, AI Advisor, Login, backend, presenter, API, RBAC, RAG,
CQRS, or Event Sourcing work was implemented in this phase.

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

## Phase 1 Implement

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

## Phase 2 Dashboard Implement

Used `design_reference/approved-dashboard.png` as the Dashboard visual direction
and `design_reference/activity-dashboard-hero.png` as the only Dashboard hero
asset.

Implemented only the existing Dashboard screen:

- replaced the old `QGroupBox` visual treatment with branded `QFrame` stat
  cards and section panels;
- added a narrow top hero/header using the approved activity image;
- kept the existing RTL title/subtitle hierarchy in the Dashboard header;
- polished the existing role-specific summary cards with restrained accent
  colors;
- kept all existing Dashboard metrics and their meanings;
- kept the existing drill-down buttons only on the same metric cards that already
  had them;
- kept the existing quick-action row and signal routing, with the manager create
  action styled as the primary action;
- kept the existing upcoming/open-work booking tables and shared table
  configuration;
- preserved Manager, Instructor, and Customer card/shortcut differences.

No charts, notifications, new metrics, new actions, new navigation, fake data,
or additional imagery were added.

## Phase 2 Dashboard Repair

Repaired the Dashboard implementation after visual review found that the first
Phase 2 result was not close enough to the approved reference.

The repair kept the same Dashboard functionality and role-specific behavior, but
cleaned up the presentation:

- made the hero/header shallow and restrained;
- kept the approved Dashboard hero image, with a white fade so the title and
  subtitle sit on guaranteed contrast;
- pinned the hero composition so Hebrew header text stays on the clean side of
  the image while preserving RTL text;
- increased stat-card and drill-down button sizing so values, labels, and
  buttons do not clip;
- made quick actions equal-width and restored the manager create action's
  visible primary styling so there is no empty-looking action slot;
- gave Dashboard section panels and booking tables stable minimum heights and
  stretch so table content remains readable.

## Phase 2 Dashboard Layout Repair

Repaired only the Dashboard layout structure after a normal-window visual check
showed the manager Dashboard could be taller than the available shell content
area while the page itself did not scroll.

The root cause was the Dashboard's single non-scrollable `QVBoxLayout`: the
hero, two-row stats region, quick-action row, and two operational table sections
were all competing for the fixed shell page height. The table sections were
given stretch in that same layout, while the stat cards used fixed vertical
sizing. At the supported window height, Qt compressed/clipped the second stats
row instead of allowing the Dashboard page to scroll.

The repair keeps the shell/sidebar fixed and wraps only the Dashboard content in
a `QScrollArea`:

- `QScrollArea.setWidgetResizable(True)`
- vertical scrollbar `AsNeeded`
- horizontal scrollbar `AlwaysOff`
- scroll widget contains the existing hero, stats grid, quick actions, and both
  operational table sections.

The manager summary metrics now remain in a real 3-column x 2-row `QGridLayout`
with six current cards and actions preserved. Stat cards use a sensible minimum
height with preferred vertical sizing, avoiding a fixed total stats-container
height that can cut the second row. Both operational tables keep internal
vertical scrolling with bounded working heights so they neither collapse nor
consume unlimited page height.

## Phase 2 Dashboard Summary Correction

Applied a Dashboard-only correction after follow-up review:

- restored the existing `פתיחה` drill-down action on the `משובצים` summary
  card by wiring it to the already-existing `assigned_count` Dashboard signal
  path;
- kept the existing Presenter navigation behavior unchanged, where
  `assigned_count` opens the booking list with the current upcoming-date filter;
- made the Dashboard title and subtitle explicitly RTL/right-aligned inside the
  hero title area;
- made all summary card labels and values explicitly RTL/right-aligned;
- preserved the current hero image/layout, scrolling, tables, quick actions,
  sidebar, roles, Presenter, backend/API, RBAC, RAG, CQRS, and Event Sourcing
  behavior.

## Files Changed

- `desktop_client/app/views/design_tokens.py`
- `desktop_client/app/views/dashboard_view.py`
- `desktop_client/app/views/shell_view.py`
- `desktop_client/tests/test_ui_foundations.py`
- `docs/screenshots/task-25-5-dashboard-instructor-shell.png`
- `docs/screenshots/task-25-5-dashboard-instructor.png`
- `docs/screenshots/task-25-5-dashboard-manager-shell.png`
- `docs/screenshots/task-25-5-dashboard-manager.png`
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
- Existing Dashboard signals were preserved:
  `drill_down_requested`, `shortcut_requested`, and
  `create_booking_requested`.
- Existing Dashboard presenter/service contracts were not changed.

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

Phase 2 focused validation:

- `QT_QPA_PLATFORM=offscreen`
- `.\.venv\Scripts\python.exe -m unittest desktop_client.tests.test_views desktop_client.tests.test_presenters.PresenterTests.test_dashboard_loads_role_specific_sections desktop_client.tests.test_presenters.PresenterTests.test_dashboard_drilldown_maps_status_and_unassigned_without_cross_role_scope desktop_client.tests.test_ui_foundations.UiFoundationTests.test_global_theme_does_not_force_pilot_geometry_on_excluded_modules desktop_client.tests.test_ui_foundations.UiFoundationTests.test_dashboard_phase_two_uses_branded_sections_without_group_boxes`
  - 15 tests passed.

Phase 2 visual validation:

- Instantiated the real PySide6 `DashboardView` for manager and instructor roles.
- Instantiated the real `ShellView` with the Dashboard page for manager and
  instructor roles to validate the shared sidebar with the redesigned Dashboard.
- Saved screenshots under `docs/screenshots/`:
  - `task-25-5-dashboard-manager.png`
  - `task-25-5-dashboard-instructor.png`
  - `task-25-5-dashboard-manager-shell.png`
  - `task-25-5-dashboard-instructor-shell.png`
- Compared the screenshots against
  `design_reference/approved-dashboard.png`.

Phase 2 required final validation:

- `.\.venv\Scripts\python.exe -m compileall backend desktop_client`
  - passed.
- `git diff --check`
  - passed, with only Git line-ending warnings for modified files.

Phase 2 repair validation:

- `QT_QPA_PLATFORM=offscreen`
- `.\.venv\Scripts\python.exe -m unittest desktop_client.tests.test_views desktop_client.tests.test_ui_foundations.UiFoundationTests.test_dashboard_phase_two_uses_branded_sections_without_group_boxes desktop_client.tests.test_ui_foundations.UiFoundationTests.test_global_theme_does_not_force_pilot_geometry_on_excluded_modules`
  - 13 tests passed.
- `.\.venv\Scripts\python.exe -m compileall backend desktop_client`
  - passed.
- `git diff --check`
  - passed, with only Git line-ending warnings for modified files.

Phase 2 repair visual validation:

- Recaptured the real PySide6 `ShellView` with Dashboard for manager and
  instructor roles.
- Compared the repaired screenshots with
  `design_reference/approved-dashboard.png`.
- Result: the repaired Dashboard is no longer visually broken. The hero title is
  readable, the image is restrained, stat cards and quick actions are stable, and
  booking tables receive practical height.

Phase 2 summary correction validation:

- `QT_QPA_PLATFORM=offscreen`
- Real manager `ShellView` with `DashboardView("manager")` was instantiated at
  1200x760 and the restored `משובצים` `פתיחה` button was clicked.
- The click emitted the existing `assigned_count` drill-down signal.
- All six Dashboard drill-down buttons were present:
  `upcoming_count`, `pending_count`, `confirmed_count`, `cancelled_count`,
  `assigned_count`, and `unassigned_count`.
- The Dashboard title and subtitle reported right alignment and RTL direction.
- All six summary labels and values reported right alignment.
- All drill-down buttons were visible and the summary card grid had no detected
  horizontal overflow in the checked manager shell.

## PySide6/QSS Notes

QSS supports property selectors for reusable visual roles, so Phase 1 added
style hooks such as `buttonRole`, `statCard`, `aiMessage`, and `aiSource`.
Widgets whose dynamic properties change at runtime still need the existing
unpolish/polish pattern to refresh QSS reliably.

Qt stylesheets do not provide a portable CSS-like box shadow model. The shared
foundation therefore uses restrained borders, contrast, spacing, and color
hierarchy for elevation in this phase.

The offscreen PySide6 screenshot environment rendered Hebrew text as square
fallback glyphs even after adding `Segoe UI`, `Arial`, and `Tahoma` to the shared
font stack. The Dashboard source strings are valid UTF-8 Hebrew and focused
tests verify those visible text values. The limitation is documented as an
offscreen font-rendering artifact; the visual validation still confirmed layout,
hero image placement, card/section hierarchy, sidebar composition, and
role-specific Dashboard differences.

## Next Task

Task 25.5 Phase 3 should implement only the Customers screen styling using the
approved Customers reference and Customers hero image. Do not begin Customers
until explicitly requested.
