# Task 06 - Activities CRUD API

## Plan

Build the backend activity catalog API only. Keep desktop UI, bookings, image upload, dashboard, RAG, and future workflow work out of scope.

Supported PRD requirements:

- FR-ACT-01: managers can create, view, update, search, and deactivate activities.
- FR-ACT-02: activity details are persisted and available through the catalog.
- FR-ACT-04: customers and instructors have read-only access to permitted activity information, and mutation APIs reject their roles.

FR-ACT-03 remains out of scope until the image Gateway task.

## Implement

Created:

- `backend/app/schemas/activity.py` with create, update, read, and list response models.
- `backend/app/infrastructure/repositories/activity_repository.py` with parameterized SQL for list, detail, create, update, and soft delete.
- `backend/app/application/services/activity_service.py` with activity use cases and role-shaped read visibility.
- `backend/app/routers/activities.py` with `GET /activities`, `GET /activities/{activity_id}`, `POST /activities`, `PUT /activities/{activity_id}`, and `DELETE /activities/{activity_id}`.

Updated:

- `backend/app/db/schema.py` adds Task 06 activity fields using additive schema columns and indexes for active/season lookups.
- `backend/app/db/init_db.py` applies additive `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` statements during initialization.
- `backend/app/main.py` registers the activities router.

Authorization behavior:

- All activity routes require bearer authentication.
- `manager` can read active and inactive activities and can create, update, and soft-delete.
- `instructor` and `customer` can read active activities only.
- `instructor` and `customer` receive 403 for create, update, and delete.
- Missing or invalid bearer token returns 401.

## Run

Configure `backend/.env` with the PostgreSQL/Supabase connection and auth secret, then apply schema initialization when enabled locally:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```

Use the documented demo users:

- `manager@example.com` / `manager123`
- `instructor@example.com` / `instructor123`
- `customer@example.com` / `customer123`

## Validate

Compile validation:

```powershell
.\.venv\Scripts\python.exe -m compileall backend desktop_client
```

Result: passed.

Database-backed validation against the configured PostgreSQL/Supabase connection:

- Schema initialization completed and added the Task 06 activity columns.
- Manager, instructor, and customer login each returned 200.
- Unauthenticated `GET /activities` returned 401.
- Manager `POST /activities` returned 201.
- Manager `GET /activities` returned 200.
- Instructor and customer `GET /activities` returned 200 and active activities only.
- Hebrew search with `search=בדיקה` returned the created activity.
- Existing activity detail returned 200.
- Missing activity detail returned 404.
- Invalid positive-number input returned 422.
- Instructor create returned 403.
- Customer update returned 403.
- Instructor delete returned 403.
- Manager update returned 200 and persisted the changed capacity.
- Manager delete returned 200 with `is_active=false`.
- Customer detail for the inactive activity returned 403.
- Manager inactive list with `is_active=false` returned the soft-deleted activity.

## Out Of Scope

- PySide6 activity screens and navigation.
- Activity images, Cloudinary, and the Gateway abstraction.
- Bookings, CQRS, Event Sourcing, instructor assignment, dashboard, and RAG.
- Advanced pricing calculation and inventory workflows.

## Next Task

Task 07 should implement the Cloudinary/image Gateway for activity images, keeping provider SDK usage behind an application-owned Gateway abstraction.
