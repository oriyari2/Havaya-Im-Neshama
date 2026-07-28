# Task 12 Manual Verification

## Demo Credentials

- Manager: `manager@example.com` / `manager123`
- Instructor: `instructor@example.com` / `instructor123`
- Customer: `customer@example.com` / `customer123`

These match `backend/app/db/init_db.py`. Do not run `/system/init-db` for normal
verification.

## Start Commands

Backend:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```

Desktop, in another terminal:

```powershell
.\.venv\Scripts\python.exe -m desktop_client.app.main
```

## Milestone 12A

1. Start the backend and desktop.
2. Enter an incorrect manager password. Expect a visible invalid-credentials
   error and remain on Login.
3. Sign in with the manager credentials. Expect Dashboard to load.
4. Stop the backend and navigate or refresh. Expect a clear connection error;
   restart the backend and retry the navigation.
5. For session-expiry verification, use the documented read-only command from
   the repository root while the backend is running:

```powershell
Remove-Item Env:SSLKEYLOGFILE -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe -c "from desktop_client.app.api.client import ApiClient,ApiError; from desktop_client.app.services.auth_service import AuthService; c=ApiClient(); s=AuthService(c).login('manager@example.com','manager123'); d=c.get('/bookings/dashboard'); q=c.get('/customers',{'search':'בית ספר','limit':1,'offset':0}); expired=[]; c.set_unauthorized_handler(lambda:expired.append(True)); c.set_access_token('invalid-token'); kind=''; exec('try:\n c.get(\"/auth/me\")\nexcept ApiError as e:\n kind=e.kind.value'); print({'role':s.role,'dashboard_fields':sorted(d),'query_count':q['count'],'expired_kind':kind,'token_cleared':c.access_token is None,'callback_count':len(expired)})"
```

Expect `role=manager`, the six dashboard fields, `expired_kind=authentication`,
`token_cleared=True`, and `callback_count=1`.

Data side effects: none. Milestone 12A verification performs login and read
queries only. No cleanup is required.

Verified on July 28, 2026 against the configured Supabase-backed development
API. The observed result matched all expectations above.

Further milestone procedures will be appended as their functionality is
implemented and approved.

## Milestone 12B

1. Start the backend and desktop with the commands above.
2. Sign in as manager and open **Customers**. Verify search, city/type/active
   filters, both supported sort choices, paging, selection, and detail loading.
3. Create `Task 12 Delete Customer` with a unique email, edit its notes, and add
   `Task 12 Delete Contact`. Confirm Delete identifies the customer by name.
   Delete it; expect HTTP 204 behavior, a refreshed list, cleared details, and
   both customer and owned contact to be absent.
4. Select a customer with booking history and attempt Delete. Expect 409 and a
   clear dependency message; the selection and record remain. Never delete a
   deterministic demo customer.
5. Sign in as customer. Open **My Profile** and verify only the authenticated
   customer's details and nested contacts are shown. Sign in as instructor and
   verify Customers and My Profile are absent.

Verified July 28, 2026 against the configured backend. The verification record
IDs were customer `f63005a4-c580-4010-a16f-32454e0819b0` and contact
`177961e7-7cf1-4708-a6e0-2ab77edd0e2b`; both were soft-deactivated after all
CRUD/reactivation checks. No schema/init/reseed operation was run.

## Milestone 12C

Use the start commands and deterministic credentials above.

1. As manager, open **Activities**. Verify the All/Active/Inactive choices,
   search, audience/season/tag filters, next/previous paging, selection, and
   full textual details.
2. Create `Task 12C Test Activity` with audience `Task12C Audience`, season
   `Task12C Season`, tag `task12c`, positive duration/capacity, and the
   description `Created for Task 12C manual verification`.
3. Edit the description and capacity. Deactivate with confirmation, find it via
   Inactive and All, reactivate it, then leave it deactivated for cleanup.
4. As instructor and customer, verify Activities is present, only active rows
   are returned, search/filter/detail work, and all management controls are
   absent. Direct mutation requests must return 403.
5. Do not run init-db, seed, schema, physical deletion, or image endpoints.

Verified July 28, 2026 against the configured API through the shared desktop
client/service path. Activity `be2959ab-a12f-43b2-a2eb-6aaecf88616a` exercised
all textual operations and remains inactive. Both non-manager roles returned
active rows only and received 403 for direct creation attempts.

## Milestone 12D

1. As manager, open **Instructors** and verify search, city/active filters,
   name/creation ordering, paging, selection, detail, and retry states.
2. Create `Task 12D Test Instructor` with a unique profile email and notes
   `Created for Task 12D manual verification`. No password is requested because
   this creates a business profile, not a login account.
3. Edit and Delete the unassigned temporary profile. Expect the list to refresh,
   details to clear, and subsequent detail read to return 404. Attempt Delete on
   an instructor with assignment history; expect 409 and no data change. Never
   delete the deterministic demo instructor.
4. As `instructor@example.com`, verify owned My Profile, no directory, and 403
   for direct directory and other-instructor detail calls.
5. As `customer@example.com`, verify customer My Profile remains correct, no
   instructor navigation exists, and instructor API access returns 403.

Verified July 28, 2026. Profile
`41832a9d-2b63-49e4-8e00-fa96d093c55b` remains inactive. No user, assignment,
seed, schema, or physical deletion operation was performed.

## Milestone 12E

As manager, select a booking activity, assign an active instructor, verify the
version/history advance, verify duplicate rejection, then remove with explicit
confirmation. A stale expected version must return 409 and refresh without an
automatic retry. Instructor Open Events must open only the safe detail; customer
assignment reads and safe-open detail must return 403.

Verified with booking `19a16e61-2ecd-4bab-a54a-20ffbcbdb7f0` and activity
`10627401-2ce6-466a-a34a-c6a4c0377eb2`. No active assignment remains; the
booking is cancelled and create/assign/remove/cancel history is preserved.

## Milestone 12F

1. Start backend and desktop with the commands above.
2. Manager: verify the six dashboard cards, shortcuts, status drill-down,
   Create Booking, named customer/activity/instructor filters, `YYYY-MM-DD`
   range validation, paging, retained visible selection, readable detail, and
   create/edit/confirm/cancel/complete. Recheck embedded assignments.
3. Instructor: verify Dashboard, Activities, My Events, Open Events, and My
   Profile only. Safe event/booking detail must omit customer, price, notes,
   history, and assignment controls.
4. Customer: verify Dashboard, Activities, My Bookings, and My Profile only.
   Status drill-down and pagination remain owned-only; Open Events is absent.
5. Stop/restart the backend during a read to verify connection error and retry.
   Use a stale version only on a disposable Task 12F booking for the 409 flow.
6. Never call init-db, seed, replay, schema, physical delete, or media routes.
   Finish disposable bookings through a supported terminal status.

Verified July 28, 2026. Booking
`55904e20-a46a-4b80-9828-468d79380256` was created and immediately completed;
it remains as a terminal two-event audit record. All deterministic accounts
authenticated, and customer Open Events returned 403.

## Milestone 12G Final Walkthrough

Verified July 28, 2026 against a fresh backend process using all three seeded
accounts and the shared HTTP/service contracts.

Manager verification covered dashboard reads, entity filters and detail,
customer/contact/activity/instructor create and update, the then-current soft-deactivation checks,
booking creation with a stable activity, all five granular edits, confirm,
complete, assignment, duplicate rejection (400), stale version rejection (409),
removal, raw history, Open Events, and safe detail. Closure record IDs:

- customer `40ffb417-00b9-4371-a2f1-b6c979bf9c23` — inactive
- contact `014a9c9b-8f78-4018-9fa6-e34c630bb35e` — inactive
- activity `fa849c9a-c448-448f-b574-329935b42731` — inactive
- instructor `35c43871-1203-47b3-b84c-adf63f1796a3` — inactive

- booking `e42c5210-ae48-46da-88a5-419e4a6b2025` — COMPLETED, version 15
- booking activity `a1c6c9fa-7e1c-4bf8-b795-31ec5b449013`

## Post-closure protected deletion verification

Verified July 28, 2026 through the supported HTTP APIs only. Temporary customer
`3bef7c04-c27b-45d9-baed-864fe10fdbfd`, owned contact
`6b11a5a9-3f27-4f75-a83c-45a8aa657e4d`, and instructor
`4e962c2f-971f-4c36-a8c2-9a5407b002ad` were created and physically removed by
the new DELETE endpoints. Customer/instructor detail returned 404 and searched
lists returned zero; updating the cascaded contact returned 404. Seeded linked
profiles, and instructors discovered through both assigned and removed booking
events, returned 409. Customer/instructor direct DELETE returned 403, both
logins remained usable, and activity deactivate/reactivate was exercised with
the activity restored to inactive. No direct SQL, init, seed, schema, replay,
media, or user-administration mutation was used.

The booking has no active assignment. Its immutable history contains the
creation, assignment/removal, granular edits, confirmation, and completion.
During closure the audit discovered that completed bookings still accepted
operational commands; those five attempted edits are retained in history as
evidence. After the aggregate fix, a fresh direct notes update returned 400.

Instructor verification confirmed active Activities, assigned detail only
while assigned, safe Open Events detail before assignment, ordinary detail 403
before assignment, no manager navigation/controls, directory denials, and raw
history 403. Customer verification confirmed own My Bookings/detail and My
Profile, no Open Events/management navigation, assignment/history 403, and no
cross-customer directory access. An invalid bearer token returned 401; desktop
tests verify token clearing and return to Login.

The read-only seed dry-run performed no mutation and aborted safely because
Task 12/manual records reference deterministic demo parents/users. Demo users
still authenticate. The one record without a booking-activity target,
`e4d1664c-2b6e-4f30-acdc-da4254dc8ba8`, is a past July 17 legacy manual booking;
all current demo and API-created bookings have stable targets. Option A
(document only) was selected and no repair, init, seed, replay, schema reset,
physical deletion, direct SQL mutation, or media mutation was run.
