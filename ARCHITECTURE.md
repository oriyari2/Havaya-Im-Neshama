# ARCHITECTURE.md

The PRD remains the source of truth. The desktop implementation uses explicit
MVP and API boundaries:

## Planning sequence after Task 21

The authoritative execution order is defined by `docs/PROJECT-ROADMAP.md`:

1. completed architecture/backend/desktop/CQRS/Event Sourcing/User
   Administration foundation (Tasks 01–21);
2. background execution, API/screen performance, refresh reduction, bounded
   caching, reliability, security, and responsiveness (Tasks 22–24);
3. Desktop visual design, UI consistency, UX, accessibility, and responsive
   layout (Tasks 25–28);
4. remaining Ollama/RAG/semantic-search/AI experience work (Tasks 29–30);
5. stabilization, performance verification, regression, packaging, and final
   release audit (Tasks 31–33).

This ordering changes scheduling, not architectural ownership. Historical Task
and PIV references to old future-task numbers are superseded by the roadmap.

```text
desktop_client/app/
  api/          HTTP transport, bearer token, API errors
  models/       desktop session/value models
  services/     backend endpoint adapters
  presenters/   UI-independent orchestration and formatting
  views/        passive PySide6 widgets
  main.py       composition root and role-aware shell wiring
```

Views emit user intent and render supplied state. Presenters do not import
PySide6. Services do not render UI. All operational data flows through FastAPI;
the desktop client never connects directly to PostgreSQL/Supabase.

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
Customers, Customer/Contact dialogs, and shared state components. Temporary
neutral tokens are structural only; Task 25 owns the next visual-system design
and Tasks 26–28 apply it across the desktop. Task 20 does not implement
production-wide background threading; Task 22 owns the reusable
long-running-operation pattern.

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
