# Task 20 PIV — Neutral Desktop UX, Accessibility, and Request-State Foundations

## Status

Design and bounded implementation are complete. ChatGPT implementation audit,
human Windows visual/keyboard approval, commit, and push remain pending.

## Initial problem evidence

The post-Task-19 desktop is functionally complete across major modules but its
shared presentation foundation is inconsistent:

- page spacing, actions, filters, tables, details, dialogs, and feedback are
  assembled independently;
- `StatefulWidget` and `RetryState` overlap without a semantic state model;
- Login and shared loading call `QApplication.processEvents()`;
- accessible names/descriptions, explicit focus order, visible-focus rules,
  disabled explanations, contrast checks, and table semantics are incomplete;
- shell/sidebar, tables, splitters, dialogs, long text, tooltips, scrolling, and
  minimum-size behavior lack an application contract;
- final brand assets and rules are not approved and must not be invented;
- future background work has no common operation/module/session/generation
  identity contract.

## Repository areas inspected

- `AGENTS.md`, `README.md`, `ARCHITECTURE.md`, `docs/PRD.md`, the authoritative
  roadmap, and requirement traceability;
- relevant completed desktop Tasks/PIV 10, 11, 12, 14, 18, and 19;
- `desktop_client/app/main.py`, global stylesheet, composition/session flow;
- Login, Shell, Dashboard, Customer, Instructor, Activity, Booking, Open Event,
  Knowledge, AI, and profile Views;
- shared View helpers/widgets, forms, dialogs, tables, details, confirmations,
  pagination, badges, and retry state;
- presenter View protocols and current loading/submission guards;
- desktop tests for Views, presenters, shared management widgets, role
  navigation, state behavior, and pilot customer/login workflows;
- architecture scans for presenter Qt imports, View data imports, and direct
  desktop database access.

## Design decisions

- Pilot: Login, Shell, Customers, Customer/Contact dialogs, and shared state/
  retry components.
- Supported minimum: 1024×640 logical pixels; preferred start remains 1200×760.
  The minimum is based on the current 210-pixel Shell sidebar, Dashboard's
  three-column cards/shortcut row, and Customers' table/detail splitter;
  wrapping, splitter movement, and scrolling preserve reachability at the floor.
- Central temporary neutral tokens cover color, typography, 4/8/12/16/24/32-
  pixel spacing, 32/40/44-pixel controls, 16/20/24-pixel icons, 4/8/12-pixel
  radii, elevation, 0/120/200-ms motion, dialog geometry, and table density.
- `PageScaffold` defines one ordered hierarchy: `PageHeader`, optional
  `FeedbackBanner`, optional `ActionBar`, optional `FilterPanel`, stretching
  `MainContent` with optional `DetailPanel`, then optional footer/pagination.
- One dialog standard defines width, padding, spacing, platform button order,
  Enter/Escape, inline validation, scrolling, initial/restored focus, and safe
  destructive defaults.
- One feedback matrix separates inline validation, `FeedbackBanner`,
  `StatePanel`, future toast, modal error, and confirmation responsibilities.
- Shared passive components: page/header, action/filter/form/detail containers,
  feedback/state panels, and bounded table configuration.
- Existing `StatefulWidget`, `SearchToolbar`, `PaginationFooter`, `ActiveBadge`,
  `RetryState`, and `confirm_action` are adapted through compatibility paths.
- A Qt-independent request-state model represents idle/loading/success/empty,
  validation, authorization, connection/server, stale, and session-expiry states.
- A plain request identity defines session/module/operation/generation/resource
  currency; stale results never render.
- Task 20 removes `processEvents()` from migrated loading behavior but does not
  claim asynchronous execution. Task 29 owns the application-wide worker pattern.

## Architecture boundaries

```text
Qt-free Presenter
  -> plain RequestState / RequestIdentity
  -> passive feature View
  -> passive shared PySide6 components
  -> temporary neutral theme/tokens
```

- Presenters must not import PySide6.
- Views must not import services, API transport, database, or provider SDKs.
- Services and backend contracts do not change for Task 20.
- The composition root applies theme/minimum-size policy and retains session
  navigation responsibility.
- Shared widgets emit intent and render state; they do not make business or
  authorization decisions.

## Planned validation

- token/contrast and temporary-branding assertions;
- component signal/state/compatibility tests;
- every request-state transition and stale/session identity rule;
- accessible names/descriptions/labels, focus order, default/Escape behavior;
- RTL with LTR email/URL/ID/date values;
- 1024×640 resize/scroll/splitter/toolbar/dialog construction;
- long-value elision and full-value tooltips;
- Login/Shell/Customers/dialog pilot behavior and duplicate-action guards;
- full desktop and backend regression suites;
- compileall, whitespace validation, and MVP/data-boundary scans;
- manual Windows review at minimum, preferred, and large window sizes.

## Expected documentation synchronization

After implementation, review and synchronize:

- this PIV record with actual implementation and validation evidence;
- Task 20 specification and accepted deviations;
- `docs/piv/requirements-traceability.md`;
- `docs/PROJECT-ROADMAP.md` status;
- `ARCHITECTURE.md` from planned to implemented wording;
- README only if run behavior changes;
- actual test counts, manual screenshots/evidence, accepted limitations, and
  deferred Task 24–29 work.

Historical Task/PIV records remain unchanged and truthful.

## Explicit non-branding constraint

Task 20 must not choose final colors, font families, logo treatment, icons,
photography, activity-image treatment, or branded login/dashboard/AI identity.
Neutral tokens are temporary structural test values. Real identity work is
blocked on Task 24 product-owner assets and approval.

## Manual-review checkpoint

Before final approval and commit, the product owner and ChatGPT must review the
running pilot for keyboard use, focus visibility/order, Hebrew/RTL and mixed
direction, 1024×640 resizing, scrolling, table overflow/tooltips, action
hierarchy, all feedback states, input retention, destructive confirmation, and
compatibility of unmodified modules. Screenshots must be labeled temporary.

## Implementation evidence

Created:

- `desktop_client/app/models/request_state.py`;
- `desktop_client/app/views/design_tokens.py`;
- `desktop_client/app/views/ui_foundations.py`;
- `desktop_client/tests/test_ui_foundations.py`.

Modified only for the approved pilot/foundation:

- composition theme/minimum size in `desktop_client/app/main.py`;
- Login and Customers presenter orchestration/state behavior;
- shared `common.py` and `management_common.py` compatibility;
- Login, Shell, Customers, CustomerDialog, and ContactDialog Views.

The implementation provides neutral centralized tokens/theme, the standard
page hierarchy, feedback/state components, dialog/table/accessibility helpers,
plain request states/identities, duplicate prevention, and obsolete Customer-
detail rejection. No backend production code, backend test, API contract,
database schema, business rule, role rule, CQRS/Event Sourcing, RAG, or image
behavior changed.

Validation evidence:

- focused Task 20/pilot suite: 64 passed;
- full desktop suite: 136 passed;
- full backend suite: 169 passed;
- compileall (`backend`, `desktop_client`, `rag`): passed;
- MVP/data-boundary, direct-database, `processEvents()`, and debug-marker scans:
  passed;
- `git diff --check`: passed with informational line-ending notices only.

Automated offscreen validation covers construction, minimum size, request-state
rendering, stale rejection, duplicate guards, focus/validation, accessibility
metadata, RTL/LTR, dialog, and table contracts. Human interactive Windows review
at all three documented sizes remains pending and is not represented as passed.

The consolidated correction audit bounded global control/table selectors to the
pilot/shared compatibility targets, introduced meaningful Customers minimums and
two-row constrained actions/filters, made optional footer spacing truly collapse,
removed rigid dialog height, made Login/Customers protocols explicit, added a
Login reentrant guard, sanitized remaining raw Customer errors, and prevented a
stale detail completion from resetting current action state. Presenter behavior
tests were moved to presenter modules; foundation tests now include all phases,
global-theme/non-pilot compatibility, dialog keyboard behavior, and meaningful
1024×640 geometry. This does not claim asynchronous execution or screen-reader
certification.

Dashboard was reviewed for compatibility only. The foundations can later host
its cards, shortcuts, request feedback, and tables without changing MVP or API
boundaries, but Dashboard remains outside the Task 20 implementation pilot and
is not redesigned here.

## Table-layout manual-review correction

The product-owner review found that the former shared configuration could leave
trailing blank space while important intermediate text remained narrow. Task 20
now provides semantic Primary, Secondary, Technical, Compact, and Action column
policies backed by centralized minimum-width tokens. A bounded resize handler
distributes only available surplus: Primary receives the greatest share,
Secondary and Technical receive moderate shares, and Compact/Action retain their
readable minima. No per-update content autosizing is performed.

Customers, Contacts, and the existing shared booking-table compatibility path
consume this policy. If the semantic minima fit, the columns use the full table
viewport; otherwise normal horizontal scrolling exposes the genuine minimum
overflow. Elided full values remain available in escaped HTML tooltips with RTL
for Hebrew descriptive content and LTR for email, phone, and date values.

Offscreen evidence (Customer primary/secondary/compact; Contact primary/
secondary/compact) was: 1024×640 = 110/75/70 and 85/55/55, with 132 px and 75 px
minimum overflow; 1200×760 = 126/83/70 with 0 unused and 85/55/55 with 71 px
minimum overflow; 1440×900 = 189/114/70 and 90/57/55, both with 0 unused.
Automated tests observe fill, growth, constrained overflow, directional
tooltips, both pilot tables, and excluded-screen construction compatibility.
Interactive Windows visual approval remains pending.
