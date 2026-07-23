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

The script is safe to run multiple times. It uses stable UUIDs for demo records
and deletes only those known demo UUIDs before inserting the fresh demo dataset.
It does not delete non-demo records.

## Run

From the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m backend.app.db.seed_demo_data
```

Expected output includes:

```text
Demo data seeded successfully.
Customers: 7
Contacts: 9
Activities: 5
Bookings: 5
```

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
