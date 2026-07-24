Task 06 - Activities CRUD API

Goal

Implement the backend API for managing the activity catalog in the Havaya ImNeshama Management System.

This task supports:

FR-ACT-01 - managers can create, view, update, search, and deactivateactivities.

FR-ACT-02 - activity details are persisted and available through thecatalog.

FR-ACT-04 - customers and instructors have read-only access to permittedactivity information, while mutation APIs reject their roles.

This task should come after authentication/RBAC and before activity imageupload, bookings, dashboard, RAG, and desktop activity screens.

Required Context

Before implementing, read:

AGENTS.md

PRD_Havaya_Im_Neshama.md

docs/piv/requirements-traceability.md

tasks/02-supabase-postgresql-persistence.md

tasks/03-seed-demo-data.md

tasks/04-customers-contacts-crud-api.md

tasks/05-authentication-rbac.md

docs/piv/05-authentication-rbac.md, if it exists

If implementation details conflict, follow the PRD and AGENTS.md.

Current State

The project already has:

FastAPI backend.

PostgreSQL/Supabase-compatible persistence.

Hebrew seed data.

Authentication and RBAC.

Customers and contacts CRUD API.

Backend structure using schemas, application services, infrastructurerepositories, and routers.

The project may already have an activities table or seed activity data fromearlier persistence/seed tasks. Reuse the existing schema when possible. If theschema is missing fields required by the PRD, extend it in the existing databaseinitialization/migration style.

Business Context

An activity is an offering in the catalog, for example:

laser activity

code race

signs quiz

creative workshop

holiday or school activity

The catalog should support Hebrew names, descriptions, equipment notes,preparation notes, and tags. Do not assume English-only values.

Required Activity Data

Store or expose these fields as far as the current schema allows:

id
name
description
target_audience
duration_minutes
recommended_capacity
pricing_rule
required_equipment
preparation_notes
season
tags
is_active
created_at
updated_at

Notes:

name is required.

description, target_audience, pricing_rule, required_equipment,preparation_notes, season, and tags may be optional.

duration_minutes and recommended_capacity should be positive numbers whensupplied.

is_active should default to true.

Tags may be stored as text, JSON, or a related table depending on the existingproject pattern. Prefer the simplest schema-compatible approach.

Required API Routes

Add an activities router, for example:

backend/app/routers/activities.py

Register the router in the FastAPI app using the existing project pattern.

Implement:

GET /activities
GET /activities/{activity_id}
POST /activities
PUT /activities/{activity_id}
DELETE /activities/{activity_id}

Route Behavior

GET /activities

Return a list of activities.

Support optional query parameters:

search
target_audience
season
tag
is_active
limit
offset

Search should match at least:

activity name

description

target audience

pricing rule

required equipment

preparation notes

season

tags, if tags are searchable in the chosen schema

Search must support Hebrew text.

Default behavior:

Return active activities unless is_active is explicitly provided.

Use a predictable order, such as activity name or creation date.

Use a reasonable default limit, for example 50.

GET /activities/{activity_id}

Return one activity by ID.

If the activity does not exist, return 404.

POST /activities

Create a new activity.

Authorization:

manager only.

Validation:

name must not be empty.

duration_minutes, if provided, must be greater than zero.

recommended_capacity, if provided, must be greater than zero.

is_active should default to true.

Return the created activity.

PUT /activities/{activity_id}

Update an existing activity.

Authorization:

manager only.

Validation:

name must not become empty.

duration_minutes, if provided, must be greater than zero.

recommended_capacity, if provided, must be greater than zero.

Return 404 if the activity does not exist.

Update updated_at.

Return the updated activity.

DELETE /activities/{activity_id}

Do not physically delete activities in this MVP.

Implement this route as a soft delete:

is_active = false

Authorization:

manager only.

Update updated_at.

Return a clear success response or the updated activity.

If the activity does not exist, return 404.

Authorization Rules

Use the existing authentication/RBAC helpers from Task 05.

Required behavior:

Missing or invalid token on protected routes returns 401.

Authenticated user with wrong role returns 403.

Missing activity record returns 404.

Role behavior for this task:

manager can read and mutate all activities.

instructor can read active activities only.

customer can read active activities only.

instructor and customer cannot create, update, or deactivate activities.

If the current implementation treats the activity catalog as public, do not leavemanager-only fields exposed publicly. Prefer requiring authentication for allactivity routes in this MVP, because the desktop application is role-based andthe PRD emphasizes server-side authorization.

Architecture Rules

Keep the implementation aligned with the existing backend structure:

Routers stay thin and contain HTTP-level logic only.

Pydantic request/response schemas belong in backend/app/schemas.

Business/use-case logic belongs in backend/app/application.

Database access belongs in backend/app/infrastructure.

Shared authentication/config helpers belong in backend/app/core.

Use parameterized SQL only.

Do not let the desktop client access PostgreSQL directly.

Suggested files:

backend/app/schemas/activity.py
backend/app/routers/activities.py
backend/app/application/services/activity_service.py
backend/app/infrastructure/repositories/activity_repository.py
backend/app/db/schema.py
backend/app/db/seed.py
backend/app/main.py

Use different names if the codebase already has a clearer local pattern.

Out Of Scope

Do not implement in this task:

PySide6 activity screens.

Desktop navigation changes.

Activity image upload.

Cloudinary or another image provider.

Image Gateway abstraction.

Bookings.

Event Sourcing or CQRS.

Instructor assignment.

Dashboard.

RAG or AI.

Advanced pricing calculation engine.

Inventory management.

Public marketing catalog.

Keep this task focused on the activity catalog API only.

Documentation

After implementation, create or update:

docs/piv/06-activities-crud-api.md
docs/piv/requirements-traceability.md

The PIV document should explain:

What was created.

Which PRD requirements were advanced.

Which files changed.

How to run it.

How it was validated.

What remains out of scope.

What the next task should be.

Update requirements traceability so:

FR-ACT-01 is marked implemented at API level.

FR-ACT-02 is marked implemented at API/persistence level.

FR-ACT-04 is marked implemented for backend authorization.

FR-ACT-03 remains not started until the Gateway/image task.

Activity UI remains not started until the desktop task.

Validation

Run:

.\.venv\Scripts\python.exe -m compileall backend desktop_client

When possible, validate database-backed behavior against the configuredPostgreSQL/Supabase connection.

Manual HTTP checks:

Manager login succeeds.

Instructor login succeeds.

Customer login succeeds.

GET /activities with manager token returns activities.

GET /activities with instructor token returns active activities only.

GET /activities with customer token returns active activities only.

GET /activities/{activity_id} returns 200 for an existing permittedactivity.

GET /activities/{missing_id} returns 404.

Missing or invalid token behavior matches the chosen route protection policy.

Manager can create an activity.

Manager can update an activity.

Manager can deactivate an activity.

Instructor cannot create, update, or deactivate activities and receives 403.

Customer cannot create, update, or deactivate activities and receives 403.

Search works with Hebrew text.

Positive-number validation works for duration and capacity.

Suggested PowerShell checks can use the same bearer-token pattern as Task 05.

Acceptance Criteria

This task is complete when:

Activity CRUD API exists and is registered in FastAPI.

Activity data is persisted in PostgreSQL/Supabase-compatible storage.

Activity list/search/detail work with Hebrew data.

Activity mutations are restricted to manager.

Non-manager roles have read-only activity access.

Soft delete/deactivation is implemented.

Routers remain thin and database logic stays in the infrastructure layer.

PIV documentation and traceability are updated.

Compile validation passes.