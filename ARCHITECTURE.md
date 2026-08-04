# ARCHITECTURE.md

The PRD remains the source of truth. The desktop implementation uses explicit
MVP and API boundaries:

## Current implementation baseline

The authoritative product scope is `docs/PRD.md`; current submission sequencing
is in `docs/PROJECT-ROADMAP.md`. Tasks 01–25.x are historical development
increments, not an instruction to add more features. The current source tree
already contains the performance/background-execution foundation, branded
Desktop system, grounded RAG consultation and AI runtime readiness. Remaining
work is release/submission verification.

```text
desktop_client/app/
  api/          HTTP transport, bearer token, API errors
  features/     Microfrontend registration façades and role ownership
  models/       desktop session/value models
  services/     backend endpoint adapters
  presenters/   UI-independent orchestration and formatting
  views/        passive PySide6 widgets
  main.py       thin composition root and role-aware shell
```

Views emit user intent and render supplied state. Presenters do not import
PySide6. Services do not render UI. All operational data flows through FastAPI;
the desktop client never connects directly to PostgreSQL/Supabase.

Desktop Microfrontends are explicit feature registrations under
`desktop_client/app/features/`. `MainWindow` mounts the role-appropriate
features through `features.registry` and no longer imports/wires business
feature Views and Presenters directly. Each feature registration owns its View,
Presenter, signal wiring and page key while reusing the existing tested MVP
classes. See `docs/architecture/desktop-microfrontends.md` for the boundary
diagram and feature map.

Task 11 booking mutations preserve these boundaries: passive dialogs collect
manager input, the booking presenter orchestrates command state and projection
refreshes, and the booking service calls the existing event-sourced endpoints.
Granular updates carry the latest returned optimistic-concurrency version into
the next command. Backend domain validation and authorization remain
authoritative.

Task 12 shared desktop infrastructure classifies transport errors without
placing navigation decisions in services. `ApiClient` clears an expired bearer
token and notifies the composition root; `MainWindow` owns the return-to-login
transition. Reusable management widgets remain passive signal/state components,
while each entity retains a dedicated service, presenter, view, and dialog
workflow.

Task 12B follows the same explicit path for customer workflows:
`CustomerService -> CustomersPresenter/CustomerProfilePresenter -> passive
CustomersView/CustomerProfileView`. Contacts remain nested in customer details;
neither views nor presenters access PostgreSQL, and server authorization remains
the ownership boundary for customer profiles.

Task 12C adds the parallel entity-specific path `ActivityService ->
ActivitiesPresenter -> passive ActivitiesView/ActivityDialog`. One role-aware
screen is composed for all roles; the presenter prevents non-manager mutations
and forces their active-only intent, while FastAPI remains the authorization
boundary. Image Gateway endpoints are intentionally not connected to this
textual catalog milestone.

Task 12D adds conventional instructor CRUD through `router -> application
service -> repository -> PostgreSQL` and `InstructorService -> presenter ->
passive view` on desktop. Instructor profiles and authentication users remain
separate: profile creation does not provision a user, profile deletion is
blocked while a login, assignment, or immutable booking event references it,
and `/instructors/me` resolves only the authenticated user's stored
`instructor_id`. Customer deletion follows the same transaction boundary:
bookings, event history, and linked users block with HTTP 409; disposable owned
contacts use the schema's `ON DELETE CASCADE`.

Task 12E keeps assignment writes on `command handler -> aggregate -> immutable
event -> projections`. Focused assignment queries serve the embedded Booking
Details presenter. Safe open-event detail is separate from ordinary instructor
booking access, and no standalone assignment module appears in navigation.

Task 12F keeps display names in the booking projection query instead of issuing
per-row detail requests. Paging/filter state belongs to `BookingsPresenter` and
passive widgets emit intent. `MainWindow` composes dashboard navigation and
targeted booking/assignment refresh callbacks, avoiding presenter cycles and a
global refresh-everything mechanism.

Task 12G enforces the same boundaries at closure: system diagnostic SQL lives
in `backend/app/db/system_queries.py`, raw event history is manager-only, and
terminal booking immutability is enforced by the aggregate rather than by UI
button state. Architecture tests scan routers, presenters, and views for these
boundary violations.

Task 19 extends the existing activity path without adding a media module:
`ApiClient -> ActivityService -> ActivitiesPresenter -> passive
ActivitiesView`. Authenticated upload/delete continue through FastAPI and the
existing image Gateway. Public Cloudinary preview bytes are downloaded over
HTTPS without the FastAPI bearer token, remain in a bounded three-entry
memory-only LRU cache, and are never written to disk. The presenter owns request
identity and rejects obsolete results but imports no PySide6; `ActivitiesView`
exclusively owns `QPixmap` decoding, scaling, and rendering. Activity images
remain conventional metadata and are not event-sourced.

Task 20 adds neutral shared View foundations without changing these MVP
boundaries. A Qt-independent semantic `RequestState`/`RequestIdentity` contract
lets presenters describe idle,
loading, success, empty, validation, authorization, connection/server, stale,
and session-expiry behavior without importing PySide6. Passive shared widgets
render that state and emit intent; they do not classify errors, access
services, or decide authorization. The bounded pilot is Login, Shell,
Customers, Customer/Contact dialogs, and shared state components. Task 20 introduced the neutral structural foundation. The later Task 25.x
work now applies the branded visual system across the current Desktop modules.
Task 22 owns the reusable long-running-operation pattern.

The View foundation standardizes an ordered `PageScaffold` composition
(`PageHeader`, optional feedback/actions/filters, stretching main content with an
optional details pane, and optional footer), centralized neutral tokens, dialog
behavior, and feedback selection. These are View-layer contracts only.
Compatibility was checked against the existing Dashboard without placing it in
the Task 20 pilot. They do not redefine MVP, add dependencies, alter desktop or
backend responsibilities, or change any backend/API boundary.

The application-level neutral background/type roles are shared, while control
geometry, focus borders, and table density selectors are bounded to the Task 20
pilot, Shell, Task 20 dialogs/state controls, and tables explicitly configured by
the shared helper. This preserves excluded module behavior while allowing later
tasks to opt into the foundation deliberately. Request identities currently
protect synchronous/reentrant Customer selection and session invalidation; they
do not claim the Task 22 background-execution guarantee.

### Task 24 role-aware Booking creation

Booking creation follows `Passive View -> Qt-free BookingsPresenter ->
BookingService -> ApiClient -> FastAPI -> CreateBookingCommand ->
BookingAggregate -> immutable BookingCreated -> transactional projection`.
Managers supply an active Customer. For Customers, FastAPI derives the linked
Customer identity and controls initial administrative fields. Instructors are
denied before command dispatch. Activities and Bookings reuse the same
Presenter/form workflow.

Instructor assignment is a separate Manager-only command after creation.
Booking Details dispatches `AssignInstructorCommand` for one Booking Activity;
immutable `BookingInstructorAssigned` updates the active-assignment projection
that scopes Instructor reads. Booking status and assignment remain independent.

Task 24.3 keeps those backend boundaries unchanged while simplifying Manager
orchestration. An optional Instructor selection is removed from the create
payload; after `BookingCreated`, the Desktop delegates to the existing
assignment Presenter and API. A `NEW` unassigned Booking uses one Details action
to assign and then confirm with the returned aggregate version. A `NEW` Booking
that is already assigned uses the same action to confirm without adding a
duplicate assignment. Customer requests remain `NEW` and unassigned.

### Task 24.1 single current Customer contact

`customer_contacts` remains compatibility/history storage, but the product
boundary exposes exactly one current active contact person. Customer reads
select the active primary contact (or first active fallback); active create or
reactivation conflicts when another current contact exists. Desktop Views render
only contact name and phone in Customer details and expose no contact collection
or independent contact lifecycle controls. Customer and contact-person
create/update are committed by the backend in one transaction.

### Task 22 desktop execution boundary

Task 22 adds a bounded scheduling boundary without changing MVP ownership.
Presenters depend on a plain `OperationExecutor` port and retain request/session
identity, duplicate-action, and stale-result decisions. Production composition
provides a PySide6 `QThreadPool` adapter with four workers and a maximum of 32
active or queued operations. The adapter executes existing synchronous Services
and `ApiClient` calls away from the Qt event loop, then dispatches plain
success/error completion to the UI thread.

Views remain passive and never call the executor, Services, HTTP, repositories,
or databases. Presenters never import Qt. Workers never access widgets. Page
changes invalidate the previous pilot Presenter; logout, session expiry, and
shutdown invalidate all outstanding callback identities. Cancellation means
cooperative suppression of obsolete results and does not claim to reverse a
mutation already committed by FastAPI.

Native lifetime ownership is explicit. A `QRunnable` uses `autoDelete=False`
and remains owned by its UI-thread operation record until the executor receives
its single queued completion or completes shutdown. Cancelling a running task
marks it obsolete but does not release its runnable/callback ownership early.
Shutdown is UI-thread-only and idempotent: reject new work, invalidate callback
identities, remove work that is still queued, wait without timeout for the
private pool to finish, synchronously drain its queued MetaCalls, and only then
release records and allow QObject teardown. This prevents a private pool,
runnable, Python wrapper, or queued completion from surviving its window.

The bounded Task 22 pilot covers Login, Dashboard, Customers and owned Customer
profile, Instructors and owned Instructor profile, and manager User
Administration. Task 23 extends the same boundary as documented below. Backend
contracts, CQRS/Event Sourcing, Gateway, authorization, and AI/RAG
responsibilities are unchanged.

### Task 23 session performance boundary

Task 23 adds one process-memory `SessionPerformanceCache` owned by the desktop
ApiClient. It is infrastructure, not domain state. Cache scope is a generation,
authenticated user ID, and role; login identity change, logout, 401 expiry, and
shutdown clear the entire scope. Canonical keys also contain resource, path, and
every response-shaping parameter. Stored/returned values are defensive copies.

Policies are per resource rather than global. They define TTL, explicit SWR
permission, 1 MiB payload limit, and invalidation relationships. Global bounds
are 128 entries, an 8 MiB serialized-size estimate, 32 in-flight identities,
and two refresh workers. Authentication, password/reset data, AI consultation,
mutations, errors, tokens/secrets, and public preview bytes are never cached;
there is no disk persistence.

SWR refresh threads are non-daemon and globally bounded. Cache shutdown is
idempotent, clears session/subscribers and Qt-facing failure handlers, and joins
every refresh thread before Qt teardown. Main-window close first detaches the
ApiClient unauthorized callback and cache freshness signal, joins cache work,
then shuts down the Qt executor. An obsolete request's 401 may clear a token
only when that request used the still-current token, so an old session cannot
expire a newer login.

The cache coalesces only complete identical GET identities. Mutation success
causes targeted resource invalidation; failure does not alter authoritative
cached state. SWR may retain safe operational data with a freshness warning,
but a 401 clears scope and overrides presentation. The cache never grants
authorization and cannot broaden a backend response.

Task 23 also adds owner/key removal to the bounded Qt execution adapter.
Superseded queued reads are removed where Qt permits; an already-running
`urllib` transport is not claimed as cancelled. Its callback record and
Presenter identity are invalidated so its result/error cannot render. Mutation
keys remain non-cancellable after dispatch and retain duplicate guards until
authoritative completion. Views remain passive, Presenters Qt-free, and workers
widget-free.

## Final presentation and AI runtime boundaries

The final Desktop visual system remains a View-layer concern. Shared tokens,
QSS roles, `ManagementWorkspace`, management heroes and reference list/detail
helpers style the application without moving business rules out of Presenters or
the backend. Login, Dashboard, Customers, Instructors, Managers, Activities,
Bookings, Knowledge Management and AI consultation are all composed within the
same role-aware executable while retaining feature-specific Presenter/Service
boundaries.

AI runtime startup opens the bounded PostgreSQL connection pool and performs a
non-fatal Ollama generation-model warm-up. Manager-only `/api/ai/readiness`
reports database-pool availability, Ollama reachability, generation/embedding
model availability and warm generation state. Current defaults are `llama3.1`,
`nomic-embed-text-v2-moe`, a 600-second generation timeout, `num_predict=2000`,
`keep_alive=30m`, and a database pool bounded to five connections.

Final regression evidence is documented in `docs/piv/final-validation.md`.
