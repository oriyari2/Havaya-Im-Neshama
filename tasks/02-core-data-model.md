# Task 02 - Supabase PostgreSQL Persistence

## Goal

Build the first real database layer for the Havaya Im Neshama CRM using
Supabase PostgreSQL.

The data model should match the real business better than a generic CRM:
customers are usually organizations such as schools, communities, municipalities,
seminars, youth groups, or event organizers. Each customer can have one or more
contact people with roles. Bookings can include several activities, instructors,
inventory quantities, loading notes, and price components.

This task is still an MVP foundation. Keep it simple, but design the tables so
the project will not need to rewrite the whole database immediately in the next
task.

## Business Context

Havaya Im Neshama provides educational and experiential activities for children,
families, schools, communities, and organizations.

Known activities include, for example:

- Tafos Et HaOr
- Merutz HaTzofen
- Chidon Shlatim
- Bag printing workshop
- Sukkah decoration workshop on canvas

The business needs to manage:

- Customers and organizations
- Contact people and their roles
- Activities and activity packages
- Event bookings that may include more than one activity
- Instructors assigned to specific activities inside a booking
- Inventory items with quantities
- Equipment requirements per activity
- Adjusted equipment quantities per booking
- Price components, additions, discounts, and final price
- Simple loading / vehicle notes
- Basic instructor payment status only, not payroll

## Out Of Scope For This Task

Do not implement:

- Authentication or users
- Desktop UI screens
- RAG
- Event sourcing
- Cloudinary
- Invoice generation
- Advanced instructor scheduling
- Advanced payroll
- Advanced inventory reservation logic
- WhatsApp automation
- AI features
- Full calendar UI

## Technology Requirements

Use Supabase PostgreSQL as the database.

Use a normal PostgreSQL connection from the FastAPI backend. Do not use SQLite.

Recommended Python package:

```text
psycopg[binary]
```

If SQLAlchemy is already present in the project, it may be used. Otherwise, keep
the implementation simple with direct SQL and psycopg.

## Environment Variables

Add the following to `.env.example`:

```text
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@YOUR_SUPABASE_HOST:5432/postgres
```

The real `.env` file must not be committed.

## Required Tables

Use UUID primary keys.

Use `created_at timestamptz not null default now()`.

Use `updated_at timestamptz not null default now()`.

Use foreign keys where relevant.

Use simple `text` status fields for now. Do not create complicated PostgreSQL
enum types unless the existing project already uses them.

### customers

Represents the customer organization, not necessarily the individual person.

Examples:

- School
- Community center
- Municipality department
- Synagogue community
- Seminary
- Youth group
- Private event organizer

Fields:

- id: UUID primary key
- name: text, required
- customer_type: text, optional
- city: text, optional
- address: text, optional
- phone: text, optional
- email: text, optional
- notes: text, optional
- is_active: boolean, default true
- created_at
- updated_at

Suggested customer_type values:

- school
- community
- municipality
- synagogue
- seminary
- youth_group
- private
- other

### customer_contacts

Represents actual people connected to a customer.

One customer can have several contacts.

Fields:

- id: UUID primary key
- customer_id: UUID foreign key to customers(id), required
- full_name: text, required
- role_title: text, optional
- phone: text, optional
- email: text, optional
- is_primary: boolean, default false
- notes: text, optional
- is_active: boolean, default true
- created_at
- updated_at

Suggested role_title examples:

- manager
- social_coordinator
- community_coordinator
- secretary
- parent_committee
- rabbi
- teacher
- other

Important: store `role_title` as text for now, because the real titles may vary.

### instructors

Represents guides / instructors who can run activities.

Fields:

- id: UUID primary key
- full_name: text, required
- phone: text, optional
- email: text, optional
- city: text, optional
- notes: text, optional
- is_active: boolean, default true
- created_at
- updated_at

Do not implement advanced payroll. Payment can be tracked only on booking
assignments.

### activities

Represents activity templates sold by the business.

Fields:

- id: UUID primary key
- name: text, required
- description: text, optional
- default_duration_minutes: integer, optional
- min_participants: integer, optional
- max_participants: integer, optional
- base_price: numeric, optional
- price_notes: text, optional
- default_setup_minutes: integer, optional
- default_cleanup_minutes: integer, optional
- is_active: boolean, default true
- created_at
- updated_at

### activity_instruction_notes

Represents instructor instructions / activity scheme.

Use this as a simple text-based guide for now.

Fields:

- id: UUID primary key
- activity_id: UUID foreign key to activities(id), required
- title: text, required
- body: text, required
- sort_order: integer, default 0
- created_at
- updated_at

### inventory_items

Represents actual inventory items with quantities.

Fields:

- id: UUID primary key
- name: text, required
- category: text, optional
- unit: text, optional
- quantity_total: integer, required, default 0
- quantity_available: integer, required, default 0
- storage_location: text, optional
- needs_charging: boolean, default false
- notes: text, optional
- is_active: boolean, default true
- created_at
- updated_at

Suggested category values:

- activity_equipment
- consumable
- printed_material
- electronic
- battery_or_charging
- vehicle_loading
- other

Examples:

- Laser tag vests
- Laser tag devices
- Voting signs
- Printed cards
- Canvas kits
- Bags
- Chargers
- Extension cables

### activity_equipment_requirements

Defines the default inventory required for an activity.

Fields:

- id: UUID primary key
- activity_id: UUID foreign key to activities(id), required
- inventory_item_id: UUID foreign key to inventory_items(id), required
- quantity_required: integer, required, default 1
- quantity_per_participant: numeric, optional
- is_optional: boolean, default false
- notes: text, optional
- created_at
- updated_at

Use either:

- `quantity_required` for fixed equipment, or
- `quantity_per_participant` for items that depend on number of children.

Do not implement automatic calculation yet unless it is easy. The schema should
allow it later.

### bookings

Represents an event/order.

A booking can include several activities through `booking_activities`.

Fields:

- id: UUID primary key
- customer_id: UUID foreign key to customers(id), required
- primary_contact_id: UUID foreign key to customer_contacts(id), optional
- event_title: text, optional
- event_date: timestamptz, optional
- location_name: text, optional
- location_address: text, optional
- city: text, optional
- participants_count: integer, optional
- audience_type: text, optional
- status: text, required, default 'draft'
- internal_notes: text, optional
- customer_notes: text, optional
- requires_vehicle: boolean, default false
- vehicle_notes: text, optional
- loading_notes: text, optional
- created_at
- updated_at

Booking status should support at least:

- draft
- quoted
- confirmed
- cancelled
- completed

Suggested audience_type values:

- children
- families
- school
- community
- staff
- mixed
- other

### booking_activities

Connects bookings to one or more activities.

This replaces the earlier simple `bookings.activity_id` design.

Fields:

- id: UUID primary key
- booking_id: UUID foreign key to bookings(id), required
- activity_id: UUID foreign key to activities(id), required
- start_time: timestamptz, optional
- duration_minutes: integer, optional
- participants_count: integer, optional
- location_detail: text, optional
- sort_order: integer, default 0
- notes: text, optional
- created_at
- updated_at

### booking_instructors

Assigns instructors to a specific activity inside a booking.

Fields:

- id: UUID primary key
- booking_activity_id: UUID foreign key to booking_activities(id), required
- instructor_id: UUID foreign key to instructors(id), required
- role: text, optional
- payment_status: text, required, default 'not_relevant'
- notes: text, optional
- created_at
- updated_at

Payment status should support at least:

- not_relevant
- unpaid
- paid

Suggested role values:

- lead
- assistant
- logistics
- driver
- other

### booking_equipment_items

Represents the planned equipment quantities for a booking.

This can start as a manually edited checklist generated from activity defaults
later. For this task, only create the table.

Fields:

- id: UUID primary key
- booking_id: UUID foreign key to bookings(id), required
- inventory_item_id: UUID foreign key to inventory_items(id), required
- quantity_planned: integer, required, default 1
- quantity_packed: integer, optional
- quantity_returned: integer, optional
- status: text, required, default 'planned'
- notes: text, optional
- created_at
- updated_at

Equipment status should support at least:

- planned
- packed
- missing
- returned

### booking_price_components

Stores price breakdown for a booking.

Fields:

- id: UUID primary key
- booking_id: UUID foreign key to bookings(id), required
- component_type: text, required
- description: text, required
- quantity: numeric, required, default 1
- unit_price: numeric, required, default 0
- total_price: numeric, required, default 0
- sort_order: integer, default 0
- created_at
- updated_at

Suggested component_type values:

- base_activity
- extra_activity
- participants_addition
- travel
- materials
- discount
- other

Important:

- Discounts can be represented with a negative `total_price`.
- Do not implement invoices in this task.
- Do not implement tax calculations unless already very simple.

## API Requirements

Keep the API minimal. This task is about creating persistence, not a full CRM UI.

Required endpoints:

```text
GET /health
GET /system/db-status
POST /system/init-db
GET /system/schema-summary
```

Expected behavior:

- `GET /health` should continue returning status ok.
- `GET /system/db-status` should check that PostgreSQL is reachable.
- `POST /system/init-db` should create all tables if they do not exist.
- `GET /system/schema-summary` should return the list of expected tables and
  whether each exists.

Do not create full CRUD routes yet unless it is already trivial in the existing
project structure. CRUD will be a separate task.

## Recommended Backend Structure

Adjust if the existing project uses a different structure, but keep it clean.

```text
backend/
  app/
    db/
      connection.py
      init_db.py
      schema.py
    routers/
      system.py
```

`connection.py`:

- Reads `DATABASE_URL`.
- Opens PostgreSQL connections.
- Fails clearly if `DATABASE_URL` is missing.

`schema.py`:

- Contains the SQL statements for the required tables.
- Keeps table names in one constant list for schema summary.

`init_db.py`:

- Runs `CREATE TABLE IF NOT EXISTS`.
- Creates required indexes where useful.

`system.py`:

- Implements database status and schema endpoints.

## Suggested Indexes

Create simple indexes:

- customers(name)
- customers(city)
- customer_contacts(customer_id)
- instructors(full_name)
- activities(name)
- bookings(customer_id)
- bookings(event_date)
- bookings(status)
- booking_activities(booking_id)
- booking_instructors(booking_activity_id)
- booking_instructors(instructor_id)
- booking_equipment_items(booking_id)
- booking_price_components(booking_id)

## Seed Data

Optional, only if easy:

Create a small development seed function or SQL file with a few activities:

- Tafos Et HaOr
- Merutz HaTzofen
- Chidon Shlatim
- Bag printing workshop
- Sukkah decoration workshop on canvas

Do not run seed automatically in production. If implemented, expose it only as
a clearly named development helper.

## Verification

After implementation, run:

```powershell
python -m compileall backend desktop_client
```

Run the backend:

```powershell
uvicorn backend.app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/system/db-status
http://127.0.0.1:8000/system/schema-summary
```

Initialize the database:

```powershell
curl -X POST http://127.0.0.1:8000/system/init-db
```

Then check in Supabase Table Editor that the tables exist.

## Done Definition

Task 02 is complete when:

- The backend connects to Supabase PostgreSQL using `DATABASE_URL`.
- `.env.example` documents the required variable.
- The required tables can be created in Supabase.
- The schema supports customers, contacts, activities, instructors, bookings,
  booking activities, inventory, equipment planning, and price components.
- `/health` still works.
- `/system/db-status` works.
- `/system/init-db` works.
- `/system/schema-summary` works.
- The code compiles.
- No secrets or temporary files are committed.

## Instruction For Codex

Implement this task exactly as written.

Use Supabase PostgreSQL, not SQLite.

Keep the implementation simple and focused on persistence.

Do not add authentication, desktop UI screens, RAG, event sourcing, Cloudinary,
invoice generation, advanced inventory reservation, advanced instructor
scheduling, or advanced payroll yet.

After implementation, run compileall and explain exactly how to verify the
database connection and endpoints.
