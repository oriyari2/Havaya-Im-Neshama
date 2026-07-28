# Task 12 - Complete Desktop Functional Management Coverage

## Background and Problem

Tasks 09-11 delivered role-scoped booking queries and core booking commands,
but the desktop does not yet expose customer, activity, instructor, or
assignment management. Task 12 closes that functional gap without performing
the Task 13 visual redesign or adding desktop media mutations.

## Goals

- complete meaningful manager, instructor, and customer desktop workflows
- preserve API client -> service -> presenter -> passive view/dialog boundaries
- add focused backend prerequisites for instructors and assignments
- preserve booking CQRS and Event Sourcing
- provide consistent transport, error, pagination, and retry behavior
- classify every OpenAPI operation at final acceptance

## Non-goals

- visual redesign, branding, animation, or final styling
- Cloudinary upload/delete desktop UI
- AI/RAG, password reset, or general account administration
- system, database, schema, replay, or event-store administration UI
- permanent activity deletion or any booking deletion

## Roles and Planned Navigation

- Manager: Dashboard, Customers, Instructors, Activities, Bookings, Open Events
- Instructor: Dashboard, Activities, My Events, Open Events, My Profile
- Customer: Dashboard, Activities, My Bookings, My Profile

Only working screens will be added to navigation.

## Bounded Milestones

1. Shared API/client infrastructure
2. Customer management
3. Activity management/catalog
4. Instructor backend and desktop management
5. Assignment read models and embedded desktop workflow
6. Booking/dashboard/navigation completion
7. Full regression, documentation, endpoint coverage, and acceptance

Each milestone requires implementation, focused tests, real-backend manual
verification, relevant documentation, and approval before the next starts.

## Milestone 12A - Shared Infrastructure

Implemented scope:

- JSON PUT and DELETE, including DELETE request bodies
- existing query encoding verified for Unicode, repeated, and empty parameters
- structured `ApiErrorKind` classification for 400/401/403/404/409/422/500
  and connection failures
- retry metadata for server/connection errors
- authenticated 401 clears the bearer token and returns the application to login
- login 401 does not trigger session-expiry navigation
- passive reusable search/sort toolbar, pagination footer, active badge,
  retry state, and confirmation helper

No business navigation or backend endpoint changed in 12A.

## Milestone 12B - Customer Management

Implemented scope:

- manager Customers navigation, list, detail, search, city/type/active filters,
  supported `name`/`created_at` ordering, and real limit/offset paging
- create, edit, and protected physical customer deletion workflows
- compact nested contact management in Customer Details (create, edit, soft
  deactivate, reactivate); contacts are retained because they are the booking
  contact source represented by `primary_contact_id`
- customer-only read-only My Profile, scoped by the authenticated session's
  `customer_id`; instructors receive neither customer screen
- passive dialogs preserve values after validation/API errors and presenters
  guard duplicate submissions

## Milestone 12C - Activity Management and Catalog

Implemented scope:

- one role-aware Activities screen: complete textual management for managers
  and an active-only read-only catalog for instructors/customers
- server-side search plus `target_audience`, `season`, `tag`, manager-only
  `is_active`, and real limit/offset pagination
- full textual detail and schema-exact create/edit fields
- explicit soft deactivate/reactivate actions and confirmation
- manager “All” now correctly omits the activity-state predicate; non-manager
  service authorization still forces active-only reads
- activity image display and POST/DELETE media mutations remain deferred to the
  media milestone; no placeholder controls are present

Activity endpoint coverage:

| Endpoint | Task 12 classification |
|---|---|
| `GET /activities` | Exposed in desktop |
| `GET /activities/{activity_id}` | Exposed in desktop |
| `POST /activities` | Exposed in desktop (manager) |
| `PUT /activities/{activity_id}` | Exposed in desktop (manager) |
| `DELETE /activities/{activity_id}` | Exposed as soft Deactivate (manager) |
| `POST /activities/{activity_id}/images` | Deferred to media milestone |
| `DELETE /activities/{activity_id}/images/{image_id}` | Deferred to media milestone |

## Milestone 12D - Instructor Management and Profile

- Manager directory: search, city/active filters, `full_name`/`created_at`
  ordering, offset pagination, detail, create/edit, and protected deletion.
- Instructor-only read-only My Profile through `/instructors/me`.
- Create manages a business profile only; it does not provision users.
- Deletion is blocked when a login, active or removed assignment, or immutable
  booking event references the instructor; no login or history is removed.
- Customers and instructors are denied directory, other-detail, and mutations.

| Endpoint | Task 12 classification |
|---|---|
| `GET /instructors` | Exposed in manager desktop |
| `POST /instructors` | Exposed in manager desktop |
| `GET /instructors/me` | Exposed in instructor desktop |
| `GET /instructors/{instructor_id}` | Exposed in manager desktop |
| `PUT /instructors/{instructor_id}` | Exposed in manager desktop |
| `DELETE /instructors/{instructor_id}` | Protected physical Delete (manager) |

## Milestone 12E - Embedded Instructor Assignments

- Manager-only assignment read model exposes stable booking activity IDs,
  booking version, named activities, requirement state, and active assignments.
- Assignment/removal remains event-sourced and uses expected-version commands.
- Management is embedded in Booking Details with a paginated active-instructor
  selector; no Assignments navigation exists.
- A separate safe open-event detail contract serves managers/instructors without
  customer, price, notes, participant count, history, or mutation powers.
- New `BookingCreated` events carry a backward-compatible stable default
  booking-activity ID so API-created bookings can enter the assignment workflow.

| Endpoint | Classification |
|---|---|
| `GET /bookings/{booking_id}/assignments` | Manager Booking Details |
| `GET /bookings/open-events/{booking_id}` | Manager/instructor Open Events |
| `POST /bookings/{booking_id}/instructors` | Manager Booking Details |
| assignment DELETE endpoint | Manager Booking Details |

## Error Contract

- 400/422: validation
- 401: authentication; expire an existing session
- 403: permission; preserve current screen state
- 404: stale/not-found; entity presenters refresh when appropriate
- 409: optimistic-concurrency conflict; booking/entity presenters refresh
- 500: retriable server error
- transport failure: retriable connection error

Entity-specific refresh and form-preservation behavior is implemented in the
milestone that owns that entity.

## Acceptance Progress

- [x] Shared PUT/DELETE transport and structured errors
- [x] Authenticated 401 session clearing and login return
- [x] Shared functional list-state components
- [x] Customer management
- [x] Activity management/catalog
- [x] Instructor management and profile
- [x] Assignment workflow
- [x] Booking/dashboard/navigation completion
- [x] Full endpoint coverage and final acceptance

## Milestone 12F - Booking, Dashboard, and Navigation Completion

- Real limit/offset paging for every role; full-page Next inference, persistent
  filters, visible-selection retention, and safe stale-selection clearing.
- Manager status/customer/activity/instructor/date filters use bounded named
  selectors through existing entity services rather than raw UUID entry.
- Booking projection queries return joined activity/customer display names;
  instructor contracts still expose activity identity only.
- Manager Complete reuses the event-sourced status command and expected version
  from NEW or CONFIRMED; terminal states stay immutable.
- Role dashboards use existing scoped summary/list/open-event endpoints and
  provide real shortcuts and drill-down. Open Events search is local to the
  endpoint's complete returned list because no server filters exist.
- Existing role routes are synchronized in the sidebar; no internal,
  assignment, media, user, system, or replay navigation was added.

## Risks and Deferred Items

- HTTP calls remain synchronous and may briefly block the Qt event loop.
- Raw booking history remains manager-only until role-safe history exists.
- Media mutation UI and visual redesign remain deferred.

## Milestone 12G - Final Acceptance and Closure

Role abbreviations below are M = manager, I = instructor, and C = customer.
“Own/scoped” means the backend applies the authenticated customer or instructor
relationship. This inventory was generated from the final OpenAPI document and
contains all 47 operations.

| Method | Path | Purpose | Allowed roles | Desktop/internal location | Classification | Evidence | Final decision |
|---|---|---|---|---|---|---|---|
| GET | `/health` | Process health | Public | Operations only | Intentionally internal | `backend/app/main.py` | Keep out of navigation |
| GET | `/system/db-status` | Database reachability | Public | Operations only | Intentionally internal | `routers/system.py`, `db/system_queries.py` | Keep out of navigation |
| POST | `/system/init-db` | Development bootstrap | Environment/flag gated | Operations only | Intentionally internal | `routers/system.py` | Never expose in desktop |
| GET | `/system/schema-summary` | Expected-table diagnostics | Public | Operations only | Intentionally internal | `routers/system.py`, `db/system_queries.py` | Keep out of navigation |
| POST | `/auth/login` | Authenticate and return session | Public | Login | Exposed in desktop | `AuthService`, `LoginPresenter` | Complete |
| GET | `/auth/me` | Authenticated token identity | M/I/C | Session diagnostics; login response already carries identity | Intentionally internal | `routers/auth.py`, `AuthService` | No duplicate desktop call |
| GET | `/customers` | Customer directory | M | Customers; booking selectors | Exposed in desktop | `CustomerService`, `CustomersPresenter` | Complete |
| POST | `/customers` | Create customer | M | Customers dialog | Exposed in desktop | `CustomerService.create_customer` | Complete |
| GET | `/customers/{customer_id}` | Customer detail | M; C own | Customers / My Profile | Exposed in desktop | `CustomerService.customer` | Complete |
| PUT | `/customers/{customer_id}` | Update customer | M | Customers dialog | Exposed in desktop | `CustomerService.update_customer` | Desktop does not mutate active state |
| DELETE | `/customers/{customer_id}` | Protected physical delete | M | Customers action | Exposed in desktop | `CustomerService.delete_customer` | 204 or dependency 409 |
| GET | `/customers/{customer_id}/contacts` | Nested contacts | M; C own | Customer Details / My Profile | Exposed in desktop | `CustomerService.contacts` | Complete |
| POST | `/customers/{customer_id}/contacts` | Create nested contact | M | Customer Details dialog | Exposed in desktop | `CustomerService.create_contact` | Complete |
| PUT | `/customer-contacts/{contact_id}` | Update/reactivate contact | M | Customer Details | Exposed in desktop | `CustomerService.update_contact` | Complete |
| DELETE | `/customer-contacts/{contact_id}` | Soft-deactivate contact | M | Customer Details | Exposed in desktop | `CustomerService.deactivate_contact` | Labeled Deactivate |
| GET | `/instructors` | Instructor directory/selector | M | Instructors; assignment/booking selectors | Exposed in desktop | `InstructorService.list_instructors` | Complete |
| POST | `/instructors` | Create business profile | M | Instructors dialog | Exposed in desktop | `InstructorService.create_instructor` | No login account created |
| GET | `/instructors/me` | Own instructor profile | I own | My Profile | Exposed in desktop | `InstructorProfilePresenter` | Complete |
| GET | `/instructors/{instructor_id}` | Instructor detail | M | Instructors | Exposed in desktop | `InstructorService.instructor` | Complete |
| PUT | `/instructors/{instructor_id}` | Update profile | M | Instructors dialog | Exposed in desktop | `InstructorService.update_instructor` | Desktop does not mutate active state |
| DELETE | `/instructors/{instructor_id}` | Protected physical delete | M | Instructors action | Exposed in desktop | `InstructorService.delete_instructor` | 204 or dependency 409 |
| GET | `/activities` | Activity list/catalog/selectors | M/I/C; I/C active only | Activities; booking selectors | Exposed in desktop | `ActivityService.list_activities` | Complete |
| POST | `/activities` | Create activity | M | Activities dialog | Exposed in desktop | `ActivityService.create_activity` | Complete |
| GET | `/activities/{activity_id}` | Activity detail | M/I/C; I/C active only | Activities | Exposed in desktop | `ActivityService.activity` | Complete |
| PUT | `/activities/{activity_id}` | Update/reactivate activity | M | Activities dialog/action | Exposed in desktop | `ActivityService.update_activity` | Complete |
| DELETE | `/activities/{activity_id}` | Soft-deactivate activity | M | Activities action | Exposed in desktop | `ActivityService.deactivate_activity` | Labeled Deactivate |
| GET | `/activities/{activity_id}/images` | Image metadata list | M/I/C; I/C active only | Future media workflow | Deferred with documented reason | `activity_images.py`; no desktop media controls | Media task |
| POST | `/activities/{activity_id}/images` | Upload through Gateway | M | Future media workflow | Deferred with documented reason | `activity_images.py`, image Gateway | Media task |
| DELETE | `/activities/{activity_id}/images/{image_id}` | Delete image through Gateway | M | Future media workflow | Deferred with documented reason | `activity_images.py`, image Gateway | Media task |
| POST | `/bookings` | Create event-sourced booking | M | Bookings / Dashboard quick action | Exposed in desktop | `BookingService.create_booking` | Complete |
| GET | `/bookings` | Filtered/scoped booking list | M; I assigned; C own | Bookings / My Events; dashboard | Exposed in desktop | `BookingsPresenter`, `DashboardPresenter` | Complete |
| GET | `/bookings/dashboard` | Six scoped summary counts | M/I/C | Dashboard | Exposed in desktop | `BookingService.dashboard` | Complete |
| GET | `/bookings/open-events` | Eligible unassigned events | M/I | Open Events / dashboard | Exposed in desktop | `OpenEventsPresenter` | Complete |
| GET | `/bookings/open-events/{booking_id}` | Safe open-event detail | M/I | Open Events detail | Exposed in desktop | `AssignmentService.open_event_detail` | Complete and role-safe |
| GET | `/bookings/my-bookings` | Compact owned booking page | C own | My Bookings / dashboard | Exposed in desktop | `BookingService.my_bookings` | Complete |
| GET | `/bookings/{booking_id}` | Scoped booking detail | M; I assigned; C own | Booking Details | Exposed in desktop | `BookingService.booking` | Complete and role-safe |
| GET | `/bookings/{booking_id}/assignments` | Active assignment read model | M | Embedded Booking Details | Exposed in desktop | `AssignmentService.assignments` | Complete; no top-level screen |
| GET | `/bookings/{booking_id}/history` | Raw immutable history | M | Manager Booking Details | Exposed in desktop | `BookingService.history`; manager guard | Complete; manager-only |
| PATCH | `/bookings/{booking_id}/status` | Confirm/cancel/complete | M | Booking command actions | Exposed in desktop | `BookingService.change_status` | Complete, expected version |
| PATCH | `/bookings/{booking_id}/schedule` | Change schedule | M | Booking edit dialog | Exposed in desktop | `BookingService.change_schedule` | Complete, event-sourced |
| PATCH | `/bookings/{booking_id}/price` | Change agreed price | M | Booking edit dialog | Exposed in desktop | `BookingService.change_price` | Complete, event-sourced |
| PATCH | `/bookings/{booking_id}/location` | Change location | M | Booking edit dialog | Exposed in desktop | `BookingService.change_location` | Complete, event-sourced |
| PATCH | `/bookings/{booking_id}/participant-count` | Change participants | M | Booking edit dialog | Exposed in desktop | `BookingService.change_participant_count` | Complete, event-sourced |
| PATCH | `/bookings/{booking_id}/notes` | Change manager notes | M | Booking edit dialog | Exposed in desktop | `BookingService.update_notes` | Complete, event-sourced |
| POST | `/bookings/{booking_id}/instructors` | Assign instructor | M | Embedded Booking Details | Exposed in desktop | `AssignmentService.assign` | Complete, event-sourced |
| DELETE | `/bookings/{booking_id}/activities/{booking_activity_id}/instructors/{instructor_id}` | Remove assignment | M | Embedded Booking Details | Exposed in desktop | `AssignmentService.remove` | Complete, confirmed/event-sourced |
| POST | `/bookings/{booking_id}/replay` | Reconstruct aggregate for diagnostics | M | Backend maintenance only | Intentionally internal | `query_handlers.replay_booking`; no service/control | Never expose in desktop |

### Final role and screen matrix

| Screen/action | Manager | Instructor | Customer |
|---|---|---|---|
| Dashboard | Six counts, operational lists, all management shortcuts | Scoped upcoming/assigned/open work | Own booking summary/list |
| Customers / contacts | Directory CRUD with protected customer Delete; nested contacts retain soft deactivation | Unavailable; backend 403 | Own read-only profile only; directory unavailable |
| Instructors | Business-profile CRUD with protected Delete | Own read-only profile only | Unavailable |
| Activities | Full textual soft-deactivation CRUD | Active-only catalog | Active-only catalog |
| Bookings | Full filters/details and event-sourced commands | Assigned My Events, safe fields | Own My Bookings/details |
| History | Manager-only raw event history | Unavailable; backend 403 | Unavailable; backend 403 |
| Assignments | Embedded assign/remove | No controls or self-claim | No access |
| Open Events | List and safe detail | List and safe detail | No screen; backend 403 |

### Final known limitations and deferrals

- Synchronous HTTP may briefly block the Qt event loop.
- List responses return current-page count, not a total; Next uses full-page inference.
- Booking filter selectors are bounded to 100 active records and searched locally.
- Open Events search is client-side over its unpaged endpoint response.
- Multi-command booking edits are sequential, not atomic; failures refresh authoritative state.
- No instructor schedule-conflict detection or numeric required-instructor count exists.
- Instructor email uniqueness is application-enforced; profile creation does not create login credentials, and no database one-to-one user/profile constraint exists.
- Legacy events without `booking_activity_id` are replay-compatible but not automatically repaired. The one inspected affected record is past and does not block demo/upcoming workflows, so no repair tool was added.
- Activity media mutation UI, Task 13 visual redesign, AI/RAG, password reset, and general user administration remain deferred.

Task 12 is complete with these documented limitations.

### Post-closure customer/instructor deletion correction

Customer and instructor manager workflows now use explicit physical Delete,
not soft deactivate/reactivate. Each delete locks the selected profile and runs
all checks and the DELETE in one transaction. Customer deletion returns 409 if
a booking, immutable booking event, or login user references the customer;
otherwise owned contacts are removed by `customer_contacts.customer_id ON
DELETE CASCADE`. Instructor deletion returns 409 for any active or removed
`booking_instructors` row, immutable instructor assignment/removal event, or
linked login user. Login accounts and auditable booking/assignment history are
never unlinked or deleted automatically. Success is HTTP 204; missing records
are 404. Existing inactive records remain listable through manager filters,
but the desktop no longer offers activation-state mutation for these profiles.

Final acceptance evidence: 75 backend tests and 72 desktop tests passed with no
skips; compileall, 47-operation OpenAPI inventory, role/schema/security scans,
architecture-boundary tests, real-backend role walkthrough, and
`git diff --check` passed. Closure records are inactive or terminal and have no
active temporary assignment.
