# Task 25.5 - Branded Desktop Visual System

## Status

Phase 3 complete: Customers only.

Phase 1 remains the completed shared branded foundation. Phase 2 remains the
completed Dashboard styling phase. Bookings, AI Advisor, Login, and the final
cross-screen consistency pass remain pending. No Booking, AI Advisor, Login,
backend, presenter, API, RBAC, RAG, CQRS, Event Sourcing, repository, database,
or authentication work was implemented in this phase.

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

## Phase 3 Customers Implement

Used `design_reference/approved-customers.png` as the Customers visual direction
and `design_reference/activity-customers-hero.png` as the only Customers hero
asset.

Implemented only the existing Customers screen:

- added a restrained Customers list-page hero strip using the approved activity
  image;
- kept the existing `CustomersView` and `ManagementWorkspace` signal contracts;
- kept the existing RTL page title/subtitle and primary `לקוח חדש` action;
- kept the existing search input, search action, immediate sort combo, reset
  action, and filter emission behavior;
- kept the existing Customer table columns exactly as implemented:
  open action, customer name, type, city, and active status;
- kept the existing table population, row selection, double-click/open-action
  details flow, pagination footer, empty states, retry state, and feedback
  behavior;
- polished the Customers table through a scoped `customerTable` style property;
- added a small shared `ManagementWorkspace.add_list_header_widget` hook so the
  Customers hero is shown only on the list page and hidden with the normal list
  header on the details page.

No new Customer columns, status values, filters, metrics, actions, navigation,
dialogs, workflows, or mockup-only features were added.

The visual reference shows additional data columns such as phone, email, index,
and join/created date. Those were intentionally not implemented because the
current Customers screen is the functional source of truth and currently exposes
only the existing compact Customer list columns, with email/phone remaining in
search/details behavior.

## Phase 3 Customers RTL Alignment Repair

Applied a Customers-only visual alignment repair after review:

- moved the `לקוחות • N` result count to the right edge of the Customers list
  heading row;
- kept the `לקוח חדש` button in the existing RTL header action composition
  without changing the current hero height;
- made Customers toolbar controls render in the natural RTL order while keeping
  the existing search, sort, and reset behavior;
- kept Hebrew table headers and textual table cells explicitly right-aligned;
- preserved LTR alignment for naturally LTR detail values such as email, phone,
  and date-style metadata.

No Customer functionality, columns, data loading, sidebar, hero dimensions,
Dashboard, backend, Presenter, API, RBAC, CQRS, Event Sourcing, RAG, or database
logic changed.

## Phase 3 Customers Header/RTL Composition Repair

Applied a second Customers-only visual correction after review:

- moved the existing `לקוחות`, `ניהול לקוחות ופרטי קשר`, and `לקוח חדש`
  widgets into the approved `activity-customers-hero.png` hero composition;
- suppressed the old separate white Customers header card on the list page while
  preserving the same widget instances, object references, signal wiring, and
  create action behavior;
- kept the current hero height and image crop behavior;
- pinned the title/subtitle to the hero's right side and the existing
  `לקוח חדש` action to the bottom-left of the hero;
- tightened the `לקוחות • N` section title so it sits at the right edge above
  the table instead of spanning the row;
- kept the RTL search row order, explicit Hebrew table header/cell alignment,
  pagination, sidebar, Dashboard, Presenters, backend/API, RBAC, RAG, CQRS, and
  Event Sourcing unchanged.

Visual validation captured:

- `docs/screenshots/task-25-5-customers-header-rtl-composition.png`

## Files Changed

- `desktop_client/app/views/design_tokens.py`
- `desktop_client/app/views/dashboard_view.py`
- `desktop_client/app/views/customers_view.py`
- `desktop_client/app/views/management_workspace.py`
- `desktop_client/app/views/shell_view.py`
- `desktop_client/tests/test_ui_foundations.py`
- `desktop_client/tests/test_customer_views.py`
- `docs/screenshots/task-25-5-dashboard-instructor-shell.png`
- `docs/screenshots/task-25-5-dashboard-instructor.png`
- `docs/screenshots/task-25-5-dashboard-manager-shell.png`
- `docs/screenshots/task-25-5-dashboard-manager.png`
- `docs/screenshots/task-25-5-customers-manager-shell.png`
- `docs/screenshots/task-25-5-customers-manager-shell-1024.png`
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
- Existing Customers signals were preserved:
  `filters_requested`, `page_requested`, `customer_selected`,
  `retry_requested`, `create_requested`, `edit_requested`,
  `deactivate_requested`, `reactivate_requested`, and
  `change_password_requested`.
- Existing Customer create/edit/deactivate/reactivate/change-password dialogs
  and Presenter/service/API behavior were not changed.

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

Phase 3 focused validation:

- `QT_QPA_PLATFORM=offscreen`
- `.\.venv\Scripts\python.exe -m unittest desktop_client.tests.test_customer_views`
  - 16 tests passed.
- `.\.venv\Scripts\python.exe -m unittest desktop_client.tests.test_ui_foundations.UiFoundationTests.test_supported_minimum_keeps_pilot_regions_meaningfully_sized desktop_client.tests.test_ui_foundations.UiFoundationTests.test_customer_table_and_dedicated_details_page_use_supported_sizes desktop_client.tests.test_ui_foundations.UiFoundationTests.test_customers_accessibility_disabled_help_and_tooltips desktop_client.tests.test_ui_foundations.UiFoundationTests.test_management_modules_share_exact_customer_foundation_values desktop_client.tests.test_ui_foundations.UiFoundationTests.test_management_create_and_search_buttons_share_primary_style_role`
  - 5 tests passed.

Phase 3 visual validation:

- Instantiated the real PySide6 `ShellView` with `CustomersView` for the manager
  role.
- Populated the existing table with representative Customer rows.
- Captured screenshots under `docs/screenshots/`:
  - `task-25-5-customers-manager-shell.png`
  - `task-25-5-customers-manager-shell-1024.png`
- Compared the real screen with `design_reference/approved-customers.png`.
- Verified title/subtitle right alignment, reachable primary action, reachable
  search/sort/reset controls, readable high-density table, visible status text,
  reachable pagination, and no detected overlap at 1200x760 or 1024x640.
- Verified the Customers hero hides when opening the existing details page and
  returns when navigating back to the list.

Phase 3 RTL repair validation:

- Instantiated the real PySide6 `ShellView` with `CustomersView` for the manager
  role and representative Customer rows.
- Captured updated screenshots:
  - `docs/screenshots/task-25-5-customers-rtl-alignment-shell.png`
  - `docs/screenshots/task-25-5-customers-rtl-alignment.png`
- Verified the result count is right-aligned with the table edge, the
  search/filter row reads RTL, table headers and Hebrew textual cells are
  right-aligned, and email/phone/date-style details keep LTR readability.

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

The same offscreen Hebrew font-rendering limitation appeared in the Customers
screenshots. The source strings remain valid Hebrew, tests assert the live text
values and RTL alignment, and the visual validation was used for composition,
asset placement, table sizing, pagination reachability, and clipping/overlap.

## Next Task

Task 25.5 Phase 4 should implement only the Booking/Orders workspace styling
using the approved Orders reference. Do not begin Bookings until explicitly
requested.
