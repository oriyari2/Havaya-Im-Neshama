AGENTS.md

Project Identity

This project is a student final project for Windows Systems Engineering.

Product:Havaya Im Neshama Management System

Primary goal:Build an academic MVP that satisfies the PRD and clearly demonstrates the required course architecture patterns.

The PRD is the source of truth.

Always follow:

PRD_Havaya_Im_Neshama.md

docs/piv/requirements-traceability.md, if it exists

the current task file under tasks/

Work task by task.Do not implement future tasks unless explicitly requested.

Required Course/PRD Architecture

The project must visibly demonstrate:

FastAPI backend

PySide6 desktop client

MVP pattern in the desktop client

Modular desktop UI boundaries

Supabase-compatible PostgreSQL persistence

Authentication and role-based authorization

CQRS for booking commands and queries

Event Sourcing for booking changes

Gateway pattern for external image service integration

Docker-based Ollama service for local RAG

RAG assistant grounded only in approved internal knowledge

PIV documentation for each implemented task

Tech Stack

Backend: FastAPI

Desktop client: PySide6

Database: PostgreSQL / Supabase-compatible SQL

AI/RAG: Ollama in Docker with a simple local RAG module

Architecture: MVP, MVC where useful, CQRS, Event Sourcing, Gateway

Backend Structure Rules

Keep backend code organized by responsibility.

Preferred structure:

backend/app/api or backend/app/routers

FastAPI routers and HTTP-level logic only

backend/app/schemas or backend/app/models

Pydantic request/response models

backend/app/application

services, use cases, commands, queries

backend/app/domain

domain rules, booking aggregate, event definitions

backend/app/infrastructure

database access, repositories, external gateways

Routers should stay thin.

Do not put large SQL blocks, repeated business logic, or domain rules directly inside routers.If logic starts repeating, extract it into a service or repository.

Database connection code belongs only in the DB/infrastructure module.

Use parameterized SQL.Do not build SQL using unsafe string interpolation.Whitelisted sort fields are allowed.

Desktop Client Rules

The desktop client must use PySide6.

Use MVP pattern:

View: PySide6 widgets and UI only

Presenter: UI behavior and orchestration

Model/API client: data access through backend API

The desktop client must never connect directly to PostgreSQL or Supabase.All data must go through the FastAPI backend.

The UI should support Hebrew and RTL where relevant.

Event Sourcing and CQRS Rules

Booking changes must be event-sourced.

Supported booking mutations should append immutable domain events.Do not overwrite booking history.

Booking read screens should use projections/queries.Booking commands should be separated from booking queries.

Booking state must be reconstructable by replaying events.

Use optimistic concurrency for booking commands when implemented.

Authentication and Authorization Rules

Server-side authorization is mandatory.Hiding a button in the desktop client is not enough.

Required roles:

manager

instructor

customer

Access is denied by default and granted by role.

Customers must not access other customers' bookings.Instructors must not edit commercial/customer fields.

Passwords must never be stored in plaintext.

RAG and AI Rules

The AI assistant is read-only in the MVP.It must not mutate customers, bookings, prices, assignments, or operational data.

Answers must be grounded in approved internal knowledge.When possible, return or identify the supporting source.

If the answer is not found in the approved knowledge, say that the information is unavailable.

Gateway Rules

External image service access must go through a Gateway abstraction.

Business logic must not directly import Cloudinary or another image provider SDK.

Task Discipline

Work only on the current task.

Do not implement:

authentication

activities

bookings

dashboard

RAG

image upload

desktop screens

unless the current task explicitly asks for them.

Keep changes small and readable.Prefer simple, clear code over clever abstractions.

Documentation Rules

After each task, update or create PIV documentation under:

docs/piv/

Each PIV document should explain:

what was created

which PRD requirements it supports

what files changed

how to run it

how it was validated

what the next task should be

Also keep requirement traceability updated when a requirement becomes implemented.

Validation Rules

After backend or desktop changes, run:

.\.venv\Scripts\python.exe -m compileall backend desktop_client

When possible, validate database-backed behavior against the configured PostgreSQL/Supabase connection.

Do not commit secrets.Do not commit .env files.

After Each Task

Explain:

what was created

how to run it

what files were changed

what was validated

which PRD requirements were advanced

what the next task should be