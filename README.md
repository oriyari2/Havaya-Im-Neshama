# Experience-with-Soul

Student final project for Windows Systems Engineering.

The project will become the Havaya Im Neshama management system described in
[docs/PRD.md](docs/PRD.md). The current MVP foundation includes the initial
FastAPI and PySide6 skeleton, Supabase-compatible PostgreSQL setup, Hebrew demo
seed data, and a customer/contact CRUD API.

## Project Structure

```text
backend/            FastAPI backend
desktop_client/     PySide6 desktop client
rag/                Future RAG modules
docker/             Future Docker configuration
migrations/         Future database migrations
docs/               Product and project documentation
tasks/              Implementation task files
```

## Setup

Create a Python virtual environment from the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies:

```powershell
pip install -r backend\requirements.txt
```

Install desktop dependencies:

```powershell
pip install -r desktop_client\requirements.txt
```

Copy `.env.example` to `.env` when local configuration is needed. Do not commit
real secrets.

## Run The Backend

```powershell
uvicorn backend.app.main:app --reload
```

Open the health check:

```text
http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## Run The Desktop App

```powershell
python -m desktop_client.app.main
```

## Current Scope

Implemented so far:

- FastAPI health/system endpoints.
- PostgreSQL schema initialization and Hebrew demo seed data.
- Customer and customer-contact CRUD API, including soft delete, active defaults,
  search, and `city` / `customer_type` filters.
- PySide6 login and role-based desktop shell using MVP boundaries.
- Role-aware dashboard, bookings, booking details/history, open events, and
  customer my-bookings screens backed by the FastAPI API.
- Manager booking creation, confirmation, cancellation, and supported field
  edits through the event-sourced command API with optimistic concurrency.
- Manager customer directory and nested contact management with search,
  filters and pagination. Customers use protected physical deletion; linked
  bookings/history/users return 409, while owned contacts cascade.
- Manager textual activity management and an active-only read-only activity
  catalog for instructors/customers, including search, filters, pagination,
  detail, and soft deactivate/reactivate.
- Manager instructor profile management with search/filter/page/detail and
  protected physical deletion, plus an instructor-owned read-only profile.
  Assignment/history/user dependencies return 409.
- Event-sourced instructor assignment/removal embedded in Booking Details and
  role-safe open-event detail for instructors.
- Paged and named booking filters, readable customer/activity projections,
  manager completion, role-operational dashboard drill-down, and synchronized
  role navigation (Task 12F).

Task 12 functional coverage and final acceptance are complete with documented
limitations. Task 13 UI/UX redesign, AI/RAG, and activity image UI remain future
work.
