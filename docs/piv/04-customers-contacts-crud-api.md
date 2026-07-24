# Task 04 - Customers And Contacts CRUD API

## Plan

Implement the customer and customer-contact CRUD API for the existing PostgreSQL
schema. This satisfies the customer-management API slice of FR-CUS-01 through
FR-CUS-03 while keeping authentication, RBAC, frontend screens, bookings,
activities, Cloudinary, and RAG out of scope for this task.

## Implement

Added routes:

- `GET /customers`
- `GET /customers/{customer_id}`
- `POST /customers`
- `PUT /customers/{customer_id}`
- `DELETE /customers/{customer_id}`
- `GET /customers/{customer_id}/contacts`
- `POST /customers/{customer_id}/contacts`
- `PUT /customer-contacts/{contact_id}`
- `DELETE /customer-contacts/{contact_id}`

Changed files:

- `backend/app/main.py` registers the customer router.
- `backend/app/schemas/customer.py` defines Pydantic request and response models.
- `backend/app/routers/customers.py` defines the API routes and HTTP error
  mapping.
- `backend/app/application/services/customer_service.py` owns customer/contact
  workflow and transaction logic.
- `backend/app/infrastructure/repositories/customer_repository.py` owns
  customer/contact SQL.
- `docs/piv/04-customers-contacts-crud-api.md` documents this PIV step.

Design decisions:

- Customers and contacts are soft-deleted by setting `is_active = false`.
- `GET /customers` returns active customers by default unless `is_active` is
  explicitly supplied.
- `GET /customers` supports optional `city` and `customer_type` query filters.
- `GET /customers/{customer_id}/contacts` returns active contacts by default
  unless `is_active` is explicitly supplied.
- Customer detail responses include active contacts directly.
- Search supports Hebrew text through PostgreSQL `ILIKE` over parameterized
  search values across name, phone, email, city, customer type, and notes.
- Ordering is limited to a whitelist: `name` or `created_at`.
- Creating or updating a primary contact clears other primary contacts for the
  same customer in the same database transaction.

## How To Run

Install dependencies and configure `backend/.env` with `DATABASE_URL`, then run:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```

If the database schema has not been initialized yet:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/system/init-db
```

## Example Requests

Create a customer:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/customers `
  -ContentType "application/json; charset=utf-8" `
  -Body '{
    "name": "בית ספר הדגמה",
    "customer_type": "בית ספר",
    "city": "ירושלים",
    "phone": "050-0000099",
    "email": "demo99@example.com",
    "notes": "לקוח בדיקה"
  }'
```

Search customers in Hebrew:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/customers?search=ירושלים
```

Filter customers by city and type:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/customers?city=ירושלים&customer_type=בית%20ספר"
```

Create a contact:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/customers/{customer_id}/contacts `
  -ContentType "application/json; charset=utf-8" `
  -Body '{
    "full_name": "איש קשר לדוגמה",
    "role_title": "רכז פעילות",
    "phone": "052-0000099",
    "email": "contact99@example.com",
    "is_primary": true,
    "notes": "איש קשר בדיקה"
  }'
```

## Validation

Validation implemented:

- Customer `name` must not be empty.
- Contact `full_name` must not be empty.
- Optional email values must have a basic email shape.
- Missing customers return `404` with `Customer not found`.
- Missing contacts return `404` with `Contact not found`.
- SQL values are passed as parameters.

Validation performed:

- `.\.venv\Scripts\python.exe -m compileall backend desktop_client`
- Manual database-backed route validation using the configured PostgreSQL
  connection:
  - created a Hebrew customer
  - searched customers by Hebrew city
  - verified `city` and `customer_type` filters
  - updated the customer
  - created two primary contacts and verified only the latest remained primary
  - soft-deleted a contact
  - soft-deleted the customer and verified default active search excluded it

## Out Of Scope

- Authentication and RBAC.
- Frontend screens.
- Booking, activity, event sourcing, Cloudinary, and RAG behavior.
- Duplicate warning UI or advanced duplicate detection.
- Import/export and real customer data.
