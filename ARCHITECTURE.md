# ARCHITECTURE.md

The PRD remains the source of truth. The desktop implementation uses explicit
MVP and API boundaries:

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
separate: profile creation does not provision a user, profile deactivation does
not mutate login state, and `/instructors/me` resolves only the authenticated
user's stored `instructor_id`.

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
