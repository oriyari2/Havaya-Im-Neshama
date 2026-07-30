# Task 24 PIV: End-to-End Booking Request and Creation Workflow

## Implementation

The existing manager-only `POST /bookings`, `BookingCreated`, event-store, and
projection flow was reused. It now admits Managers and Customers; Customer
ownership and protected initial fields are server-controlled. The role-aware
desktop form is reachable from Bookings and a selected Activity. Instructor
creation remains denied at UI and API layers.

## Requirements

- `FR-BKG-01`: Manager creation.
- `FR-BKG-01A`: authenticated Customer self-service request.
- `FR-AUTH-02`: deny-by-default role authorization.
- `NFR-03`, `NFR-07`, `NFR-08`: responsive MVP, separation, cache/lifecycle safety.

## API and event flow

`POST /bookings` accepts the existing representation with optional
`customer_id` at parsing. Managers must provide it. Customers normally omit it;
if supplied it must match their link. The server forces `NEW`, price zero, and
no instructor requirement. Instructors receive 403.

The unchanged handler validates active Customer/Activity, appends exactly one
`BookingCreated`, updates Booking/default-activity projections, and commits once.
No migration or historical event changed.

## Desktop, cache, and validation

The passive dialog renders role fields. `BookingsPresenter` owns mode, options,
validation, duplicate protection, submission, and reconciliation. Customer
options load only for Managers. Task 23 invalidates Bookings, history,
assignments, open events, and Dashboard—not Users, Instructors, or Activities.

Focused coverage verifies ownership/tampering, Instructor denial, Manager
Customer requirement, protected payloads, Activity preselection, role controls,
and existing Event Sourcing/query behavior: 90 focused Booking tests passed.
Full suites passed with 182 Desktop and 189 Backend tests. A native Windows
64-test combined Qt suite passed. A 25-iteration lifecycle stress run completed
with zero crashes and zero post-shutdown callbacks. Compile and scans passed.

The first combined native run exposed a test-lifetime defect: Task 24's added
dialog test left top-level Qt objects for the following executor suite. Explicit
test teardown now closes and deferred-deletes top-level widgets and drains
deferred deletes; the same combined command then passed. Production lifecycle
code did not require alteration.

## Limitations

Customer requests intentionally begin with zero agreed price and no instructor
requirement. Assignment approval and notifications remain out of scope. Task 25
was not started. No human interactive gestures are claimed; role behavior was
validated through API, Presenter, View, native Qt, and lifecycle automation.
