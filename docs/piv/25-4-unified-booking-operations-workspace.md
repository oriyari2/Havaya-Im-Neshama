# Task 25.4 - Unified Booking Operations Workspace

## Architectural finding

Open Events is not a separate entity. `GET /bookings/open-events` queries the
Booking projection for upcoming, instructor-required Booking Activities that
lack an active assignment. Its detail endpoint returns the same Booking header
plus Booking Activity assignment requirements. Task 25.4 therefore integrates
it as the **waiting for instructor assignment** queue in Bookings and removes
the duplicate navigation page. The projection endpoint remains unchanged and
is reused by the unified workspace.

Booking mutations remain CQRS commands that append immutable events with
optimistic concurrency. No Booking row/history is physically deleted.

## Unified Desktop flow

Bookings now uses the shared management workspace: header, compact summary
queues, framed search/sort/filter toolbar, semantic RTL table, fixed per-row
Details action, pagination, dedicated Details hero/cards, shared feedback and
module-home reset. Single click selects; action, double-click and Enter open
Details; Back preserves current list controls.

Verified summary queues are:

- Pending approval: upcoming `NEW` projection count.
- Waiting for instructor assignment: upcoming instructor-required Bookings
  with at least one Booking Activity lacking an active assignment; selecting
  it uses the existing Open Events projection.
- Approved: upcoming `CONFIRMED` Bookings. Assignment readiness remains a
  separate, accurately named concern because the list API has no
  all-activities-assigned filter.

No rejected state exists in the domain and none is displayed.

The table contains Open, Customer, Activity, event time, location,
participants, and status. Status labels retain their domain values and use
text plus semantic treatment. Instructor/customer responses remain scoped and
commercially restricted by the backend response models.

Booking Details groups Booking, Customer, and System information, manager-only
immutable history, and manager-only Activity-scoped assignments. Valid actions
are shown only for the current status. Cancellation uses cancellation wording
and preserves history.

## Searchable entity selectors

`SearchableEntitySelector` is the reusable RTL ID-backed selector used for
Customer, Activity, and Instructor choices. It supports contains completion,
keyboard navigation, readable contextual labels, loading/empty/error states,
and rejects arbitrary typed text because submission reads only an ID belonging
to an actual item. Activity choices exclude inactive records. Changing the
Activity clears Instructor selection.

Create options use bounded active-entity pages rather than unbounded datasets.
The existing APIs have no dedicated remote typeahead contract, so the bounded
results are filtered locally. Instructor assignment reuses the selector and
debounces the existing remote Instructor query by 300 ms. The backend remains
authoritative for activity membership, active state, conflicts, optimistic
version, and any assignment eligibility not represented by a dedicated API.
Instructor assignment remains optional at creation and otherwise occurs from
Booking Details, matching the existing workflow.

## Backend/Desktop capability audit

| Capability | Classification | Notes |
|---|---|---|
| Create Booking | Implemented in Desktop | Manager/customer roles; real Customer/Activity IDs |
| Search | Implemented for the bounded visible result page | Backend has no Booking search parameter |
| Sort | Implemented as event-time order | Repository order is event time then creation time |
| Status/date filters and pagination | Implemented in Desktop | Existing list contract |
| Customer/Activity/Instructor filters | Backend only in this compact revision | API remains available; selectors are used in forms |
| Approval (`NEW` to `CONFIRMED`) | Implemented in Desktop | Manager-only Event-Sourced status command |
| Rejection | Intentionally unsupported | No domain status/command exists |
| Cancellation/completion | Implemented in Desktop | State-aware manager actions, immutable history |
| Schedule/price/location/participants/notes edit | Implemented in Desktop | Separate versioned commands |
| Assignment/removal/reassignment | Implemented in Desktop | Reassignment is remove then assign through existing commands |
| Open Events | Implemented as unified queue | Derived projection, not separate entity |
| Booking history | Implemented for Manager | Readable event summaries; raw payloads hidden |
| Replay endpoint | Intentionally hidden | Maintenance/verification operation, not normal operator action |
| Customer scoping | Implemented server-side and reflected read-only | Own bookings only |
| Instructor scoping | Implemented server-side and reflected read-only | Assigned bookings only, commercial fields excluded |
| Physical deletion | Intentionally unsupported | Event history and projections are preserved |
| Availability/qualification selector hints | Recommended for later | No dedicated eligibility API; command validates current rules |
| Open Event selector in Create | Intentionally absent | Open Event is a derived Booking queue, not a selectable entity |

## Validation

Focused tests cover summary queues, derived Open Events filtering, list/detail
navigation, status actions, assignments, role visibility, selector filtering
and IDs, stale dependency clearing, inactive exclusion, validation, RTL,
loading/empty behavior, and window ownership. Backend Booking query, creation,
assignment and Event Sourcing suites remain authoritative for domain behavior.

No screenshots, generated images, Knowledge Management work, or AI Advisor
work is included.

Run the focused regression from the repository root:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\Scripts\python.exe -m unittest desktop_client.tests.test_booking_workspace desktop_client.tests.test_booking_assignments_presenter desktop_client.tests.test_assignment_views desktop_client.tests.test_assignment_service desktop_client.tests.test_services desktop_client.tests.test_presenters desktop_client.tests.test_views backend.tests.test_booking_queries backend.tests.test_booking_event_sourcing backend.tests.test_booking_creation_roles backend.tests.test_assignment_queries -q
.\.venv\Scripts\python.exe -m compileall backend desktop_client
git diff --check
```

The Presenter Qt scan verifies that presenters do not import PySide6, and the
Desktop database scan verifies that the client does not import a PostgreSQL
driver, open database connections, or read `DATABASE_URL`.

## Files changed

- `desktop_client/app/main.py`, navigation and Dashboard wiring: one Booking
  destination and integrated unassigned queue.
- `desktop_client/app/views/bookings_view.py`: unified list, queues, Details,
  history and assignment workspace.
- `desktop_client/app/views/booking_dialogs.py`,
  `desktop_client/app/views/assignment_dialogs.py`, and
  `desktop_client/app/views/entity_selector.py`: shared RTL ID-backed selection
  flow.
- Booking presenter/service/formatting and design tokens: orchestration,
  bounded form options and semantic state presentation.
- Focused Desktop tests: navigation, selectors, role/state visibility,
  assignment, list/Details actions and RTL behavior.
- Parent Task 25 and requirements traceability: Task 25.4 completion evidence.

## Task 25.4.1 - Booking UI polish

The final polish replaces the Details-page assignment tree with compact
per-activity cards. Unassigned activities show an amber state and one primary
assignment action; assigned activities show the Instructor, a green state,
and replace/remove actions. Assignment and replacement continue through the
existing searchable, debounced Instructor dialog and existing assignment
commands.

The permanent filter row is replaced by an RTL child popover anchored to the
toolbar. Its collapsible sections expose only filters supported by current
contracts: one Booking status, the derived unassigned queue, one Activity and
a date range. Active filters render as individually removable chips. No new
top-level window, backend endpoint, authorization rule or domain status was
introduced. Create/Edit labels, headings and Hebrew fields now enforce RTL
alignment explicitly.

The Booking sort menu also offers `שם לקוח`. The Desktop sends the whitelisted
`customer_name` value through the existing list service; event-time sorting
supports explicit nearest-first (`event_at`) and farthest-first
(`event_at_desc`) choices. The projection orders
by `customers.name ASC` before `LIMIT/OFFSET`, with event time and creation time
as stable tie-breakers. Reset restores the default event-time order.

## Next

Stop after Task 25.4.1 and wait for approval.
