Task 05 - Authentication and RBAC

Goal

Add backend authentication and role-based authorization for the Havaya Im NeshamaManagement System.

This task supports:

FR-AUTH-01 - registered users can authenticate.

FR-AUTH-02 - protected backend operations are authorized by role and resource.

The PRD requirement that server-side authorization is authoritative.

This task should come before role-specific desktop UI, bookings, dashboard, RAG,and protected activity/customer workflows.

Required Context

Before implementing, read:

AGENTS.md

PRD_Havaya_Im_Neshama.md

docs/piv/requirements-traceability.md

tasks/02-supabase-postgresql-persistence.md

tasks/03-seed-demo-data.md

tasks/04-customers-contacts-crud-api.md

If implementation details conflict, follow the PRD and AGENTS.md.

Current State

The project already has:

FastAPI backend.

PostgreSQL/Supabase-compatible persistence.

Hebrew seed data.

Customers and contacts CRUD API.

Backend structure using schemas, application services, infrastructurerepositories, and routers.

The project does not yet have:

Login.

Current-user endpoint.

Password hashing.

Server-side role checks.

Protected customer routes.

Roles

Support these MVP roles:

manager
instructor
customer

Access is denied by default and granted by role.

For this task, keep role rules simple:

manager can use the existing customer/contact CRUD API.

instructor must not create, update, or delete customers or contacts.

customer must not create, update, or delete customers or contacts.

Future customer ownership checks for bookings can be left for booking tasks.

Database Requirements

Add or reuse a users table through the existing schema initialization mechanism.

Required fields:

id
username or email
password_hash
role
is_active
customer_id, nullable
instructor_id, nullable
created_at
updated_at

Rules:

Passwords must never be stored in plaintext.

Seed demo users with hashed passwords only.

Do not commit secrets or .env files.

Use parameterized SQL.

Keep database access inside the infrastructure layer.

Suggested demo users:

manager@example.com
instructor@example.com
customer@example.com

Use simple local demo passwords only if they are documented as demo credentialsand are hashed in the database.

Backend API Scope

Implement:

POST /auth/login
GET /auth/me

Suggested login behavior:

Request body contains username/email and password.

Invalid credentials return 401 with a generic message.

Inactive users cannot sign in.

Successful login returns a bearer token and basic user profile.

Suggested current-user behavior:

Requires bearer token.

Returns the signed-in user's id, username/email, role, and relatedcustomer_id/instructor_id if present.

Missing or invalid token returns 401.

Token approach:

Use a simple JWT or existing project auth pattern if one already exists.

Secret/configuration should come from environment variables.

Provide a safe development default only if the project already uses that style,and clearly document it as local-only.

Authorization Scope

Add reusable backend dependencies/helpers for:

getting the current user from the request

requiring authentication

requiring one or more roles

Protect the existing customer/contact mutation routes:

POST /customers
PUT /customers/{customer_id}
DELETE /customers/{customer_id}
POST /customers/{customer_id}/contacts
PUT /customer-contacts/{contact_id}
DELETE /customer-contacts/{contact_id}

For this task:

Require manager for the mutation routes above.

Customer/contact read routes may remain public only if that keeps the tasksmall, but document the decision.

Prefer protecting reads too if it is straightforward and does not break themanual validation flow.

Suggested Files

Follow the existing project structure. Likely files:

backend/app/schemas/auth.py
backend/app/routers/auth.py
backend/app/application/services/auth_service.py
backend/app/infrastructure/repositories/user_repository.py
backend/app/core/security.py
backend/app/core/auth.py
backend/app/main.py

Use different names if the codebase already has a clearer local pattern.

Validation And Error Handling

Use normal FastAPI responses:

401 for missing/invalid token or bad credentials.

403 for authenticated users without the required role.

404 only for missing domain records.

500 only for unexpected backend/database failures.

Error messages should be clear but should not expose database internals orcredential details.

Examples:

{ "detail": "Invalid credentials" }

{ "detail": "Not authenticated" }

{ "detail": "Not authorized" }

Out Of Scope

Do not implement in this task:

PySide6 login screen.

Role-based desktop navigation.

Activities CRUD.

Bookings.

Event Sourcing or CQRS.

Dashboard.

RAG or AI.

Cloudinary or image upload.

Advanced user administration UI.

Password reset or email verification.

Supabase Auth integration unless the project already has it wired.

Documentation

Create:

docs/piv/05-authentication-rbac.md

Update:

docs/piv/requirements-traceability.md

Document:

what was created

which PRD requirements it supports

what files changed

how to run it

how it was validated

demo users and roles, without exposing real secrets

what remains out of scope

what the next task should be

Validation Commands

After implementation, run:

.\.venv\Scripts\python.exe -m compileall backend desktop_client

If backend tests exist, run the relevant test command too.

Manual Acceptance Checks

Minimum checks:

Initialize the database if needed.

Confirm demo users exist with hashed passwords.

Login as manager and receive a token.

Call GET /auth/me with the manager token.

Login as instructor and receive a token.

Login as customer and receive a token.

Invalid password returns 401.

Missing token on a protected route returns 401.

Instructor token cannot create/update/delete customers or contacts and gets403.

Customer token cannot create/update/delete customers or contacts and gets403.

Manager token can create/update/soft-delete a customer.

Acceptance Criteria

Task 05 is complete when:

login endpoint exists and is registered in FastAPI

current-user endpoint exists and is registered in FastAPI

passwords are hashed

demo users for manager, instructor, and customer exist

reusable authentication/authorization helpers exist

protected routes return 401 when unauthenticated

protected routes return 403 when authenticated with the wrong role

manager can still perform customer/contact mutations

SQL uses parameters, not unsafe string concatenation

PIV documentation exists under docs/piv

requirements traceability is updated

compile validation passes