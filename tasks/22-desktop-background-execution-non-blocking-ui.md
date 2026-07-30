# Task 22 Audit — Desktop Background Execution and Non-Blocking UI

## Status

**DESIGN APPROVED — IMPLEMENTATION COMPLETE — VALIDATION COMPLETE**

This document records the approved boundary and completed implementation of the
first performance task after Task 21. Commit and push evidence are recorded in
the Task 22 PIV.

## Why Task 22 is next

Most desktop presenters currently call synchronous HTTP services on the Qt UI
thread. Loading indicators exist, but network, database-backed API, upload,
preview, dashboard, booking, and AI calls can block interaction. Performance and
responsiveness now precede visual redesign and remaining AI expansion. Task 22
therefore establishes the safe execution/lifecycle foundation required by later
performance tasks and reused by all later UI and AI work.

## Objectives

1. Inventory and measure desktop operations that can block the Qt event loop.
2. Define one reusable background-execution boundary without importing Qt into
   Presenters or business/data access into Views.
3. Keep the UI responsive during justified long-running work.
4. Define operation identity across session, module, operation, generation, and
   resource so obsolete completion never renders.
5. Define cancellation, timeout, duplicate-action, logout/session-expiry,
   navigation, shutdown, error, and cleanup behavior.
6. Migrate only a bounded representative pilot selected by the later design;
   Tasks 23–24 close wider request/refresh/performance concerns.
7. Establish measurable responsiveness evidence before visual redesign.

## Acceptance criteria

- A measured inventory identifies blocking desktop calls and prioritizes a
  bounded pilot by latency and user impact.
- The approved execution mechanism has explicit ownership in an adapter or
  composition boundary; Presenters remain Qt-free and Views remain passive.
- Pilot operations do not block keyboard, window movement/resizing, navigation,
  or repaint while work runs.
- Loading blocks only conflicting actions; unrelated safe interaction remains
  available.
- Duplicate conflicting submissions cannot start concurrently.
- Every completion is checked against current session/module/operation/
  generation/resource identity before rendering.
- Navigation, selection change, logout, session expiry, and application shutdown
  invalidate obsolete work safely.
- Cooperative cancellation is used where supported; otherwise results are
  ignored safely and resources are released.
- Timeouts and cancellation produce friendly non-technical state without
  exposing tokens, URLs, credentials, SQL, or response bodies.
- Bearer tokens remain confined to the FastAPI client and are never transferred
  to public/external URLs or worker logs.
- No worker accesses or mutates PySide6 widgets outside the UI thread.
- Exceptions are delivered to the UI thread through a safe plain-result/error
  contract and never disappear silently.
- No unbounded thread, task, callback, result, or memory accumulation occurs.
- Existing authorization, API contracts, CQRS/Event Sourcing, Gateway, and RAG
  behavior remain unchanged.
- Focused concurrency/lifecycle tests, full desktop/backend regression,
  compileall, architecture/security scans, and manual Windows responsiveness
  checks pass.

## Affected desktop modules

Audit coverage includes:

- `desktop_client/app/main.py` composition, session, navigation, and shutdown;
- API client/service call boundaries and bearer-token lifecycle;
- Task 20 `RequestState`/`RequestIdentity` contracts;
- shared loading, feedback, retry, dialog, and action-disable components;
- Login/session restoration where network work occurs;
- Dashboard and role-specific summary/detail loading;
- Customers, Users, Instructors, Activities/images, Bookings/history/
  assignments, Open Events, profiles, Knowledge Management, and AI Chat calls;
- existing Task 19 preview-download cancellation/cache behavior as compatibility
  evidence, not as a new generic cache design;
- desktop tests and application composition tests.

The later design must select a smaller pilot. Audit coverage does not authorize
converting every operation in one task.

## Affected backend modules

No backend production change is expected for the execution foundation. Existing
FastAPI endpoints, authorization, request/response models, database schema,
repositories, booking commands/queries/events/projections, image Gateway, and
RAG services remain unchanged.

Read-only timing and endpoint-behavior inspection is expected. If a measured
blocking defect requires a backend contract change, Task 22 must stop and obtain
explicit architectural approval; query/API optimization belongs primarily to
Task 23.

## Architecture impact

The intended boundary is:

```text
passive PySide6 View
  -> user intent
Qt-free Presenter
  -> plain operation request / RequestIdentity
execution adapter owned by desktop composition/infrastructure
  -> existing Service -> ApiClient -> FastAPI
  <- plain success/error/cancel result
UI-thread dispatcher
  -> Presenter currency check -> passive View render
```

Qt worker/thread objects must not enter Presenters. Views must not call services
or own retry/business decisions. Services remain synchronous endpoint adapters
unless the approved design establishes a plain non-Qt interface. The desktop
still never accesses PostgreSQL directly.

Task 22 changes scheduling/execution mechanics only. It must preserve MVP,
server-side authorization, CQRS/Event Sourcing, Gateway isolation, role-aware
RAG grounding, and read-only AI boundaries.

## Documentation impact

The later design/implementation cycle is expected to synchronize:

- this Task 22 document from audit to approved design and evidence;
- `docs/piv/22-desktop-background-execution-non-blocking-ui.md` after authorized
  implementation;
- `docs/PROJECT-ROADMAP.md` status;
- `docs/piv/requirements-traceability.md`, especially `NFR-03`, `NFR-06`,
  `NFR-07`, `NFR-08`, and responsiveness evidence;
- `ARCHITECTURE.md` only for the implemented execution boundary;
- README only if launch/runtime/user guidance changes.

The PRD remains unchanged unless an approved product requirement changes.

## Implementation risks

| Risk | Required mitigation |
|---|---|
| Qt widgets touched from worker threads | Plain results plus UI-thread dispatcher; thread-affinity tests |
| Qt leaks into Presenters | Interface/import scans and plain operation ports |
| Stale result overwrites current screen | Session/module/operation/generation/resource identity check |
| Logout token/session race | Invalidate epoch, suppress completion, clear sensitive references |
| Duplicate mutations | Per-operation conflict guards retained until completion |
| Cancellation interrupts a committed backend mutation | Distinguish request cancellation from server outcome; refresh authoritative state |
| Worker/task leak on navigation or shutdown | Owned lifecycle registry, bounded concurrency, deterministic cleanup |
| Every trivial call moved to a worker | Evidence-based threshold and bounded pilot |
| Error swallowed across thread boundary | Typed plain result/error delivery and test coverage |
| UI appears responsive but data races increase | Deterministic concurrency tests and serialized conflicting actions |
| Phase 3 redesign enters scope | Preserve current visuals except required progress/cancel states |
| Task 23 optimization enters scope | Measure and report; defer query/refresh/cache optimization |

## Recommended implementation order

1. Measure representative calls and document UI-thread blocking evidence.
2. Classify operations as trivial, read-only slow, mutation, streaming/AI, or
   external media; select a bounded pilot.
3. Specify the plain operation/result/cancellation/lifecycle interfaces.
4. Specify the Qt execution adapter, UI-thread dispatcher, ownership registry,
   concurrency bounds, and shutdown behavior.
5. Map existing `RequestIdentity` and session epoch into completion currency.
6. Define mutation cancellation semantics and authoritative refresh behavior.
7. Add deterministic adapter/lifecycle/stale/logout/duplicate/error tests before
   migrating the pilot.
8. Implement the adapter and composition wiring, then migrate pilot operations.
9. Run latency/responsiveness measurements and manual Windows interaction checks.
10. Run focused/full regressions, compileall, architecture/security/whitespace
    scans, and synchronize documentation.
11. Await complete audit and approval before commit/push.

## Estimated complexity

**High.** The feature surface is unchanged, but execution and lifecycle behavior
crosses composition, session, navigation, services, state identity, errors, and
shutdown. Incorrect threading can cause races, crashes, duplicate mutations,
stale rendering, or token exposure. Complexity is bounded by selecting a small
pilot and deferring API/query/refresh/cache optimization to Task 23.

## Explicitly out of scope

- visual redesign, branding, or screen-wide layout migration;
- new modules, screens, roles, permissions, or domain behavior;
- backend query optimization, broad API redesign, or caching (Task 23);
- reliability/security/observability closure beyond execution safety (Task 24);
- new AI/RAG/Ollama/semantic-search behavior;
- Windows packaging or release preparation;
- unbounded conversion of every synchronous call.

## Implemented pilot

The bounded pilot moves the following operations behind the shared execution
boundary:

- authentication login;
- Dashboard summary and role-specific section loading;
- Customer directory list, detail, create/edit with primary-contact update,
  delete, and owned Customer profile loading;
- Instructor directory list, detail, create/edit, delete, and owned Instructor
  profile loading;
- manager User Administration list, detail, create, email update, password
  reset, activation, and deactivation.

Searches in this pilot are explicit-submit searches, so no keystroke debounce is
needed. Broader refresh/query optimization and caching remain Task 23.

## Implemented execution and lifecycle rules

- Production composition owns one `QtOperationExecutor` with four workers and a
  maximum of 32 active/queued operations.
- Presenters depend only on the plain `OperationExecutor` contract. Their unit
  tests use `ImmediateOperationExecutor`; no Presenter imports Qt.
- Worker results and errors are delivered on the UI thread. Workers never hold
  or manipulate widgets.
- Presenter operation identity rejects stale list/detail completion and blocks
  duplicate conflicting mutations.
- Page changes invalidate work owned by the previous pilot Presenter. Logout,
  session expiry, and application close invalidate all Presenter identities and
  executor callbacks.
- Cancellation is cooperative result suppression. A request already accepted by
  FastAPI may still finish server-side; the obsolete desktop result is ignored.
- Capacity errors and service failures remain friendly and do not expose
  credentials, tokens, SQL, response bodies, or implementation diagnostics.

## Measurement evidence

A deterministic representative 200 ms service call was used because test and
CI environments do not provide stable production network latency:

| Measurement | Before | After |
|---|---:|---:|
| UI-thread occupation by simulated call | approximately 200 ms | operation submission under 50 ms |
| 20 ms Qt UI heartbeat during call | blocked until completion | fired while work was running |
| result callback thread | UI thread only because call was synchronous | explicitly dispatched to UI thread |

The test verifies behavior rather than claiming network/API acceleration. Task
22 removes UI-thread waiting; Task 23 owns request-count, query, and cache work.

## Validation gate

Implementation is complete only with focused lifecycle and presenter tests,
full desktop/backend suites, compileall, architecture/security scans,
whitespace validation, and manual Windows responsiveness evidence. Final
results are recorded in `docs/piv/22-desktop-background-execution-non-blocking-ui.md`.
