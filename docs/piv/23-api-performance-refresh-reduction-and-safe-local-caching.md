# Task 23 PIV — API Performance, Refresh Reduction, and Safe Local Caching

## Status

Implementation, automated validation, real-backend measurement, native-Windows
automation, architecture/security scans, and documentation are complete. The
requested exact commit and push close the task.

## Implementation and architecture summary

Task 23 adds one bounded `SessionPerformanceCache` at the desktop ApiClient
boundary. Authenticated GETs use resource policies, complete deterministic keys,
deep-copy isolation, LRU/memory bounds, TTL, optional SWR, and identical-flight
coalescing. Successful mutations invoke a documented resource invalidation
matrix. Login establishes `(generation, user_id, role)`; logout, 401 expiry,
identity change, and shutdown clear it.

Task 22's plain Presenter operation identities now support owner/key queue
removal and latest-intent replacement. The Qt adapter remains the only Qt-aware
executor. Mutations are explicitly non-cancellable after dispatch. The widened
screen migration preserves passive Views, Qt-free Presenters, unchanged
Services/ApiClient/FastAPI ownership, and all authorization/domain contracts.

## Files created

- `desktop_client/app/infrastructure/performance_cache.py`
- `desktop_client/tests/test_performance_cache.py`
- `desktop_client/tests/task23_measurements.py`
- `tasks/23-api-performance-refresh-reduction-and-safe-local-caching.md`
- `docs/piv/23-api-performance-refresh-reduction-and-safe-local-caching.md`

## Files modified

- Desktop composition/data/lifecycle: `desktop_client/app/api/client.py`,
  `desktop_client/app/infrastructure/qt_operations.py`,
  `desktop_client/app/models/operation.py`, `desktop_client/app/main.py`
- Presenters: Activities, AI Chat, Booking Assignments, Bookings, Customers,
  Dashboard, Instructors, Knowledge, Open Events, and Users
- Services: Activity, Auth, Booking, Customer, Instructor, Knowledge, and User
- Tests: background operations and Customers presenter
- Documentation: `ARCHITECTURE.md`, `docs/PROJECT-ROADMAP.md`, and
  `docs/piv/requirements-traceability.md`

No backend production file, API contract, database schema, `docs/PRD.md`,
Gateway, CQRS/Event Sourcing, or AI/RAG implementation changed.

## Every screen migrated

- Task 22 screens retained: Login, Dashboard, Customers/detail/owned profile,
  Instructors/detail/owned profile, and User Management.
- Task 23 additions: Activities/detail/image operations, Bookings/detail/history/
  create options/commands, assignment model/selector/commands, Open Events list/
  detail, Knowledge list/detail/mutations, and AI consultation.
- Shell navigation cancels inactive read owners and clears obsolete loading
  state. No session-restoration workflow exists to migrate.

## Cache policy and bounds

| Resource | TTL / freshness | Related invalidation |
|---|---|---|
| Dashboard | 15 s SWR | booking/assignment commands |
| Customers | 30 s SWR | Customer/contact and linked User changes |
| Instructors | 30 s SWR | Instructor and linked User changes |
| Users | 20 s SWR | User create/email/status; reset excluded |
| Activities | 60 s SWR | image or core Activity changes |
| Bookings | 20 s SWR | booking/assignment and affected Activity changes |
| History | 15 s hard | booking commands |
| Assignments | 10 s hard | assignment/booking commands |
| Open Events | 15 s SWR | booking/assignment/Activity changes |
| Knowledge | 20 s hard | knowledge mutations only |

Bounds: 128 entries, 8 MiB total estimate, 1 MiB per cacheable payload, 32
in-flight read identities, two refresh workers, four Qt workers, and 32 pending
Qt callbacks/operations. Existing image preview retention stays separate and
bounded to three; SWR retention stops 120 seconds beyond TTL; general cache
persistence and disk writes do not exist.

## Complete invalidation evidence

- User create: Users plus only the Customer/Instructor resource selected by
  role; Manager create touches Users only.
- User email/status: Users and potentially linked business presentation.
- Reset password: no display cache invalidation and no secret retention.
- Customer/contact: Customers + Users, not Instructors/Bookings/Dashboard.
- Instructor: Instructors + Users, not Customers/unrelated operational data.
- Booking/assignment: Bookings, history, assignments, Open Events, Dashboard.
- Activity core: Activities, Bookings, Open Events; image: Activities only.
- Knowledge: Knowledge only.

All invalidation runs after HTTP success. A failure neither populates nor clears
authoritative cache state. Ordered/page uncertainty uses a targeted subsequent
list read rather than optimistic row placement.

## Request identity, isolation, and no-secret evidence

Canonical keys include session generation, user, role, resource, path, entity/
ownership and every normalized parameter. Tests change page, page size, search,
filter/status, sort, and ownership individually and observe independent misses.
Session tests switch Manager -> Customer -> another Manager -> Instructor and
observe zero retained entries. Auth logout/expiry use the same clear boundary.

The store recursively rejects password, confirmation, access/refresh token,
token, secret, and credential keys; authentication, reset, AI consultation,
mutation requests, raw errors, and preview bytes never enter it. Values are
defensively copied and exist only in process memory.

## Coalescing, latest intent, and lifecycle evidence

Two concurrent identical reads produce one loader invocation and one
`coalesced` diagnostic count. Different identities do not join. Success/failure
always removes the flight registry. Capacity raises a friendly bounded error.

`replace()` asks the Qt pool to remove an older queued read. Already-running
`urllib` transport cannot be cancelled; its Python callback record is removed,
then presenter generation/current-resource checks suppress result and error.
Navigation updates the page first and clears obsolete loading state. Mutation
keys remain registered/running across navigation and focused tests observe their
completion. Qt runnable deletion races are safely treated as “already finished.”

## Request, refresh, and rendering evidence

- An identical fresh GET changes from one HTTP per visit to zero HTTP on return.
- Customers -> Users -> Customers and the five-page rapid sequence reuse valid
  entries; no speculative prefetch was added.
- Retry invalidates only the exact current list identity before fetching.
- Explicit search remains explicit; Open Events automatic search remains local,
  so no unnecessary debounce exists.
- Customer, Instructor, User, Activity, Booking, and Open Event list presenters
  compare the filter/payload signature and skip unchanged table reconstruction.
- A rendered list does not re-enter blocking full-page loading on cache reuse.
- Existing page/filter/selection restoration logic and paged backend queries
  remain intact.

## Real before/after measurement

Measurement uses the running FastAPI service and configured database through the
real desktop ApiClient on 2026-07-31; it is not a simulated-delay claim.

| Read | Uncached repeat | First cache-populating read | Cached return | HTTP on cached return |
|---|---:|---:|---:|---:|
| Dashboard | 1971.891 ms | 2057.860 ms | 0.049 ms | 0 |
| Customers | 2028.664 ms | 1978.949 ms | 0.542 ms | 0 |
| Instructors | 2408.315 ms | 1843.411 ms | 0.175 ms | 0 |
| Users | 1889.613 ms | 2021.075 ms | 0.511 ms | 0 |
| Activities | 2047.061 ms | 2006.964 ms | 0.378 ms | 0 |
| Bookings | 1936.675 ms | 2074.523 ms | 0.471 ms | 0 |
| Open Events | 1928.133 ms | 2226.619 ms | 0.093 ms | 0 |
| Knowledge | 1964.434 ms | 2066.311 ms | 0.084 ms | 0 |

The first read remains bounded by unchanged network/backend/database latency.
The improvement is an avoided request and immediate local copy, not faster
server execution. In that run the cache reported 13 hits, 12 misses, 13 stores,
one SWR stale hit, zero refresh failures, zero in-flight identities, and 12
entries/86,781 estimated bytes before disposal; logout/shutdown tests then
verify zero retained entries. The five navigation submissions measured 1.952–
5.129 ms. Customers -> Users -> Customers returned to useful Customers content
in 15.378 ms with zero HTTP on the return. Instrumented real Qt View calls were
8.935 ms for the one Customers table build, 1.608 ms for Users, 5.234 ms for
Instructors, and 3.090 ms total for two Dashboard render calls. Returning to
Customers produced no second table-build call.

## Automated and Windows validation

Focused Task 23 tests cover cache, lifecycle, latest intent, mutation survival,
request counts, rendering reuse, and affected presenters. The full desktop suite
contains 175 passing tests at the final evidence point.

The opt-in harness performs read-only authenticated application composition at
1024x640, 1200x760, and 1440x900 and produced the table above. A separate native
Qt `windows`-platform run passed 34 lifecycle, navigation, resize, supported-size,
View, and UI-foundation tests. It was scripted rather than human-driven; Task 22
and Task 21 already supplied manual Windows mutation/navigation evidence, and
Task 23 does not change backend mutation contracts. A fresh human interactive
run of all 44 requested gestures is not claimed.

## Validation commands and final evidence

- Focused Task 23/affected desktop: 115 passed.
- Full desktop: 175 passed.
- Full backend: 185 passed.
- Native Windows Qt lifecycle/View/foundation: 34 passed.
- `python -m compileall backend desktop_client rag`: passed.
- `git diff --check`: passed; CRLF conversion notices are informational.
- Presenter Qt, passive View/data access, desktop direct DB, secret retention,
  cache/session isolation, queue/worker bounds, stale callback, TODO/FIXME/
  debug, and backend-change scans: passed with no architecture violation.

## Limitations and remaining work

- `urllib` exposes no safe cancellation for an HTTP call already in progress;
  queued work is removed and running callbacks are invalidated instead.
- SWR reports freshness status but does not show an absolute “verified at” time.
- SWR stale retention is capped at 120 seconds beyond resource TTL.
- Memory size is a conservative serialized-JSON estimate, not exact CPython
  heap accounting.
- Server-side latency remains unchanged and is considered by Task 24 only when
  measured evidence justifies a compatible reliability/performance change.
- Native Windows automation passed; a fresh human interactive run of every
  requested gesture was not available in the managed execution environment.

Task 24 and Task 25 were not started.
