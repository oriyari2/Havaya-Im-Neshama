# Task 12 PIV - Complete Desktop Functional Management Coverage

## Planned

Task 12 is one umbrella task executed as seven approved milestones. It expands
the functional desktop surface, adds only necessary backend prerequisites, and
preserves the existing MVP, CQRS, Event Sourcing, authorization, and Gateway
boundaries.

## Milestone 12A Implemented

- Added PUT and DELETE support to the shared HTTP client.
- DELETE accepts an optional JSON body for the existing assignment-removal API.
- Added explicit error categories and retry metadata.
- Authenticated HTTP 401 clears the token and invokes the shell's session-expiry
  path; invalid credentials without a token remain a normal login error.
- Added passive shared widgets for search/sort intent, offset pagination,
  active state, retry state, and confirmation.
- Added focused transport and offscreen widget tests.

## Architectural Decisions

- Transport policy remains in `ApiClient`; entity services will consume it.
- The unauthorized callback is transport-to-composition-root notification, not
  a UI decision inside a service.
- Shared widgets expose signals and render state only. Entity presenters will
  own query, pagination, retry, and mutation decisions.
- No generic CRUD presenter or form engine was introduced.

## Security and Authorization

- Bearer behavior is preserved.
- A 401 expires only an existing authenticated session.
- A 403 does not clear session or navigate away.
- System and diagnostic endpoints remain absent from desktop navigation.

## Validation Evidence

Focused tests cover PUT, DELETE, DELETE body, Unicode/repeated query parameters,
error classification, connection retry metadata, authenticated 401 handling,
login 401 behavior, search/sort signals, pagination offsets, active state, and
retry signals.

- focused 12A/view tests: 16 passed
- complete desktop suite: 30 passed
- desktop compileall: passed
- architecture boundary scans: passed
- `git diff --check`: passed with existing line-ending warnings only

Real-backend verification is read-only and is documented in
`docs/manual-testing-task-12.md`.

The real desktop `ApiClient` authenticated the seeded manager, read all six
dashboard fields, executed a Unicode customer search with limit/offset, then
received an authentication-classified 401 for an invalid bearer token. The
token cleared and the expiry callback ran exactly once. No database mutation
endpoint was called.

## Milestone 12B Implemented

- Added `CustomerService`, UI-independent customer formatting, and manager and
  customer-profile presenters.
- Added a functional manager Customers screen with search, backend-supported
  filters/order, offset pagination, selection/detail, create/edit, and explicit
  protected physical Delete actions.
- Retained contacts as a compact nested Customer Details section because the
  existing PRD, seed model, and booking `primary_contact_id` make them part of
  the current booking workflow. No Contacts navigation item was added.
- Added passive customer/contact dialogs with required-field/basic email
  checks, submit guards, backend error display, and preserved form contents.
- Added read-only My Profile only for a customer session containing a reliable
  `customer_id`; the backend continues to enforce ownership.

Focused 12B tests: 9 passed. Complete desktop suite: 39 passed. Desktop
compileall and `git diff --check` passed. Real-backend CRUD verification created
customer `f63005a4-c580-4010-a16f-32454e0819b0` and contact
`177961e7-7cf1-4708-a6e0-2ab77edd0e2b`, exercised update/deactivate/reactivate,
verified customer-owned profile access, then soft-deactivated both records.

## Milestone 12C Implemented

- Added `ActivityService`, formatter, role-aware presenter, passive view, and
  passive create/edit dialog.
- Managers can list active and inactive activities, search/filter/page, inspect
  full textual details, create/edit, and soft deactivate/reactivate.
- Instructors and customers use the same screen in read-only mode. Their
  presenter query is explicitly active-only and backend authorization remains
  authoritative even if a direct request asks for inactive records.
- Corrected a confirmed repository defect: `is_active=None` previously added
  `is_active=true`, preventing a manager “All” query from including inactive
  activities. `None` now means no state predicate; the application service
  continues forcing `True` for non-managers.
- Search/audience/season/tag use trimmed case-insensitive substring matching.
  Tags remain the existing textual schema field, not a new structured model.
- Image metadata is not rendered and media mutations remain deferred. This
  avoids introducing remote-image transport and failure handling into the
  complete textual catalog milestone.

Validation: 15 focused tests, 51 complete desktop tests, and 52 complete backend
tests passed. Compileall and diff checks passed. Real-backend verification used
activity `be2959ab-a12f-43b2-a2eb-6aaecf88616a`, confirmed filters, pagination,
detail, create/edit/protected deletion, manager all-state visibility,
active-only instructor/customer reads, and direct mutation 403 responses. The
record was left soft-deactivated.

## Milestone 12D Implemented

The existing schema separates instructor profiles and authentication users.
`users.instructor_id` is nullable, has no one-to-one constraint, and the live
database had six profiles with only one linked user. Profile and login email
are separate fields. Create/update therefore manage business profiles only and
never accept passwords, roles, or user fields.

Physical deletion is blocked by linked login state and all
assignment/history rows remain unchanged. Existing booking validation prevents
new assignments to inactive instructors. `/instructors/me` uses only the
authenticated user's stored instructor ID.

Added focused backend schema/repository/service/router layers and the desktop
`InstructorService -> InstructorsPresenter/InstructorProfilePresenter ->
passive view/dialog` flow. Duplicate profile email returns 409 and transaction
failures roll back.

Validation: 57 desktop and 57 backend tests passed. Real verification created
profile `41832a9d-2b63-49e4-8e00-fa96d093c55b`, exercised CRUD, filters, sort,
pagination, duplicate conflict, role denials, `/me`, and reactivation, then
left it inactive. No user, assignment, schema, or seed mutation occurred.

## Milestone 12E Implemented

`booking_activities.id` is the stable target. Active state is a set of
activity/instructor pairs; removed projection rows and immutable events remain.
Each assign/remove event advances the booking version. Multiple instructors per
activity are supported; only the identical active pair is a duplicate. No
schedule-conflict rule exists.

Added manager assignment reads, safe manager/instructor open-event detail, an
embedded `BookingAssignmentsPresenter`, passive assignment widgets, and a
paged selector using `InstructorService`. Customers are denied. HTTP 409 reloads
state without retrying the mutation.

Inspection found API-created bookings had no `booking_activities` row. New
`BookingCreated` events now optionally carry a generated activity ID and create
the default projection row; legacy events remain replay-compatible.

Real verification used booking `19a16e61-2ecd-4bab-a54a-20ffbcbdb7f0` and
activity `10627401-2ce6-466a-a34a-c6a4c0377eb2`: assign/remove events were
appended, duplicate and stale commands were rejected, no active assignment
remains, and the temporary booking was cancelled with four events preserved.

## Deviations

No functional deviation. A pre-existing booking-dialog test was aligned with
the dialog's current explicit customer/activity placeholder selections.

## Milestone 12F Implemented

Booking lists now send real `limit`/`offset`, preserve manager filters through
paging, reset offset for new filters, infer Next only from a full page, retain a
visible selection, and clear a stale selection. Server filters are `status`,
`customer_id`, `activity_id`, `instructor_id`, `from_date`, and `to_date`;
customer/instructor identity filters remain manager-only. Bounded active
customer/activity/instructor results from existing services populate named
selectors while stable IDs remain internal.

Projection SQL joins customer and activity names, avoiding N+1 detail calls and
still labeling inactive historical relations. The instructor/open-event schemas
carry activity name only; customer identity, price, and notes remain protected.
Complete reuses the event-sourced status command with expected version. The
domain permits NEW or CONFIRMED to become COMPLETED and makes COMPLETED and
CANCELLED terminal.

Dashboards compose existing role-scoped summary, list, my-bookings, and open-
event endpoints. Status cards drill into filtered bookings, unassigned opens
Open Events, and shortcuts target functional screens. Independent endpoint
errors remain visible without hiding successful data. Open Events filtering is
explicitly client-side over its unpaged response.

Refresh stays coordinated in the composition root: booking changes refresh
list/detail/history and dashboard; assignment callbacks additionally refresh
Open Events. No presenter cycles or global refresh-everything mechanism was
introduced. Synchronous HTTP and the 100-row bounded selector lookup remain
documented limitations.

Validation observed 67 desktop and 63 backend tests passing. Real-backend
verification created booking `55904e20-a46a-4b80-9828-468d79380256`, completed
it from version 1 to 2, and confirmed readable names, two immutable events, all
six dashboard fields for all roles, combined manager filters, instructor scoped
reads, and customer 403 for Open Events. No init, seed, replay, schema, delete,
or direct SQL operation ran.

## Milestone 12G Final Acceptance

The audit generated 47 OpenAPI operations. M/I/C mean manager/instructor/
customer; own/scoped reads are enforced by the backend. Evidence names refer to
modules under `backend/app` or `desktop_client/app`.

| Method | Path | Purpose | Roles | Location | Classification | Evidence | Decision |
|---|---|---|---|---|---|---|---|
| GET | `/health` | Process health | Public | Operations | Intentionally internal | `main.py` | No desktop control |
| GET | `/system/db-status` | DB reachability | Public | Operations | Intentionally internal | `routers/system.py`, `db/system_queries.py` | No desktop control |
| POST | `/system/init-db` | Dev bootstrap | Environment/flag gated | Operations | Intentionally internal | `routers/system.py` | Never expose |
| GET | `/system/schema-summary` | Schema diagnostic | Public | Operations | Intentionally internal | `db/system_queries.py` | No desktop control |
| POST | `/auth/login` | Authenticate/session | Public | Login | Exposed in desktop | `AuthService` | Complete |
| GET | `/auth/me` | Token identity | M/I/C | Diagnostics | Intentionally internal | `routers/auth.py`; login payload supplies identity | Avoid duplicate call |
| GET | `/customers` | Customer directory | M | Customers/selectors | Exposed in desktop | `CustomerService.list_customers` | Complete |
| POST | `/customers` | Create customer | M | Customers dialog | Exposed in desktop | `CustomerService.create_customer` | Complete |
| GET | `/customers/{customer_id}` | Customer detail | M; C own | Customers/My Profile | Exposed in desktop | `CustomerService.customer` | Complete |
| PUT | `/customers/{customer_id}` | Update | M | Customers | Exposed in desktop | `CustomerService.update_customer` | Desktop does not mutate active state |
| DELETE | `/customers/{customer_id}` | Protected physical delete | M | Customers | Exposed in desktop | `delete_customer` | 204 or dependency 409 |
| GET | `/customers/{customer_id}/contacts` | Nested contacts | M; C own | Customer details/profile | Exposed in desktop | `CustomerService.contacts` | Complete |
| POST | `/customers/{customer_id}/contacts` | Create contact | M | Customer details | Exposed in desktop | `create_contact` | Complete |
| PUT | `/customer-contacts/{contact_id}` | Update/reactivate contact | M | Customer details | Exposed in desktop | `update_contact` | Complete |
| DELETE | `/customer-contacts/{contact_id}` | Soft deactivate contact | M | Customer details | Exposed in desktop | `deactivate_contact` | Deactivate wording |
| GET | `/instructors` | Directory/selectors | M | Instructors/booking assignment selectors | Exposed in desktop | `InstructorService.list_instructors` | Complete |
| POST | `/instructors` | Create profile | M | Instructors dialog | Exposed in desktop | `create_instructor` | No account provisioning |
| GET | `/instructors/me` | Own profile | I own | My Profile | Exposed in desktop | `InstructorProfilePresenter` | Complete |
| GET | `/instructors/{instructor_id}` | Profile detail | M | Instructors | Exposed in desktop | `InstructorService.instructor` | Complete |
| PUT | `/instructors/{instructor_id}` | Update | M | Instructors | Exposed in desktop | `update_instructor` | Desktop does not mutate active state |
| DELETE | `/instructors/{instructor_id}` | Protected physical delete | M | Instructors | Exposed in desktop | `delete_instructor` | 204 or dependency 409 |
| GET | `/activities` | Catalog/list/selectors | M/I/C; I/C active | Activities/booking selectors | Exposed in desktop | `ActivityService.list_activities` | Complete |
| POST | `/activities` | Create activity | M | Activities dialog | Exposed in desktop | `create_activity` | Complete |
| GET | `/activities/{activity_id}` | Activity detail | M/I/C; I/C active | Activities | Exposed in desktop | `ActivityService.activity` | Complete |
| PUT | `/activities/{activity_id}` | Update/reactivate | M | Activities | Exposed in desktop | `update_activity` | Complete |
| DELETE | `/activities/{activity_id}` | Soft deactivate | M | Activities | Exposed in desktop | `deactivate_activity` | Deactivate wording |
| GET | `/activities/{activity_id}/images` | Image metadata | M/I/C; I/C active | Future media | Deferred with documented reason | `routers/activity_images.py`; no UI | Media task |
| POST | `/activities/{activity_id}/images` | Gateway upload | M | Future media | Deferred with documented reason | image Gateway | Media task |
| DELETE | `/activities/{activity_id}/images/{image_id}` | Gateway deletion | M | Future media | Deferred with documented reason | image Gateway | Media task |
| POST | `/bookings` | Create booking | M | Bookings/dashboard | Exposed in desktop | `BookingService.create_booking` | Complete |
| GET | `/bookings` | Scoped/filter list | M; I assigned; C own | Bookings/My Events/dashboard | Exposed in desktop | `BookingsPresenter` | Complete |
| GET | `/bookings/dashboard` | Six scoped counts | M/I/C | Dashboard | Exposed in desktop | `DashboardPresenter` | Complete |
| GET | `/bookings/open-events` | Eligible open events | M/I | Open Events/dashboard | Exposed in desktop | `OpenEventsPresenter` | Complete |
| GET | `/bookings/open-events/{booking_id}` | Safe open detail | M/I | Open Events detail | Exposed in desktop | `AssignmentService.open_event_detail` | Complete/safe |
| GET | `/bookings/my-bookings` | Compact owned page | C own | My Bookings/dashboard | Exposed in desktop | `BookingService.my_bookings` | Complete |
| GET | `/bookings/{booking_id}` | Scoped detail | M; I assigned; C own | Booking details | Exposed in desktop | `BookingService.booking` | Complete/safe |
| GET | `/bookings/{booking_id}/assignments` | Active assignment read | M | Embedded booking details | Exposed in desktop | `AssignmentService.assignments` | Complete |
| GET | `/bookings/{booking_id}/history` | Raw immutable history | M | Manager booking details | Exposed in desktop | `BookingService.history`, manager guard | Complete |
| PATCH | `/bookings/{booking_id}/status` | Confirm/cancel/complete | M | Booking actions | Exposed in desktop | `change_status` | Event-sourced/versioned |
| PATCH | `/bookings/{booking_id}/schedule` | Schedule update | M | Edit dialog | Exposed in desktop | `change_schedule` | Event-sourced/versioned |
| PATCH | `/bookings/{booking_id}/price` | Price update | M | Edit dialog | Exposed in desktop | `change_price` | Event-sourced/versioned |
| PATCH | `/bookings/{booking_id}/location` | Location update | M | Edit dialog | Exposed in desktop | `change_location` | Event-sourced/versioned |
| PATCH | `/bookings/{booking_id}/participant-count` | Participant update | M | Edit dialog | Exposed in desktop | `change_participant_count` | Event-sourced/versioned |
| PATCH | `/bookings/{booking_id}/notes` | Notes update | M | Edit dialog | Exposed in desktop | `update_notes` | Event-sourced/versioned |
| POST | `/bookings/{booking_id}/instructors` | Assign instructor | M | Embedded details | Exposed in desktop | `AssignmentService.assign` | Event-sourced/versioned |
| DELETE | `/bookings/{booking_id}/activities/{booking_activity_id}/instructors/{instructor_id}` | Remove instructor | M | Embedded details | Exposed in desktop | `AssignmentService.remove` | Confirmed/event-sourced |
| POST | `/bookings/{booking_id}/replay` | Diagnostic reconstruction | M | Maintenance | Intentionally internal | no desktop service/control | Never expose |

### Closure defects fixed

1. System diagnostics contained SQL in the router. Queries now live in
   `backend/app/db/system_queries.py`; endpoint behavior is unchanged.
2. Raw history relied on ordinary booking visibility and could reveal event
   payload fields to instructors/customers. It is now manager-only in the
   application query handler, with direct-denial tests.
3. `COMPLETED` blocked status transitions but still accepted operational field
   commands. Both terminal statuses now reject operational updates in the
   aggregate, with regression coverage and a real API 400 verification.

### Final role matrix

| Workflow | Manager | Instructor | Customer |
|---|---|---|---|
| Dashboard | Six counts, operational lists, management drill-down | Scoped upcoming/assigned/open work | Own summary and bookings |
| Customers/contacts | Customer protected Delete; nested contact soft-deactivation CRUD | Denied | Own profile read only |
| Instructors | Full profile CRUD with protected Delete | Own profile read only | Denied |
| Activities | Full textual soft-deactivation CRUD | Active catalog | Active catalog |
| Bookings | Full filters/details/commands | Assigned events and safe detail | Own bookings/detail |
| Assignments | Embedded assign/remove | No controls/self-claim | Denied |
| History | Raw manager-only history | 403 | 403 |
| Open Events | List/safe detail | List/safe detail | Absent/403 |

### Legacy decision and data audit

Option A (document only) was selected. The only inspected booking lacking a
booking-activity row, `e4d1664c-2b6e-4f30-acdc-da4254dc8ba8`, is a past July 17
legacy manual booking. All deterministic demo bookings and current API-created
bookings have stable activity targets, so no required upcoming workflow is
blocked and a repair tool would add unnecessary mutation risk. Demo users still
authenticate; Task 12 customer/activity/instructor verification records are
inactive, and no active temporary assignment remains.

### Authoritative known limitations

- Synchronous HTTP can briefly block Qt.
- List counts are page counts, not totals; Next uses full-page inference.
- Related booking selectors are bounded to 100 active records and search locally.
- Open Events search is client-side over an unpaged response.
- Multi-command edits are sequential rather than atomic.
- There is no instructor schedule-conflict rule or numeric required-instructor count.
- Instructor email uniqueness is application-level; creating a profile does not
  provision a login; users and instructors have no database one-to-one constraint.
- Legacy events without `booking_activity_id` are not automatically repaired.
- Media mutations, Task 13 visual redesign, AI/RAG, password reset, and general
  user/account administration remain deferred.

Task 12 is complete with documented limitations.

### Final validation evidence

- `python -m unittest discover -s backend/tests -v`: 75 passed, none skipped.
- `python -m unittest discover -s desktop_client/tests -v`: 72 passed, none skipped.
- `python -m compileall backend desktop_client`: passed.
- OpenAPI: 47 unique operations; all classified above.
- Router SQL, presenter PySide, view data-layer, sensitive-schema, tracked-env,
  role-navigation, and authorization scans: passed.
- `git diff --check`: passed; only Git line-ending conversion warnings appeared.

### Post-closure deletion behavior correction

The customer and instructor desktop actions were changed from soft lifecycle
switches to explicit manager-only Delete actions. Backend DELETE now physically
removes only an unreferenced profile, in a single locked transaction. Customer
bookings, customer IDs in immutable booking events, and linked users block with
HTTP 409; customer-owned contacts alone cascade. Instructor active/removed
assignment rows, instructor IDs in immutable booking events, and linked users
block with HTTP 409. Constraint races are translated to the same non-technical
409 contract; unexpected failures use the existing structured 500 transport
handling. No login, booking, event, or assignment history is deleted or
unlinked. Activity soft deactivate/reactivate remains unchanged.

Real-backend evidence: an API-created customer/contact and instructor were
deleted with 204; subsequent details, list searches, and the cascaded contact
update proved absence (404/zero results). Seeded customer/instructor profiles
and instructors referenced by assigned and removed events returned 409;
non-manager DELETE returned 403; both linked logins still returned `/auth/me`;
the activity lifecycle check ended in its original inactive state. Verification
used supported APIs only.
