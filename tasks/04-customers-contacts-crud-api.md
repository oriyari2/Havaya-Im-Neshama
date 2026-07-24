Search must support Hebrew text.

Default behavior:

return active customers unless is_active is explicitly provided

order by customer name or creation date using a simple, predictable order

use a reasonable default limit, for example 50

GET /customers/{customer_id}

Return one customer by ID.

If the customer does not exist, return 404.

Include the customer's contacts either:

directly in the response, or

through the separate /customers/{customer_id}/contacts endpoint.

Choose the simpler option that fits the current codebase.

POST /customers

Create a new customer.

Required field:

name

Optional fields should follow the existing schema:

customer_type
city
address
phone
email
notes
is_active

Validation:

name must not be empty.

email, if provided, should have a basic valid email shape.

is_active should default to true.

Return the created customer.

PUT /customers/{customer_id}

Update an existing customer.

Use the existing schema fields.

Validation:

name must not become empty.

return 404 if the customer does not exist.

Update updated_at.

Return the updated customer.

DELETE /customers/{customer_id}

Do not physically delete customers in this MVP.

Implement this route as a soft delete:

is_active = false

Update updated_at.

Return a clear success response or the updated customer.

If the customer does not exist, return 404.

Customer Contact Behavior

GET /customers/{customer_id}/contacts

Return contacts for a customer.

Default behavior:

return active contacts unless is_active is explicitly provided

return 404 if the customer does not exist

POST /customers/{customer_id}/contacts

Create a contact for an existing customer.

Required field:

full_name

Optional fields should follow the existing schema:

role_title
phone
email
is_primary
notes
is_active

Validation:

customer must exist

full_name must not be empty

email, if provided, should have a basic valid email shape

is_active should default to true

Primary contact behavior:

If a new contact is created with is_primary = true, make other contacts forthe same customer non-primary.

Keep this logic simple and inside one database transaction.

Return the created contact.

PUT /customer-contacts/{contact_id}

Update an existing contact.

Validation:

full_name must not become empty

return 404 if the contact does not exist

Primary contact behavior:

If the contact is updated to is_primary = true, make other contacts for thesame customer non-primary.

Update updated_at.

Return the updated contact.

DELETE /customer-contacts/{contact_id}

Do not physically delete contacts in this MVP.

Implement this route as a soft delete:

is_active = false

If the deleted contact was primary, it is acceptable for the customer to have noprimary contact after deletion in this task.

Update updated_at.

Return a clear success response or the updated contact.

If the contact does not exist, return 404.

Data Models

Use Pydantic request and response models.

Suggested files:

backend/app/models/customer.py

or follow the existing project structure if models are organized differently.

Recommended models:

CustomerCreate
CustomerUpdate
CustomerResponse
CustomerListResponse
CustomerContactCreate
CustomerContactUpdate
CustomerContactResponse

Keep field names aligned with the database schema.

Do not expose raw database rows if the existing codebase already has a responsemodel pattern.

Error Handling

Use normal FastAPI error responses:

400 for invalid input that passes Pydantic but fails business validation

404 for missing customer or contact

500 only for unexpected backend/database failures

Error messages should be clear but should not expose database internals.

Examples:

{ "detail": "Customer not found" }

{ "detail": "Contact not found" }

Database Requirements

Use the existing backend database connection code.

Keep SQL parameterized. Do not build SQL by string-concatenating user input.

Use transactions where more than one write is required, especially when settingone primary contact and clearing the previous primary contact.

Do not modify the existing schema unless absolutely required.

If a small index is clearly useful for search or filtering, add it only throughthe existing schema initialization mechanism and document it.

Out Of Scope

Do not implement in this task:

authentication or RBAC

frontend screens

booking CRUD

activity CRUD

event sourcing

Cloudinary

RAG or AI features

import/export

duplicate warning UI

real customer data

Duplicate detection for phone or email is a PRD requirement, but for this taskit is enough to leave it for a later UI/API validation task unless it is veryeasy to add safely.

Documentation

Create documentation for this task:

docs/piv/04-customers-contacts-crud-api.md

Document:

what routes were added

how to run the backend

example requests for creating a customer and a contact

example request for searching customers in Hebrew

validation performed

what remains out of scope

Validation

After implementation, run:

.\.venv\Scripts\python.exe -m compileall backend desktop_client

If the backend has tests, run the relevant test command.

Manually validate the API using the local FastAPI server or another existingproject method.

Minimum manual checks:

List customers:

GET /customers

Search Hebrew customer data:

GET /customers?search=ירושלים

Create a customer with Hebrew data:

{
  "name": "בית ספר הדגמה",
  "customer_type": "בית ספר",
  "city": "ירושלים",
  "phone": "050-0000099",
  "email": "demo99@example.com",
  "notes": "לקוח בדיקה"
}

Update the customer.

Soft-delete the customer and verify it no longer appears in the defaultactive customer list.

Create a contact for an existing customer:

{
  "full_name": "איש קשר לדוגמה",
  "role_title": "רכז פעילות",
  "phone": "052-0000099",
  "email": "contact99@example.com",
  "is_primary": true,
  "notes": "איש קשר בדיקה"
}

Create another primary contact for the same customer and verify the previouscontact is no longer primary.

Soft-delete a contact.

Acceptance Criteria

Task 04 is complete when:

customer CRUD routes exist and are registered in FastAPI

customer contact CRUD routes exist and are registered in FastAPI

customers and contacts use the existing PostgreSQL database

Hebrew data can be created, returned, updated, and searched

customers and contacts are soft-deleted using is_active = false

primary contact logic works correctly

inputs are validated with Pydantic

missing records return 404

SQL uses parameters, not unsafe string concatenation

documentation exists under docs/piv

compile validation passes

basic manual API validation was performed

