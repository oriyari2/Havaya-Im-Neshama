# Task 03 - Seed Demo Data

## Plan

Add a backend-owned seed script for realistic Hebrew demo data that uses the
existing PostgreSQL connection helper. The data supports early testing of
customers, contacts, instructors, activities, equipment, bookings, assignments,
and price lines without adding any frontend database access.

## Implement

Created `backend/app/db/seed_demo_data.py`.

The script inserts demo records into:

- `customers`
- `customer_contacts`
- `instructors`
- `activities`
- `activity_instruction_notes`
- `inventory_items`
- `activity_equipment_requirements`
- `bookings`
- `booking_activities`
- `booking_instructors`
- `booking_equipment_items`
- `booking_price_components`

All business-facing demo content is Hebrew and represents the business
"חוויה עם נשמה". The contacts, phone numbers, and email addresses are fake demo
values only, using examples such as `050-0000001` and `demo1@example.com`.

The refresh uses stable UUIDs for demo records and reserves the three demo-user
email addresses. Records using the reserved UUID range are demo-owned. Records
attached to demo parents are part of the demo object graph and are checked
before deletion.

Before changing data, the command checks the known customer, contact, activity,
instructor, inventory, booking, and booking-activity relationships. It aborts
if an external row would be deleted by a cascade or would prevent deletion
through a foreign key. The refresh is therefore destructive only to the
verified demo object graph.

The business-data refresh and recreation of the manager, instructor, and
customer demo users run in one transaction. A failure rolls back the complete
refresh. Booking statuses use the domain values `NEW`, `CONFIRMED`, `COMPLETED`,
and `CANCELLED`.

## Run

From the repository root in PowerShell, preview the affected object groups and
row counts without writing anything:

```powershell
.\.venv\Scripts\python.exe -m backend.app.db.seed_demo_data --dry-run
```

After reviewing the preview, perform the refresh:

```powershell
.\.venv\Scripts\python.exe -m backend.app.db.seed_demo_data
```

The refresh recreates these authentication users through the existing
`seed_demo_users()` implementation:

- `manager@example.com` / `manager123`
- `instructor@example.com` / `instructor123`
- `customer@example.com` / `customer123`

`POST /system/init-db` is not required afterward because the refresh recreates
the demo users itself.

## Validate

Run Python compilation:

```powershell
.\.venv\Scripts\python.exe -m compileall backend desktop_client
```

Then run the seed script and confirm records exist in the main seeded tables:

- `customers`
- `customer_contacts`
- `activities`
- `inventory_items`
- `bookings`

## Result

Task 03 provides repeatable Hebrew demonstration data for the existing
PostgreSQL schema while keeping all database access inside the FastAPI backend
codebase.
