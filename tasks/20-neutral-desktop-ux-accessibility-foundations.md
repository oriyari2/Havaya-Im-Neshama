# Task 20 — Neutral Desktop UX, Accessibility, and Request-State Foundations

## 1. Context

Tasks 01–19 deliver the functional FastAPI/PySide6 MVP, role-safe desktop
modules, booking CQRS/Event Sourcing, Cloudinary images, and grounded RAG. The
authoritative remaining-work sequence in `docs/PROJECT-ROADMAP.md` begins with a
neutral desktop foundation before Task 21 adds User Administration and before
Task 24 supplies real brand decisions.

Task 20 is a structural PySide6 task. It must preserve behavior, role access,
MVP, passive Views, backend contracts, Hebrew/RTL support, and the existing
desktop-to-FastAPI boundary. It is not a visual-branding task.

Related requirements: `NFR-01`, `NFR-03` (request-state foundation only),
`NFR-07`, `NFR-09`, `NFR-10`, the PRD desktop information architecture, and the
course PySide6/MVP/modular-UI requirements.

## 2. Problem statement

The desktop is functionally broad but lacks one shared UI contract:

- `APP_STYLE` is a small ad-hoc stylesheet with temporary brown/beige values;
- pages define margins, spacing, titles, actions, feedback, tables, and details
  independently;
- `StatefulWidget`, `RetryState`, dialogs, and feature Views expose overlapping
  but inconsistent loading/error/empty/success behavior;
- loading sometimes calls `QApplication.processEvents()`, which is not a safe
  long-running-operation strategy;
- some controls are disabled without an accessible explanation;
- accessible names/descriptions, visible focus, and explicit focus order are
  mostly absent;
- the shell has a fixed 210-pixel sidebar and no documented minimum window;
- table column sizing, long-text handling, overflow, tooltips, splitter sizing,
  and scroll behavior vary by screen;
- action importance and destructive risk are communicated primarily by text;
- future asynchronous work has no shared semantic request-state or request-
  identity contract.

A repository-wide redesign in one task would be unsafe. A bounded pilot must
prove shared foundations while unmodified modules remain compatible.

## 3. Goal

Create reusable, neutral, accessible View foundations and semantic request-state
contracts, then validate them on a representative pilot:

- Login;
- application Shell/navigation;
- Customers table/detail screen;
- Customer and Contact dialogs;
- shared loading/empty/error/success/retry components.

The result must be usable at the documented Windows minimum resolution and give
Task 21 a stable table/form/page foundation. It must not choose final branding.

## 4. In scope

- Central neutral spacing, sizing, radius, color-state, and typography-role
  tokens.
- A single neutral stylesheet builder applied by the composition root.
- Shared page header/scaffold, action bar, filter/form section, detail section,
  data-table configuration, feedback banner, state panel, and dialog conventions.
- Adaptation rather than needless replacement of `StatefulWidget`,
  `SearchToolbar`, `PaginationFooter`, `ActiveBadge`, `RetryState`, and
  `confirm_action`.
- Consistent primary, secondary, and destructive actions.
- Accessible names/descriptions, explicit labels, focus visibility, logical tab
  order, disabled explanations, and contrast rules.
- RTL/Hebrew and mixed-direction conventions.
- Minimum window, resize, splitter, scroll, table overflow, long-text, and
  tooltip rules.
- A Qt-independent request-state model and View rendering contract.
- Duplicate-action prevention while the relevant request is active.
- Design-level operation/session/module/generation identity for stale-result
  rejection, without production-wide threading.
- Pilot migration and focused tests.
- Required documentation synchronization and manual review.

## 5. Out of scope

- Final brand colors, typography, logo placement, icons, photography, activity-
  image treatment, branded login/dashboard, or AI visual identity.
- Inventing or modifying the real organization's identity.
- Redesigning Dashboard, Activities, Instructors, Bookings, Open Events,
  profiles, Knowledge Management, or AI Chat beyond compatibility fixes.
- Application-wide worker/thread conversion; that belongs to Task 29.
- AI-specific cancellation/chat semantics; that belongs to Task 28.
- New business workflows, data fields, permissions, APIs, or backend changes.
- Mobile UI, global search, charts, reports, or decorative analytics.
- Changing presenter/service authorization behavior.

## 6. Current-state findings

### Shared UI

- `StatefulWidget` owns a centered `state_label` but has no typed state,
  accessible role, retry action, or consistent success/error appearance.
- `RetryState` duplicates part of that responsibility.
- `SearchToolbar`, `PaginationFooter`, and `ActiveBadge` are useful passive
  primitives but have no shared density, accessibility, tooltip, or style
  contract.
- Booking tables use one helper while entity screens configure tables directly.
- `resizeColumnsToContents()` can make long values expand tables unpredictably.

### Shell and Login

- `MainWindow` starts at 1200×760 but declares no minimum supported size.
- the sidebar is fixed to 210 pixels and offers no constrained behavior;
- navigation selection is functional but not accompanied by accessible current-
  page semantics;
- Login has labels and password masking, but no explicit accessible metadata,
  initial focus rule, stable Enter behavior contract, or shared feedback/loading
  component;
- Login and `StatefulWidget` call `QApplication.processEvents()` during loading.

### Operational screens and dialogs

- Customers is representative of dense CRUD screens: title, retry label,
  search, filters, actions, table, splitter, details, nested contacts, and
  pagination are assembled with ad-hoc margins and no scroll fallback.
- table columns lack a documented sizing/truncation/tooltip policy;
- selection-dependent controls become disabled but do not explain why;
- Customer/Contact dialogs provide labels and inline errors but lack shared
  field grouping, explicit focus order, accessible descriptions, standard
  action hierarchy, and resize/scroll rules;
- success and errors use different controls in different modules, and some
  presenters pass technical exception strings directly.

### Architecture and tests

- presenters remain Qt-free and Views remain data-layer-free; this boundary must
  not regress;
- current tests cover construction, signals, role visibility, basic loading,
  empty/error state, and submission disabling, but not accessible properties,
  focus order, RTL details, minimum size, overflow/tooltips, or state transitions.

## 7. UX principles

1. Structure before decoration: hierarchy, spacing, behavior, and accessibility
   are stable while visual identity remains temporary.
2. One obvious primary action per local context; secondary and destructive
   actions remain visually distinct and text-labeled.
3. State is adjacent to the content or operation it describes and never relies
   on color alone.
4. Loading preserves spatial stability and disables only conflicting actions.
5. Empty states explain what is empty and, when authorized, the next safe action.
6. Errors use friendly Hebrew, retain relevant user input, and expose retry only
   for safe/retriable reads.
7. Dense operational data uses available space efficiently without oversized
   empty panels.
8. Keyboard, screen reader metadata, RTL, truncation, and small-window behavior
   are part of the component contract, not later polish.
9. Shared components stay passive: they emit intent and render supplied state.

## 8. Architecture design

```text
Presenter (Qt-free)
  -> semantic RequestState / plain View protocol
  -> passive feature View
  -> shared passive PySide6 components
  -> neutral tokens and stylesheet
```

- `desktop_client/app/models/request_state.py` is Qt-independent and may be
  imported by presenters and Views.
- Presenters choose semantic state and determine whether a result is current.
- Views translate semantic state into Qt visibility, focus, accessible text,
  and enabled state; they do not classify network/domain errors.
- Shared PySide6 components accept text/state/value inputs and emit signals only.
- The composition root applies the neutral stylesheet and minimum-size policy.
- Services and `ApiClient` remain unchanged in Task 20.
- Existing feature protocols may gain narrowly scoped semantic methods such as
  `render_request_state(state)` only where the pilot proves the need. They must
  not accept Qt objects.
- Task 20 defines identity fields for future work; Task 29 implements reusable
  background execution across slow workflows.

## 9. Shared token design

Tokens are temporary and neutral. They are implementation constants, not final
brand choices.

Every migrated View must consume these constants through the token/theme module.
Numeric geometry, colors, type sizes, shadows, and animation timings must not be
repeated as hardcoded values in pilot Views or shared components.

### Spacing scale and control geometry

| Token | Value | Use |
|---|---:|---|
| `SPACE_1` | 4 px | compact internal gaps |
| `SPACE_2` | 8 px | related controls |
| `SPACE_3` | 12 px | form rows/toolbars |
| `SPACE_4` | 16 px | component padding |
| `SPACE_6` | 24 px | section separation |
| `SPACE_8` | 32 px | page-level separation |
| `CONTROL_HEIGHT_COMPACT` | 32 px | compact secondary controls |
| `CONTROL_HEIGHT` | 40 px | standard inputs/buttons |
| `CONTROL_HEIGHT_LARGE` | 44 px | primary login/dialog action |
| `ICON_SIZE_SMALL` | 16 px | inline/status icons |
| `ICON_SIZE` | 20 px | standard button/navigation icons |
| `ICON_SIZE_LARGE` | 24 px | prominent actions/state panels |
| `RADIUS_SMALL` | 4 px | inputs/badges |
| `RADIUS_MEDIUM` | 8 px | cards/panels |
| `RADIUS_LARGE` | 12 px | prominent containers |

Touch/mobile targets are not required, but keyboard/mouse targets must not be
compressed below their token height without documented exception.

### Temporary neutral colors

| Role | Value |
|---|---|
| application background | `#F5F6F8` |
| surface | `#FFFFFF` |
| alternate surface/hover | `#EEF1F4` |
| border | `#C8CDD4` |
| primary text | `#1F2933` |
| muted text | `#5F6B76` |
| focus indicator | `#1F6FEB` |
| selected background | `#DCEBFF` |
| disabled background/text | `#E5E7EB` / `#7A858F` |
| success | `#176B45` on `#E7F5ED` |
| warning | `#7A4D00` on `#FFF4D6` |
| error/destructive | `#A61B1B` on `#FDECEC` |

Hover, focus, selected, disabled, success, warning, and error must differ by
more than color where meaning matters: text, border, enabled state, and/or
accessible description must also change. Normal text targets at least 4.5:1;
large text and non-text focus/boundary indicators target at least 3:1. Exact
contrast calculations are part of validation.

### Typography roles

Task 20 uses the platform/application default font; it does not select a final
font family.

| Role | Size/line height | Weight |
|---|---|---:|
| application/page title | 24/32 px | 700 |
| section title | 18/26 px | 600 |
| body/input | 14/20 px | 400 |
| button/label | 14/20 px | 600 |
| supporting text | 12/18 px | 400 |
| summary value | 26/32 px | 700 |

System fixed-width font may be used only for technical IDs when it improves
legibility; it is not a brand typography decision.

### Elevation and animation

| Token | Value | Use |
|---|---:|---|
| `ELEVATION_NONE` | no shadow | embedded sections/tables |
| `ELEVATION_LOW` | 0 1 px 3 px at 12% black | cards and raised feedback |
| `ELEVATION_MODAL` | 0 8 px 24 px at 18% black | dialogs only |
| `DURATION_INSTANT` | 0 ms | reduced-motion or state replacement |
| `DURATION_FAST` | 120 ms | hover/focus feedback |
| `DURATION_STANDARD` | 200 ms | small visibility transitions |

Animation must never delay input, request-state rendering, or focus movement.
Reduced-motion preference uses `DURATION_INSTANT`. Qt stylesheet limitations may
mean a documented token has no pilot animation consumer; components must not
invent local timings.

### Dialog and table geometry

| Token | Value | Use |
|---|---:|---|
| `DIALOG_WIDTH_DEFAULT` | 520 px | ordinary create/edit dialog |
| `DIALOG_WIDTH_MAX` | 720 px | recommended maximum before content reflows |
| `DIALOG_PADDING` | 24 px | dialog content inset |
| `DIALOG_ROW_GAP` | 12 px | related form rows |
| `DIALOG_SECTION_GAP` | 24 px | section/action separation |
| `TABLE_CELL_PADDING_X` | 12 px | horizontal cell breathing room |
| `TABLE_CELL_PADDING_Y` | 8 px | vertical cell breathing room |
| `TABLE_ROW_HEIGHT` | 40 px | standard operational row height |
| `TABLE_HEADER_HEIGHT` | 40 px | standard table header height |

These values are logical pixels. The implementation must respect platform DPI
scaling and must not force a dialog beyond the available screen geometry.

## 10. Shared component design

### New foundations

- `PageScaffold`: the authoritative page hierarchy and responsive slots defined
  below.
- `PageHeader`: title, optional description, and a passive action slot.
- `ActionBar`: primary/secondary/destructive grouping with RTL-aware order.
- `FilterPanel`: labeled, wrapping/search/filter content with apply/reset intent.
- `FormSection`: titled/labeled field grouping and validation summary slot.
- `DetailPanel`: readable field/value presentation with wrapping and copy-safe
  technical values.
- `FeedbackBanner`: semantic success/warning/error/authorization/connection
  feedback; non-modal and screen-reader named.
- `StatePanel`: loading/empty/error display with optional safe retry signal.
- shared table configurator or small `DataTable` subclass: selection, header,
  stretch/interactive sizing, elision, accessible name, and tooltip-on-truncate.

Avoid a framework-sized abstraction. Components must be small QWidget classes
or helpers with direct behavior and no knowledge of services, roles, or domain
entities.

### Authoritative `PageScaffold` hierarchy

Every new desktop page and every later migrated page uses the same ordered
structure. Optional slots collapse completely when absent; pages must not insert
unmanaged top-level sections between these slots.

```text
PageScaffold (page margins: SPACE_6; section gap: SPACE_6)
├── PageHeader
│   ├── title
│   ├── optional description
│   └── optional page-level action slot
├── optional FeedbackBanner
├── optional ActionBar
├── optional FilterPanel
├── MainContent (stretch = 1)
│   ├── StatePanel overlay/replacement for loading, empty, or blocking error
│   └── page content (table, form, cards, or split workspace)
│       └── optional DetailPanel (normally the secondary splitter pane)
└── optional Footer / PaginationFooter
```

- `PageHeader` and the footer remain visually stable while request state changes.
- `ActionBar` contains page-scope actions; row/detail actions stay adjacent to
  their target and do not create a second page action bar.
- `FilterPanel` follows actions and precedes results consistently. Search is part
  of this area even when implemented through `SearchToolbar`.
- `MainContent` owns remaining vertical stretch. A `StatePanel` replaces content
  only when no valid content can be retained; non-blocking operation feedback
  uses `FeedbackBanner` without moving the page hierarchy.
- At normal widths, the optional `DetailPanel` is the secondary pane of a
  splitter. At constrained width it remains reachable by splitter movement or
  documented scrolling; it must not disappear.
- Below a component's comfortable width, action/filter groups wrap into ordered
  rows, then main content scrolls. Header, primary action, current state, and
  footer controls remain reachable. No horizontal overlap or silent control
  removal is allowed.

### Adapt existing components

- `StatefulWidget` delegates to the new `StatePanel`/`FeedbackBanner` while
  retaining compatibility wrappers during migration.
- `RetryState` becomes a compatibility wrapper or is absorbed by `StatePanel`;
  there must be one authoritative retry/state rendering contract.
- `SearchToolbar` gains an accessible label/name, standard action hierarchy,
  wrapping/minimum-width behavior, and busy-state support without owning filters.
- `PaginationFooter` gains accessible labels/descriptions and stable RTL order.
- `ActiveBadge` exposes semantic accessible text/property and never relies on
  color alone.
- `confirm_action` remains the shared modal destructive confirmation and receives
  standard button wording/focus; ordinary errors/successes remain non-modal.

### Application dialog standard

- Ordinary dialogs open at `DIALOG_WIDTH_DEFAULT` (520 px), may grow with content,
  and should not exceed `DIALOG_WIDTH_MAX` (720 px) without a documented workflow
  need. Available screen geometry always takes precedence.
- Content uses `DIALOG_PADDING`; fields use `DIALOG_ROW_GAP`; sections and the
  action row use `DIALOG_SECTION_GAP`.
- Use `QDialogButtonBox` platform semantics. In RTL, do not manually reverse the
  Windows/Qt order. There is one primary affirmative action and one Cancel action;
  destructive confirmation uses explicit destructive wording and Cancel/No.
- The primary action is the dialog default only for a valid, unambiguous form.
  Enter submits from single-line fields only when validation can run safely; it
  must not submit from multiline editors. Escape always closes/cancels without
  submission or mutation.
- Validation is inline beside/under the relevant field plus an optional form
  summary. Values are retained and the first invalid field receives focus.
- If content cannot fit vertically, the form body scrolls while the title/context
  and action row remain reachable. Dialogs must never require resizing beyond the
  current screen to reach Cancel or Save.
- Initial focus goes to the first editable field, or the safest context control
  in a confirmation. Destructive action never receives initial/default focus.
- The opener records the previously focused widget; after close, focus returns
  to that widget when it still exists and is enabled, otherwise to its containing
  page's logical action or content control.
- Destructive confirmations default to Cancel/No, describe the target and
  consequence, and require an explicit click or keyboard selection of the
  destructive action.

### Unified feedback strategy

| Mechanism | Use when | Do not use when |
|---|---|---|
| Inline validation | A correctable field/form value is invalid; retain input and focus the first invalid field | Transport failures, authorization denial, success, or page-level empty/loading state |
| `FeedbackBanner` | Non-modal operation success, warning, authorization denial, connection/server failure while valid context remains | Field-specific validation, confirmation, or a page with no renderable content |
| `StatePanel` | Main content is initially loading, empty, or unavailable because of a blocking read error; may offer a safe read retry | Mutation success, transient field errors, or feedback that should preserve visible content |
| Temporary notification/toast | Not introduced by Task 20; a later task may use it only for low-risk, non-actionable, nonessential confirmation that remains available elsewhere | Errors, validation, authorization, destructive outcomes, required instructions, or the only record of success |
| Modal error dialog | Only an exceptional blocking condition requires acknowledgment before the user can safely continue | Routine API/network errors, validation, or errors representable by `FeedbackBanner`/`StatePanel` |
| Confirmation dialog | An explicit irreversible, destructive, or materially consequential action needs informed consent | Navigation, ordinary saves, safe reads, or actions that are readily reversible and already clear |

Presenters select semantic `RequestPhase` and safe message content. Views select
the specified rendering mechanism; shared widgets do not classify domain or
transport errors.

## 11. Request-state model

### Qt-independent types

`RequestPhase`:

- `IDLE`
- `LOADING`
- `SUCCESS`
- `EMPTY`
- `VALIDATION_ERROR`
- `AUTHORIZATION_ERROR`
- `CONNECTION_ERROR`
- `SERVER_ERROR`
- `STALE`
- `SESSION_EXPIRED`

`RequestState` contains only plain data:

- `phase`;
- user-safe Hebrew `message`;
- `operation_key` identifying list/detail/save/login/etc.;
- `retryable`;
- `blocks_primary_action`;
- optional non-sensitive `diagnostic_id` for future Task 23 support.

`RequestIdentity` defines, but does not yet globally execute, the comparison
contract:

- `session_epoch`;
- `module_key`;
- `operation_key`;
- monotonically increasing `generation`;
- optional selected resource identifier.

### State behavior

| State | View behavior | Action behavior |
|---|---|---|
| Idle | no transient banner; content ready | actions follow selection/role rules |
| Loading | show operation-specific progress without clearing valid content unless necessary | disable only conflicting action and duplicate submission |
| Success | show non-blocking confirmation; preserve stable content/selection | re-enable actions after authoritative refresh |
| Empty | show helpful explanation and permitted next step | create may remain enabled for manager |
| Validation error | show near form/field and summary; retain values; focus first invalid field | allow correction/resubmit |
| Authorization error | friendly denial, no retry, no leaked details | forbidden action remains unavailable |
| Connection/server error | friendly banner, retain content; safe read retry only | mutation retry requires explicit user action and idempotency safety |
| Stale/obsolete | never render and never replace state/content | no action; record only sanitized diagnostics if needed |
| Session expired | composition root replaces workspace with Login | invalidate identities and ignore late completion |

Presenters own `_loading`/`_submitting` guards and request currency. Views render
state and enforce duplicate clicks defensively by disabling relevant controls.
`QApplication.processEvents()` must not be the request-state mechanism and is
removed from the migrated pilot. Task 20 does not pretend this makes network
calls asynchronous.

## 12. Accessibility rules

1. Every input has a visible label; placeholder text is supplementary only.
2. Interactive widgets receive meaningful `accessibleName`; descriptions explain
   format, purpose, risk, or disabled reason where needed.
3. Page/section headings have stable object names and hierarchy for tests.
4. Tab order follows visual reading/task order in RTL: page controls, filters,
   primary content, detail actions, pagination; destructive actions do not gain
   surprising default focus.
5. Focus is visible with a minimum 2-pixel indicator meeting 3:1 contrast.
6. Enter submits only in a clear single-purpose form; Escape closes dialogs
   without submitting; destructive confirmation defaults to Cancel/No.
7. Disabled selection-dependent actions expose a tooltip/accessible description
   such as “יש לבחור לקוח תחילה”; color is never the only explanation.
8. Validation errors remain visible, are associated by naming/description with
   the relevant field, and focus the first invalid control when the View is told
   which field failed.
9. Status and badges always include readable text.
10. Tables have accessible names, row selection semantics, readable headers,
    and keyboard selection.
11. Contrast is measured for neutral tokens; brand contrast is revalidated in
    Task 24/25 rather than assumed.
12. Modal dialogs have title, parent, initial focus, logical tab cycle, and one
    default primary action.

## 13. RTL/Hebrew rules

1. Application, pages, dialogs, forms, action groups, and navigation default to
   `RightToLeft`.
2. Hebrew prose and labels align right and wrap at word boundaries.
3. Emails, URLs, technical IDs, and opaque tokens use explicit LTR direction
   and left alignment inside the value/control while their Hebrew label remains
   RTL.
4. Phone numbers, currency, quantities, and dates use a consistent presentation;
   ISO timestamps/IDs remain LTR, while localized human-readable date labels
   remain RTL.
5. Table column order follows task importance in RTL; the primary identity
   column is visually first on the right. Technical/action columns stay narrow.
6. Dialog action order follows Qt platform semantics and is not manually reversed
   in a way that breaks Windows expectations.
7. Punctuation is included in localized messages and tested with mixed Hebrew/
   English values to prevent visual reordering ambiguity.
8. Placeholders are concise Hebrew guidance and never replace labels.
9. Elided text retains its full logical value in a tooltip; email/URL/ID tooltips
   preserve LTR direction.
10. User-entered text is not force-normalized or reordered by the View.

## 14. Layout and resize rules

- Supported minimum application size: 1024×640 logical pixels. The preferred
  starting size remains 1200×760. This is evidence-based: the current Shell uses
  a 210-pixel sidebar, leaving about 814 pixels for page content; the current
  Dashboard uses a three-column summary grid plus a single-row shortcut group;
  and Customers uses a two-pane table/detail splitter with nested contacts.
  At 1024×640, the Shell can retain a bounded 200–240 pixel sidebar, Dashboard
  can wrap shortcuts/cards without changing its information architecture, and
  Customers can keep both panes reachable through splitter movement and vertical
  scrolling. A larger minimum would unnecessarily exclude common 1366×768-class
  Windows displays after OS chrome; a smaller minimum would not reliably retain
  these three existing structures without hiding actions. Behavior below the
  minimum is not guaranteed.
- Top-level page margins use `SPACE_6`; compact shared components use
  `SPACE_2`/`SPACE_3`; sections use `SPACE_6` rather than arbitrary gaps.
- Shell sidebar uses a bounded width (recommended 200–240 px), not an
  unconstrained fixed-layout assumption; main content receives stretch.
- Pages do not impose a large fixed width. Forms may use a readable maximum
  width while tables/detail workspaces consume available space.
- Table/detail screens use a horizontal splitter at normal width, with sensible
  initial ratios and minimum pane widths. At the 1024×640 floor, nested details
  must remain reachable through scroll/splitter movement rather than clipping.
- Forms/dialog content uses a scroll area when vertical content can exceed the
  available screen; action buttons remain reachable.
- Tables use stretch for one descriptive column and interactive/content-based
  caps for the rest. Long values are elided, never allowed to force uncontrolled
  window growth, and expose full tooltips.
- Detail labels use fixed semantic label columns; values wrap/select as needed.
- Toolbars may wrap or use a two-row layout at the minimum size; controls must
  not overlap or disappear.
- Empty/loading/error panels reserve enough space to avoid severe layout jumps
  but do not create oversized blank regions.

## 15. Pilot screens

### Login

Validates labeled forms, accessible metadata, initial focus, Enter behavior,
validation/loading/error states, primary action, minimum-size centering, and the
removal of `processEvents()` as a loading convention.

### Application Shell/navigation

Validates root margins, bounded sidebar, selected navigation semantics, keyboard
focus, page stretch, email mixed-direction display, logout distinction, and
minimum window behavior without final logo/brand treatment.

### Customers

Chosen as the table-heavy pilot because it combines search, sorting, filters,
primary/secondary/destructive actions, pagination, row selection, a splitter,
detail fields, a nested contacts table, status badges, and every common request
state. It directly validates components needed by Task 21 User Administration
without touching booking/Event Sourcing behavior.

### Customer and Contact dialogs

Chosen as the representative form family because they include required and
optional data, email/phone mixed direction, inline validation, submit loading,
and retained values. They validate shared dialog/form conventions for Task 21.

### Shared state components

`StatefulWidget`/`RetryState` migration validates loading, empty, validation,
authorization, connection/server error, success, retry, and duplicate-action
contracts. Other screens keep compatibility wrappers until Tasks 25–28.

Dashboard, Bookings, Activities, Instructors, Open Events, Knowledge, AI, and
profile screens are compatibility-tested but not visually migrated in Task 20.

### Dashboard compatibility review (not a pilot migration)

The existing role-dependent Dashboard was inspected specifically for foundation
compatibility. Its title maps to `PageHeader`; request feedback maps to
`StatePanel`/`FeedbackBanner`; summary cards and booking tables fit
`MainContent`; and shortcuts map to a wrapping `ActionBar`. The token hierarchy
supports its titles, summary values, cards, table density, spacing, and focus
states. `RequestState` is independent of Dashboard query data and therefore does
not require a new presenter/backend contract. At the minimum size, its three-
column grid and shortcut row must be able to wrap during its later Task 25
migration. No Dashboard code, layout, behavior, API, graph, or branding is
changed in Task 20, and this compatibility finding does not add Dashboard to the
pilot.

## 16. Migration plan

1. Add Qt-independent request-state types and neutral token/theme modules.
2. Add small passive shared layout/state/table/form components.
3. Adapt existing shared widgets behind compatibility methods; do not break all
   feature protocols at once.
4. Apply the neutral theme and minimum-size policy in the composition root.
5. Migrate Login and Shell.
6. Migrate Customers and Customer/Contact dialogs.
7. Add focused widget/protocol/accessibility/resize/RTL/state tests.
8. Run the full desktop/backend regression suites and architecture scans.
9. Perform manual Windows review at 1024×640, 1200×760, and a larger window.
10. Record remaining module-specific migration work for Tasks 25–29.

## 17. File-level implementation plan

### Expected new production files

- `desktop_client/app/models/request_state.py` — semantic request phases, state,
  and identity data without Qt.
- `desktop_client/app/views/design_tokens.py` — temporary neutral numeric/color/
  typography-role constants with an explicit non-branding warning.
- neutral Qt stylesheet generation is colocated in `design_tokens.py`; the
  approved optional file split was reduced to keep one authoritative token/theme
  source.
- `desktop_client/app/views/ui_foundations.py` — bounded passive page/header/
  action/filter/form/detail/feedback/state/table foundations.

The exact split may be reduced during implementation if fewer files are clearer;
it must not become a generic UI framework.

### Expected modified production files

- `desktop_client/app/main.py` — apply neutral theme and 1024×640 minimum;
  preserve composition and role wiring.
- `desktop_client/app/views/common.py` — state compatibility and shared table
  behavior; remove migrated `processEvents()` usage.
- `desktop_client/app/views/management_common.py` — adapt search, pagination,
  badge, retry, confirmation, accessibility, and busy-state contracts.
- `desktop_client/app/views/login_view.py` — pilot migration.
- `desktop_client/app/views/shell_view.py` — pilot migration.
- `desktop_client/app/views/customers_view.py` — pilot table/detail migration.
- `desktop_client/app/views/customer_dialogs.py` — pilot form/dialog migration.
- `desktop_client/app/presenters/login_presenter.py` and
  `desktop_client/app/presenters/customers_presenter.py` only if semantic
  request-state protocol methods are necessary; no PySide6 imports.

### Expected test files

- new `desktop_client/tests/test_ui_foundations.py`;
- updates to `test_views.py`, `test_management_common.py`,
  `test_customer_views.py`, `test_customers_presenter.py`, and
  `test_presenters.py` only where pilot contracts change.

### Documentation

- `tasks/20-neutral-desktop-ux-accessibility-foundations.md`;
- `docs/piv/20-neutral-desktop-ux-accessibility-foundations.md`;
- `docs/piv/requirements-traceability.md`;
- `docs/PROJECT-ROADMAP.md`;
- `ARCHITECTURE.md`;
- `README.md` only if launch behavior or user-visible run instructions change.

### Files that must not change

- backend production and tests;
- database schema/migrations/seed data;
- RAG/Ollama/Cloudinary implementation;
- non-pilot feature behavior;
- `docs/PRD.md` unless a separately approved product requirement changes;
- historical Task 01–19/PIV records.

## 18. Acceptance criteria

1. Neutral tokens are centralized, documented temporary, and contain no claimed
   final brand decision.
2. Shared components are passive, small, reusable, and avoid domain/service
   imports.
3. Login, Shell, Customers, CustomerDialog, ContactDialog, and shared state
   components use the new foundations without functional or role regressions.
4. Existing unmodified screens remain compatible and usable.
5. Presenters remain free of PySide6; Views remain free of service/database
   access; desktop remains free of PostgreSQL access.
6. The evidence-based 1024×640 minimum is enforced/documented and pilot content
   remains reachable without overlap or clipped actions.
7. Focus order, visible focus, labels, accessible names/descriptions, table
   semantics, and disabled explanations meet the defined rules.
8. RTL and mixed-direction values render according to the documented policy.
9. Tables constrain long values and expose full text through tooltips.
10. Primary, secondary, and destructive actions are distinguishable without
    color alone.
11. All request phases have a deterministic semantic/View behavior.
12. Active operations prevent duplicate conflicting actions.
13. Stale/obsolete results are specified as non-renderable, and session expiry
    invalidates future request identities.
14. Pilot loading does not use `QApplication.processEvents()` as its mechanism.
15. Errors are friendly Hebrew and do not expose raw provider/developer details.
16. Focused/full tests, compileall, architecture scans, and whitespace validation
    pass.
17. Manual product-owner/ChatGPT review passes before commit.
18. Documentation and roadmap status are synchronized honestly.

## 19. Automated test plan

- Token tests: required roles/values exist, temporary warning is present, and
  contrast calculations meet thresholds.
- Shared widget tests: intent signals, state rendering, retry visibility,
  action hierarchy/properties, and compatibility wrappers.
- Request-state tests: every phase, duplicate guard, state transitions, stale
  non-render rule, session/module/generation identity comparison.
- Accessibility tests: non-empty accessible names/descriptions, visible labels,
  first invalid focus, disabled explanation, badge text, table names/headers.
- Focus tests: explicit Login/dialog order, Enter/Escape/default behavior.
- RTL tests: layout direction plus LTR email/URL/ID controls and mixed text.
- Resize/scroll tests: pilot construction and reachable controls at 1024×640;
  bounded sidebar; splitter minimums; dialog scroll; no toolbar overlap. A
  compatibility construction check covers Dashboard without migrating it.
- Table tests: selection, stable selected ID after refresh when present,
  sizing policy, elision, and full-value tooltip.
- Presenter/View protocol tests: plain request-state objects only, loading and
  duplicate transitions, no Qt imports.
- Existing pilot behavior tests: login, customer CRUD/contact actions,
  pagination, retry, deletion confirmation, input retention.
- Architecture scans:

```powershell
rg "PySide6|QPixmap|QImage|QLabel" desktop_client\app\presenters
rg "desktop_client\.app\.(services|api)|psycopg|DATABASE_URL|get_connection" desktop_client\app\views
rg "psycopg|DATABASE_URL|get_connection" desktop_client
```

- Required validation:

```powershell
.\.venv\Scripts\python.exe -m unittest desktop_client.tests.test_ui_foundations desktop_client.tests.test_views desktop_client.tests.test_management_common desktop_client.tests.test_customer_views desktop_client.tests.test_customers_presenter desktop_client.tests.test_presenters -v
.\.venv\Scripts\python.exe -m unittest discover -s desktop_client/tests -v
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
.\.venv\Scripts\python.exe -m compileall -q backend desktop_client rag
git diff --check
git status --short
```

## 20. Manual validation plan

On the supported Windows environment:

1. Start the backend and desktop using documented commands.
2. At 1024×640, 1200×760, and a larger window, inspect Login, Shell, Customers,
   CustomerDialog, and ContactDialog.
3. Complete Login entirely by keyboard; verify initial focus, Tab/Shift+Tab,
   Enter submission, loading, invalid credentials, and session-expiry message.
4. Verify Shell keyboard navigation, selected page, long/mixed-direction email,
   bounded sidebar, content stretch, and logout distinction.
5. On Customers, test empty, populated, loading, success, retriable connection
   error, non-retriable authorization error, search/filter/page, selection,
   detail/contact tables, long values/tooltips, disabled explanations, stable
   selection, and destructive confirmation.
6. In both dialogs, test long values, invalid fields, retained input, first-error
   focus, submit duplicate prevention, Escape, scrolling, and mixed-direction
   email/phone values.
7. Confirm no raw technical/provider message is displayed.
8. Verify unmodified modules still open and retain their existing behavior.
9. Capture neutral-foundation screenshots clearly labeled “temporary styling.”
10. Obtain ChatGPT architecture audit and product-owner manual approval before
    documentation synchronization and commit.

## 21. Documentation updates

- Task design and PIV planning record are created before implementation.
- Roadmap Task 20 becomes `Design approved`; implementation/audit/commit remain
  not started.
- Traceability marks `NFR-01`, `NFR-03`, `NFR-07`, `NFR-09`, and `NFR-10` as
  planned Task 20 coverage, not implemented coverage.
- `ARCHITECTURE.md` records the planned semantic request-state/passive component
  boundary without claiming implementation.
- README changes only if implementation changes startup or run behavior.
- Historical Task 01–19 and PIV evidence remains unchanged.
- After implementation, actual files, tests, counts, manual evidence,
  limitations, and roadmap status must replace plans without rewriting history.

## 22. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Shared component over-engineering | Limit components to repeated pilot evidence; prefer helpers/adapters over a framework |
| Functional regression during visual migration | Pilot only; retain compatibility methods; run complete desktop/backend suites |
| Presenter/View boundary erosion | Plain state models only; architecture scans; no Qt objects in protocols |
| Temporary styling treated as brand | Name/document tokens as temporary; no logo/font/final palette claims |
| Accessibility inferred rather than proven | Automated properties plus keyboard/screen-size manual review |
| `processEvents()` removal mistaken for async support | Document synchronous limitation; Task 29 owns background closure |
| State component hides valid content | Operation-local state; retain valid content on recoverable errors |
| RTL changes disrupt technical values | Explicit per-widget direction for email/URL/ID/date tests |
| Broad repository churn | Only pilot screens migrate; later modules remain Tasks 25–29 |

## 23. Deferred work for Tasks 24–29

- Task 24: approved logo, brand colors, typography guidance, imagery, and visual
  tone checkpoint.
- Task 25: branded Shell/Login/Dashboard and purposeful operational graph.
- Task 26: remaining manager screen migration and data-quality completion.
- Task 27: instructor/customer experience migration.
- Task 28: branded professional AI/Knowledge UX and AI-specific cancellation.
- Task 29: reusable application-wide background execution and remaining slow
  workflow closure.

## 24. Product-owner decisions

No branding decision is required or permitted for Task 20. Product-owner review
must confirm only:

- 1024×640 as the supported minimum desktop window;
- the pilot set and neutral structural direction;
- Hebrew wording for shared loading/empty/error/success states;
- that screenshots may show temporary neutral styling and are not final design.

Official identity decisions remain mandatory Task 24 inputs.

## 25. Definition of done

Task 20 is done only after:

- this design receives ChatGPT/product-owner approval;
- the bounded implementation satisfies every acceptance criterion;
- focused and full automated validation passes;
- architecture/security scans pass;
- the manual Windows/keyboard/RTL/resize/state review passes;
- no final branding is invented;
- implementation, tests, architecture, traceability, PIV, roadmap, and accepted
  limitations are synchronized;
- ChatGPT audit and required fixes receive final approval;
- the product owner approves the running pilot;
- Task 20 receives its own clean commit and push and roadmap status update.

## 26. Implementation record

Status: implementation complete; ChatGPT audit, human Windows visual review,
approval, commit, and push remain pending.

Implemented exactly within the approved pilot:

- Qt-independent `RequestPhase`, `RequestState`, and `RequestIdentity` types;
- centralized temporary neutral tokens and stylesheet builder;
- passive `PageScaffold`, header/action/filter/form/detail, feedback/state,
  accessibility, mixed-direction, and table foundations;
- compatible `StatefulWidget`, `RetryState`, search, pagination, badge, and
  booking-table behavior;
- Login, Shell, Customers, CustomerDialog, and ContactDialog migration;
- 1024×640 minimum enforcement, bounded Shell navigation, accessible metadata,
  focus order, validation focus/input retention, disabled explanations, table
  elision/tooltips, and duplicate-action guards;
- generation/resource identity checks preventing an obsolete Customer detail
  response from replacing a newer selection.

Dashboard and every other non-pilot module remain visually unmigrated. Shared
booking-table compatibility changed only to consume the approved table helper;
no feature behavior, backend, API, database, authorization, CQRS/Event Sourcing,
RAG, or image workflow changed.

Validation completed before audit:

- focused Task 20/pilot suite: 64 tests passed;
- complete desktop suite: 136 tests passed;
- complete backend suite: 169 tests passed;
- compileall for `backend`, `desktop_client`, and `rag`: passed;
- presenter-Qt, View-data-layer, direct-desktop-database, `processEvents()`, and
  temporary-debug scans: passed;
- `git diff --check`: passed (line-ending notices only).

Automated offscreen validation covers the documented state, focus, RTL/LTR,
table, dialog, stale-response, duplicate-action, and minimum-size contracts.
Human visual/keyboard inspection on an interactive Windows desktop at 1024×640,
1200×760, and a larger window remains an approval checkpoint and is not claimed
as completed by automated execution.

### Audit correction pass

The consolidated pre-approval audit corrected concrete defects without adding
scope:

- control/table stylesheet selectors are bounded to the pilot, Task 20 dialogs,
  Shell, state controls, and tables explicitly configured through the shared
  helper; excluded feature controls are not forced into pilot geometry;
- Customers uses separate search and filter rows at constrained width, explicit
  table/details minimums, horizontal and vertical splitters, and a two-row contact
  action grid so important controls remain reachable at 1024×640;
- optional `PageScaffold` footer content now collapses completely when absent;
- Customer/Contact dialogs use the standard minimum and recommended maximum width
  without a rigid height, retain a scrollable body, label buddies, validation
  association/focus, Enter/Escape behavior, and focus restoration;
- Login now has a presenter-owned reentrant duplicate guard;
- Login/Customers View protocols are explicit, raw Customer conflict/unknown
  exception text is not displayed, and stale detail completion cannot reset the
  current request's enabled state;
- presenter-owned identity, invalidation, stale-result, sanitized-error, and
  guard-release tests live in presenter test modules; View tests cover all phases,
  optional slots, bounded global-theme compatibility, keyboard/dialog behavior,
  meaningful minimum-size geometry, and non-pilot construction.

This remains synchronous request orchestration. The generation/session/resource
contract protects the currently implemented reentrant/stale boundaries and is
ready for later workers, but it is not represented as application-wide async
protection; Task 29 remains responsible for that work. Automated tests validate
Qt metadata and keyboard events only. Human screen-reader/assistive-technology
and interactive Windows visual review remain pending.

### Table-layout manual-review correction

Product-owner Windows review confirmed that the earlier shared table helper
could leave unused viewport space while intermediate descriptive columns stayed
at Qt default widths. The corrected helper assigns every configured column one
reusable semantic policy: Primary text, Secondary text, Technical, Compact, or
Action. Centralized token minimums protect readable values; remaining viewport
width is distributed with Primary receiving the largest weight, Secondary and
Technical receiving moderate weight, and Compact/Action remaining narrow.

The policy is resize-event driven and does not run content-based autosizing.
When semantic minimums fit, configured columns consume the complete viewport;
horizontal overflow occurs only when their combined readable minimums exceed
it. Customer and Contact tables declare their column semantics explicitly, and
the shared booking-table compatibility helper uses the same foundation without
redesigning excluded screens. Full values remain in direction-aware HTML
tooltips: Hebrew descriptive values are RTL and email, phone, and date values
are LTR.

Offscreen geometry at the three review sizes recorded Customer primary/
secondary/compact widths of 110/75/70 px at 1024×640 (132 px required minimum
overflow), 126/83/70 px at 1200×760 (0 unused), and 189/114/70 px at 1440×900
(0 unused). Contact widths were 85/55/55 px (75 px required minimum overflow),
85/55/55 px (71 px required minimum overflow), and 90/57/55 px (0 unused).
Focused tests observe viewport fill, proportional expansion, constrained-size
overflow, both pilot tables, directional tooltips, and excluded-screen
compatibility. Interactive human visual approval remains pending.
