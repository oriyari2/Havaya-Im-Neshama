# Task 23 — API Performance, Refresh Reduction, and Safe Local Caching

## Status

**DESIGN APPROVED — IMPLEMENTATION COMPLETE — VALIDATION COMPLETE**

Task 23 is the second Phase 2 performance increment. It completes the
whole-desktop migration onto Task 22's bounded execution boundary, adds a
session-safe request/cache boundary, and reduces redundant HTTP and rendering
work. It does not make the backend faster and does not start Task 24 or 25.

## Problem statement and observed problem

Task 22 made the bounded pilot non-blocking, but reopening a page still issued
the same request, rapid navigation retained obsolete reads, identical reads
could run concurrently, and unchanged list payloads rebuilt tables. The
reported Customers -> Users -> Customers path therefore showed a loading reset
and repeated server latency even though the first Customers response remained
valid. Live localhost measurements also showed roughly two seconds per ordinary
uncached read, making avoided requests materially valuable.

## Goal and PRD traceability

Provide immediate, bounded, authorization-safe desktop reuse while preserving
all product and architecture behavior. This advances `NFR-03` responsiveness,
`NFR-06` controlled failures, `NFR-07` MVP boundaries, and `NFR-08` bounded,
maintainable infrastructure. It changes no functional PRD requirement.

## Scope

- Inventory every reachable screen and request pattern.
- Centralize authenticated GET caching, deterministic identities, coalescing,
  resource TTLs, bounds, diagnostics, and invalidation in the desktop data
  boundary.
- Extend latest-intent execution to Activities, Bookings/history/form options,
  assignments, Open Events, Knowledge Management, and AI consultation while
  retaining the Task 22 screens.
- Retain visible data on safe reopening, avoid unchanged table rebuilds, cancel
  or suppress obsolete reads, and preserve non-cancellable mutations.
- Add focused deterministic tests and real-backend measurement evidence.

## Explicit exclusions

- No backend production, API-contract, schema, authorization, CQRS/Event
  Sourcing, Gateway, AI/RAG/Ollama, branding, or visual redesign changes.
- No speculative prefetch, transport-level HTTP cancellation claim, persistent
  cache, cache of login/consultation requests, or optimistic domain mutation.
- No Task 24 reliability/observability expansion and no Task 25 visual system.
- `docs/PRD.md` remains unchanged.

## Architecture constraints

```text
Passive PySide6 View
  -> Qt-free Presenter + plain operation identity
  -> bounded Qt execution adapter / session cache
  -> Service
  -> ApiClient
  -> unchanged FastAPI contract
```

Workers never access widgets. Presenters import no Qt. Views access no service,
HTTP, repository, database, cache, or domain boundary. The cache lives at the
ApiClient infrastructure edge so all services share one authenticated session
scope.

## Whole-application performance inventory

`Entry/refresh` lists HTTP reads. Detail identity always includes the entity ID;
list identity includes normalized page, page size, search, filter, status,
date, sort, and ownership inputs supplied by the screen.

| Screen/module | Entry/refresh, detail, mutation requests | Search/filter/page/render behavior before Task 23 | Classification and implemented policy | Supersession/invalidation |
|---|---|---|---|---|
| Login/session | `POST /auth/login`; no restoration request exists | Blocking work was already migrated in Task 22 | Authentication; never cached | Duplicate guarded; login starts a new user+role+generation scope; logout/401 clears it |
| Dashboard | dashboard summary plus role-scoped booking/open-event lists | Repeated on every entry; complete sections rebuilt | 15 s SWR for constituent reads; retain rendered content | Latest `load`; booking mutations invalidate dashboard |
| Customers | paged `/customers`; `/customers/{id}`; contacts; create/edit/deactivate | Explicit search/filter/sort/page; list and detail reloaded; unchanged table rebuilt | 30 s SWR, session scoped, separate list/detail/page keys | Latest list/detail; exact retry invalidation; Customer mutations invalidate Customers and linked User presentation |
| Customer-owned profile | owned `/customers/{customer_id}` | One owned detail on entry | Customers 30 s SWR; ownership/entity in key | Page invalidation suppresses obsolete callback; Customer mutation invalidates |
| Instructors | paged `/instructors`; `/instructors/{id}`; mutations | Explicit search/filter/sort/page; unchanged table rebuilt | 30 s SWR | Latest list/detail; Instructor mutations invalidate Instructors and Users |
| Instructor-owned profile | `/instructors/me` | Repeated owned profile read | Instructors 30 s SWR; role/user/session scope prevents sharing | Page invalidation; Instructor mutation invalidates |
| User Management | paged `/users`; `/users/{id}`; create/email/status/reset | Explicit search/role/status/page; unchanged table rebuilt | 20 s SWR; password reset payload/result never cached | Latest list/detail; role-aware create invalidation; reset password does not refresh business data |
| Activities | paged `/activities`; detail; image metadata; public preview; mutations | Explicit filters/page; preview already had bounded three-entry memory LRU | Activity JSON 60 s SWR; external image bytes remain in existing three-preview cache only | Latest list/detail/preview; image mutation invalidates Activities only; core mutation also invalidates affected Booking/Open Event names |
| Bookings | role-scoped paged list; detail; create options; commands | Explicit filters/date/page; list and detail were synchronous outside pilot | 20 s SWR list/detail; 15 s hard history; reference reads use resource policy | Latest list/detail/options; commands are non-cancellable and invalidate bookings/history/assignments/open-events/dashboard |
| Booking history | `/bookings/{id}/history` | Loaded with detail; manager only | 15 s hard expiry | Booking commands invalidate; detail identity suppresses stale history |
| Booking assignments | assignment model, instructor selector pages, assignment commands | Selector pagination/filter; previously synchronous | 10 s hard operational cache plus Instructor reference policy | Latest model/selector; assignment mutation is non-cancellable and invalidates booking-related resources |
| Open Events | list and detail | Local automatic text filter (no HTTP, so no debounce needed); full row rebuild | 15 s SWR | Latest list/detail; Booking/Activity mutations invalidate |
| Knowledge Management | sources list/detail and content mutations | Full list refreshed after mutation; no table-heavy rendering | 20 s hard expiry; no SWR because administrative freshness matters | Latest list/detail; mutations invalidate only knowledge entries |
| AI Chat | `POST /api/ai/consult` | User-explicit submit; long request; duplicate guarded | Non-cacheable sensitive operational read | Obsolete callback suppressed on navigation; no RAG behavior change |
| Shell/navigation | no HTTP itself | Changed page immediately but old work could remain queued | Non-cacheable orchestration | Page owner cancellation, queued removal when possible, callback invalidation, newest page remains active |

List endpoints already request the server-supported page rather than downloading
all rows. Automatic Open Events filtering is local and cheap; every server-side
search is explicit-submit, so adding debounce would add latency without reducing
requests. Image downloads and decoding remain bounded by Task 19 and are never
placed in the general JSON cache.

## Baseline and performance budgets

The checked-in measurement harness performs authenticated reads through the
real `ApiClient` and native application composition. The pre-change behavioral
baseline is one HTTP request and a blocking visible reload on each page return.
A local-backend run on 2026-07-31 measured uncached repeats at 1,890–2,408 ms
across Dashboard, Customers, Instructors, Users, Activities, Bookings, Open
Events, and Knowledge. Task 23 targets remain:

- click/submission under 100/50 ms respectively;
- cached useful content under 150 ms and zero duplicate HTTP;
- one HTTP for identical concurrent reads;
- zero obsolete rendering, cross-session leakage, duplicate mutation, or
  unbounded queue/cache growth.

The final measured table and environment limitations are recorded in the PIV.

## Cache policy matrix

| Resource | TTL | SWR | Payload limit | Stale-on-refresh-failure | Mutation triggers |
|---|---:|---|---:|---|---|
| Dashboard | 15 s | yes | 1 MiB | retain + non-blocking warning | Booking command/assignment |
| Customers/profile/contacts | 30 s | yes | 1 MiB | retain + warning | Customer/contact/User-linked mutation |
| Instructors/profile | 30 s | yes | 1 MiB | retain + warning | Instructor/User-linked/assignment-related mutation |
| Users | 20 s | yes | 1 MiB | retain + warning | User create/email/status; not password reset |
| Activities JSON | 60 s | yes | 1 MiB | retain + warning | Activity/image mutation |
| Bookings | 20 s | yes | 1 MiB | retain + warning | Booking command, assignment, affected Activity |
| Booking history | 15 s | no | 1 MiB | no; hard reload | Booking command |
| Assignments | 10 s | no | 1 MiB | no; hard reload | Assignment/Booking command |
| Open Events | 15 s | yes | 1 MiB | retain + warning | Booking/assignment/Activity mutation |
| Knowledge | 20 s | no | 1 MiB | no; hard reload | Knowledge mutation |
| Login, password/reset payloads, AI consult, public image bytes, mutations/errors | none | no | none | never retained | not applicable |

Global bounds are 128 entries, 8 MiB estimated serialized JSON, 1 MiB per
resource payload, 32 in-flight identities, two background refreshes, four Qt
workers, and 32 pending Qt operations. The separate Task 19 preview cache stays
at three decoded previews.

## Cache keys and session isolation

Keys are canonical JSON over session generation, user ID, role, resource, path,
and recursively normalized parameters. Empty/`None` parameters are removed,
dictionary keys are sorted, and all response-shaping entity, ownership, page,
page-size, search, status, filter, date, sort, and relationship IDs remain.
Responses are deep-copied on store and return. A new login identity or role
increments generation and clears entries/in-flight consumers; logout, 401
expiry, and shutdown clear the complete scope. No disk persistence exists.

## Coalescing, navigation, and cancellation rules

- The first complete request identity owns the HTTP load. Concurrent identical
  consumers wait on the same bounded flight and receive defensive copies.
- A failed flight stores no exception or response and is removed before retry.
- `replace(key)` removes a safely queued older read and invalidates its callback.
- A running `urllib` request cannot be transport-cancelled; its record/callback
  is invalidated and its result cannot render.
- Navigation immediately changes the stack, clears obsolete loading state, and
  cancels each inactive presenter owner. Current page/resource generation is
  still checked at callback time.
- Mutations (`submit`, `mutation`, `mutate`, `delete`) are never queue-cancelled
  after dispatch; duplicate guards remain until authoritative completion.

Thus queue removal, callback invalidation, stale suppression, and unavailable
transport cancellation are distinct and are not overstated.

## Complete invalidation matrix

| Successful mutation | Invalidated resources | Deliberately preserved |
|---|---|---|
| Manager User create | Users | all business/booking/activity/knowledge data |
| Customer-role User create | Users, Customers | Instructors, bookings, activities, knowledge |
| Instructor-role User create | Users, Instructors | Customers, bookings, activities, knowledge |
| User email/status | Users, Customers, Instructors (linked role is not in request identity) | bookings, activities, knowledge |
| Password reset | none; secrets never cached | all displayed business data |
| Customer/contact create/edit/deactivate | Customers, Users | Instructors, bookings, dashboard, activities, knowledge |
| Instructor create/edit/deactivate | Instructors, Users | Customers, bookings unless an assignment command also occurs |
| Booking command | Bookings, history, assignments, Open Events, Dashboard | Customers, Users, Activities, Knowledge |
| Assignment add/remove | Bookings, history, assignments, Open Events, Dashboard | Users, Customers, Activities, Knowledge |
| Activity core mutation | Activities, Bookings, Open Events | Users, Customers, Instructors, Knowledge |
| Activity image mutation | Activities only | Bookings/Open Events and all unrelated resources |
| Knowledge mutation | Knowledge only | all operational resources |

Invalidation happens only after successful HTTP mutation completion. Presenter
refreshes preserve its filter/page identity; uncertain ordered list placement is
handled by a targeted authoritative list refresh rather than an unsafe local row
insertion.

## Freshness and error behavior

Fresh entries return immediately. Hard-expired entries reload. SWR entries stay
visible while one of at most two refreshes runs. Safe refresh failure retains
the stale value and emits a non-blocking freshness warning with retry available;
it does not mark the item freshly verified. Stale retention is capped at 120
seconds beyond TTL, after which the entry is discarded and hard-reloaded.
Initial load failures use existing
sanitized view feedback. A 401 synchronously clears the token/session cache and
dispatches session expiry, so cached presentation cannot hide authorization
failure. Failed mutations leave authoritative cached state unchanged.

## Rendering-performance behavior

Customers, Instructors, Users, Activities, Bookings, and Open Events retain the
last formatted list signature and do not call the table rebuild method for an
unchanged filter/payload. Dashboard retains its rendered sections. Reopening a
rendered list does not start a blocking loading reset. Existing semantic tables,
selection restoration, pagination, filters, and Task 19 bounded preview behavior
remain unchanged; no View/business responsibility was added.

## Acceptance criteria

- All reachable justified reads use Task 22 execution and the central policy.
- Customers -> Users -> Customers returns cached content without another HTTP,
  visible clearing, or unchanged table rebuild.
- Complete identities coalesce exactly one in-flight HTTP and separate different
  page/filter/sort/ownership/session requests.
- Latest navigation stays active; obsolete result/error/loading callbacks do not
  render; capacity remains bounded.
- Mutations survive navigation, reject duplicates, and apply the matrix only
  after success.
- Logout/session expiry/identity change leave zero entries and no data leak.
- Secrets, AI consults, login, preview bytes, errors, and mutation payloads are
  never cached or persisted.
- Full desktop/backend regression, compile, whitespace, architecture/security
  scans, real measurements, and supported-size Windows smoke complete.

## Automated test plan

Focused tests cover miss/hit/defensive copy, every query dimension, hard/SWR
expiry, refresh failure, coalescing, failure cleanup, bounds, LRU eviction,
secret/large-payload rejection, role/user/session isolation, logout semantics,
targeted and related invalidation, password-reset exclusion, request counts,
latest-intent queue removal, mutation survival, stale callback suppression,
shutdown, responsiveness, and unchanged-table rendering. Full desktop and
backend suites guard authorization and domain behavior.

## Manual Windows validation plan

Use the approved demo Manager, Instructor, and Customer accounts without
recording their credentials. At 1024x640, 1200x760, and 1440x900 validate login,
every role-visible page, Customers/Users return paths, rapid navigation, window
move/resize, repeated details/search/filter/page actions, representative
Customer/Instructor/User mutations and linked screen reconciliation, stale
refresh warning, logout/cross-role isolation, and shutdown during work. Record
what is native-interactive, scripted-native, or unavailable; do not fabricate.

## Documentation and completion criteria

Synchronize this task, PIV 23, traceability, roadmap, and the approved
architecture section. README changes only if operator instructions change.
Task 23 closes only after exact test totals and validation evidence are recorded,
the exact commit is pushed to `origin/main`, and the tree is clean.
