# Task 05 - Authentication and RBAC

## Plan

Harden backend authentication and server-side authorization for the academic MVP.

Supported PRD requirements:

- FR-AUTH-01: registered users can authenticate.
- FR-AUTH-02: protected backend operations are authorized by role and resource ownership.
- NFR-04: credentials and API secrets are supplied through environment variables and excluded from source control.

Out of scope:

- PySide6 login screen and role-based desktop navigation.
- Activities, bookings, dashboard, RAG, Cloudinary, and user administration UI.
- Instructor-to-customer read access until a clear instructor/customer relationship exists in a future booking or instructor task.

## Implement

Created or retained:

- `backend/app/schemas/auth.py` with login, token, and current-user response models.
- `backend/app/core/auth.py` with reusable `get_current_user` and `require_roles` FastAPI dependencies.
- `backend/app/infrastructure/repositories/user_repository.py` for parameterized user SQL.
- `backend/app/application/services/auth_service.py` for login and token-to-user use cases.
- `backend/app/routers/auth.py` with `POST /auth/login` and `GET /auth/me`.

Hardened:

- `backend/app/core/security.py` now uses `PyJWT` for JWT creation and validation instead of custom HMAC/JWT logic.
- `AUTH_SECRET_KEY` is loaded from the process environment after the shared backend loader reads `backend/.env`. A fixed fallback is allowed only for `APP_ENV=development`, `APP_ENV=local`, or `APP_ENV=test`; non-local runtime without a real secret raises an error.
- `backend/.env.example` documents `AUTH_SECRET_KEY=change-me-in-local-env`, `APP_ENV=development`, and `INIT_DB_ENABLED=false`.
- A strong local `AUTH_SECRET_KEY` was generated into `backend/.env`. This file is ignored and must not be committed.
- Customer/contact reads now require authentication.
- Customer/contact mutations remain manager-only.
- `backend/app/application/services/customer_service.py` applies resource-aware customer read rules.
- `backend/app/routers/system.py` prevents `/system/init-db` unless the app is running in local/development/test mode and `INIT_DB_ENABLED=true`.
- `backend/app/db/init_db.py` links seeded customer/instructor users to the first active customer/instructor records when those records exist.
- `backend/app/core/environment.py` is the single backend `.env` loader. It reads only `backend/.env` with `utf-8-sig` for Windows-created env files and resolves the file path from backend source location.

## Access Rules

Customer/contact endpoints now use these server-side rules:

- `manager`: can read and mutate all customers and contacts.
- `customer`: can read only the customer record linked by `current_user.customer_id` and contacts for that customer; cannot mutate customers or contacts.
- `instructor`: cannot mutate customers or contacts. Instructor customer/contact reads are denied for now because the current schema does not yet expose a clear instructor-to-customer relationship.
- Missing or invalid token returns 401.
- Authenticated but unauthorized role/resource returns 403.
- Missing customer/contact records return 404 when the request is otherwise allowed to resolve the resource.

Protected customer/contact reads:

- `GET /customers`
- `GET /customers/{customer_id}`
- `GET /customers/{customer_id}/contacts`

Protected manager-only mutations:

- `POST /customers`
- `PUT /customers/{customer_id}`
- `DELETE /customers/{customer_id}`
- `POST /customers/{customer_id}/contacts`
- `PUT /customer-contacts/{contact_id}`
- `DELETE /customer-contacts/{contact_id}`

## Run

Install backend dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

Configure local environment in `backend/.env`:

```text
DATABASE_URL=postgresql+psycopg://...
APP_ENV=development
AUTH_SECRET_KEY=<strong local secret>
INIT_DB_ENABLED=false
```

To explicitly allow local schema/demo initialization, set:

```text
INIT_DB_ENABLED=true
```

Then run:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```

## Validate

Compile validation:

```powershell
.\.venv\Scripts\python.exe -m compileall backend desktop_client
```

Result: passed.

Manual HTTP/database-backed validation using FastAPI `TestClient` against the configured Supabase PostgreSQL connection:

- `/system/init-db` returned 403 while `INIT_DB_ENABLED=false`.
- `POST /auth/login` returned 200 for manager, instructor, and customer demo users.
- `GET /auth/me` returned 200 with a valid manager bearer token.
- Invalid password returned 401.
- Missing token on customer/contact reads returned 401.
- Invalid token on customer/contact reads returned 401.
- Missing token on customer/contact mutations returned 401.
- Instructor/customer mutation attempts returned 403.
- Customer read of another customer returned 403.
- Customer read of the linked customer record returned 200.
- Customer read of linked customer contacts returned 200.
- Instructor customer list read returned 403.
- Manager created, read, updated, and soft-deleted a customer.
- Manager created, updated, and soft-deleted a contact.

`PyJWT==2.10.1` was installed into the local virtual environment for validation. `httpx` was also installed locally so Starlette/FastAPI `TestClient` could execute the manual API checks.

## Next Task

Task 06 should remain Activities CRUD API. Activity mutations should reuse the same auth helpers, and activity reads should be shaped by role without adding booking, RAG, dashboard, or image upload behavior early.
