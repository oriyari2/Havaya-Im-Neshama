# Task 03 - Demo Seed Data

## What Was Created

The demo seed was rebuilt as a safe additive seeding workflow for the Hebrew
business system "חוויה עם נשמה".

Created:

- `backend/app/db/demo_seed_catalog.py` with deterministic Hebrew demo
  definitions.
- `backend/app/db/seed_demo_data.py` with dry-run, apply, and verify modes.
- Expanded `backend/tests/test_seed_demo_data.py` coverage for seed contracts.

The catalog currently defines 16 customers, 24 contacts, 11 instructors, 12
activities, 14 inventory items, activity instructions, equipment requirements,
32 realistic bookings, booking activities, instructor assignment history,
equipment usage, and price components.

The corrected catalog uses an explicit `PRIMARY_CONTACT_BY_CUSTOMER_KEY` map
instead of arithmetic contact selection. The apply path validates the existing
`customer@example.com`, `instructor@example.com`, and `manager@example.com`
login links and aborts if a required account/profile link is missing. It does
not reset passwords or relink demo users.

The apply path now treats post-apply verification as part of the same
transaction. If verification reports failures, it raises a dedicated
`SeedVerificationError`, rolls the transaction back, avoids commit, returns a
non-zero CLI exit, and prints only sanitized verification failure names.

Activity IDs are resolved in this order: existing seed-owned ID, existing exact
normalized Hebrew name, then a new deterministic seed ID. The resolved IDs are
used for booking events, booking activities, instruction notes, equipment
requirements, and related rows to avoid duplicate Hebrew activities.

Instruction notes are resolved by the resolved activity ID and normalized
Hebrew title. Equipment requirements are resolved by the resolved activity ID
and resolved inventory item ID. Existing regular relationships are reused,
manual rows are not overwritten, and only deterministic seed-owned
relationships are updated or created. The dry-run report includes reused
instruction notes, instruction notes to create, reused equipment requirements,
and equipment requirements to create.

The dry-run report also detects legacy seed-owned detail rows attached to the
deterministic demo bookings when old booking activity, equipment, or price
component IDs would leave row counts higher than the current catalog. It does
not delete those rows automatically; the warning identifies the affected table
and asks for a manual review/remap or removal before `--apply`.

## PRD Requirements Supported

This advances the academic MVP by supplying realistic data for:

- PostgreSQL / Supabase-compatible persistence.
- Customer, contact, instructor, activity, inventory, and booking management.
- CQRS booking read models and dashboard filters.
- Event Sourcing for booking creation, status changes, assignment, removal,
  and reassignment history.
- Role-specific customer and instructor dashboards using the existing demo
  login accounts.

## Event Sourcing Decision

Production booking commands generate random booking IDs, but the seed requires
deterministic identities and safe partial reruns. The seeder therefore uses a
small explicit seeding path that delegates to the same booking aggregate,
booking event table, and projection sync used by production command handlers.

It appends deterministic seed events only when the expected event is missing,
replays the aggregate, and updates projections through
`booking_projection_repository`.

Existing seed bookings preserve event-sourced aggregate fields on rerun. The
seeder uses the replayed aggregate date, location, participant count, agreed
price, instructor requirement, notes, status, and version instead of
recomputing relative catalog values and overwriting the projection directly.
Seed-owned event-sourced changes should be represented by appended domain
events.

Instructor assignment verification now checks active assignment projection rows
by booking activity and resolved instructor ID, and checks ordered
`BookingInstructorAssigned` / `BookingInstructorRemoved` event history. Real
reassignment is verified as assign instructor A, remove A, assign instructor B
for the same booking activity, with B distinct from A.

Catalog assignment coverage is calculated by replaying assignment steps in
order. `assign` adds an active booking-activity/instructor pair and `remove`
removes it. Booking 15 is intentionally modeled as a reassignment scenario:
instructor 3 is assigned, removed, and replaced by instructor 6, so the
confirmed instructor-required activity ends with active coverage.

Rich display/operations fields such as `event_title`, `primary_contact_id`,
`customer_notes`, vehicle/loading notes, multi-activity rows, equipment usage,
and price components are intentionally projection/supporting-table data for the
demo seed. They are documented outside the event-sourced booking aggregate,
whose history remains focused on booking creation, status, schedule, location,
price, participant count, notes, and instructor assignment/removal events.

Multi-activity start offsets are cumulative from all prior activity durations.
The optional 10 NIS sign-quiz price component is explicit through
`include_sign_quiz_addon`; sukkah bookings can appear with or without the
add-on, and bookings where the sign quiz is a full second activity do not also
receive the add-on.

Large multi-activity bookings that include the sign quiz now cap the sign-quiz
booking activity at its supported activity maximum and use notes to describe
round-based operation for the wider event audience.

## How To Run

Default mode is read-only dry run:

```powershell
.\.venv\Scripts\python.exe -m backend.app.db.seed_demo_data
```

Read-only verification:

```powershell
.\.venv\Scripts\python.exe -m backend.app.db.seed_demo_data --verify
```

Apply later, after reviewing the dry run:

```powershell
.\.venv\Scripts\python.exe -m backend.app.db.seed_demo_data --apply --confirm "אני מאשר יצירת נתוני דמו"
```

`--apply` is the only mode that writes. The seed does not run during imports or
normal FastAPI startup.

## Validation

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
.\.venv\Scripts\python.exe -m unittest discover -s desktop_client/tests -v
.\.venv\Scripts\python.exe -m compileall backend desktop_client
git diff --check
.\.venv\Scripts\python.exe -m backend.app.db.seed_demo_data
```

The final command is read-only.

## Next Task

After applying the seed manually, validate the dashboards and booking filters
against the configured PostgreSQL database, especially:

- `customer@example.com` customer visibility.
- `instructor@example.com` future assignments.
- open confirmed bookings that still require assignment.
- booking history screens for assignment removal and reassignment.
