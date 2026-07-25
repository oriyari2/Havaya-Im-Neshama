Requirements Traceability and Next Tasks

Purpose

This file maps the PRD requirements to implementation tasks so the project stays aligned with the academic MVP requirements.

The goal is not to add features randomly. Each development task should clearly answer:

Which PRD requirement does this satisfy?

Which files or modules implement it?

How can it be validated?

What evidence can be shown in the final project submission?

Current Status

Area

PRD requirements

Current status

Notes

Project skeleton

Architecture, Git workflow, PIV artifacts

Started

Task 01 exists

Supabase PostgreSQL

Cloud database, schema, persistence

Started / partly implemented

Task 02 and DB schema exist

Hebrew demo data

Seed data, no private real data

Implemented

Task 03 completed

Customer API

FR-CUS-01, FR-CUS-02, FR-CUS-03

Backend API implemented

Task 04 completed at API level

Customer UI

FR-CUS-01

Not started

Required for end-to-end demo

Authentication and RBAC

FR-AUTH-01, FR-AUTH-02

Backend implemented and hardened

Task 05 adds login, current-user retrieval, hashed demo users, PyJWT bearer tokens, environment-backed AUTH_SECRET_KEY configuration, reusable auth helpers, manager-only customer/contact mutations, authenticated customer/contact reads, customer-owned customer/contact reads, instructor read denial until a clear relationship exists, and local-only guarded /system/init-db. FR-AUTH-03 and booking-specific FR-AUTH-04 remain for desktop and booking ownership tasks.

Activity catalog

FR-ACT-01, FR-ACT-02, FR-ACT-04

Backend API implemented

Task 06 adds authenticated activity list/search/detail/create/update/soft-delete API, additive PostgreSQL persistence fields for target audience, duration, recommended capacity, pricing rule, required equipment, preparation notes, season, and tags, manager-only mutations, active-only instructor/customer reads, Hebrew search validation, and PIV documentation. Desktop activity UI remains not started.

Activity image Gateway

FR-ACT-03, Gateway course requirement

Backend API implemented

Task 07 adds activity image persistence, manager-only upload/delete endpoints, customer/instructor read visibility for active activities, activity response image URLs, and a Cloudinary adapter behind an application-owned Gateway abstraction. Desktop image UI remains not started.

Booking Event Sourcing

FR-BKG-01 to FR-BKG-06

Not started

Critical course requirement

Instructor management

FR-INS-01 to FR-INS-04

Seed data only

Needs API/UI and booking integration

Dashboard

FR-DASH-01 to FR-DASH-03

Not started

Required for role-specific demo

RAG AI assistant

FR-AI-01 to FR-AI-06

Not started

Required course/PRD concept

Docker/Ollama

Docker, AI service

Not started

Needed for AI demo

PySide6 desktop MVP

Desktop GUI, MVP pattern, modular UI

Skeleton only

Must be visible in final demo

Recommended Task Order From Now

Task 05 - Backend Structure Alignment

Status: Implemented as a small structure cleanup after Task 04.

Before adding more modules, align the backend structure with the PRD architecture:

backend/app/schemas for Pydantic request/response models.

backend/app/api/v1/routers for FastAPI routers.

backend/app/application for services, commands, and queries.

backend/app/infrastructure/repositories for DB access.

backend/app/domain for domain rules and booking aggregate later.

Do not rewrite everything if the current code works. Make a small, practical cleanup so future modules do not become messy.

Validation:

Existing customer/contact API behavior still works.

compileall passes.

Documentation notes the chosen structure.

Task 05 - Authentication and RBAC

Status: Implemented and hardened.

Implemented:

Users table.

Hashed demo users for manager, instructor, and customer.

POST /auth/login.

GET /auth/me.

Reusable current-user and require-role helpers.

Manager-only customer/contact mutation routes.

Authenticated customer/contact read routes.

Resource-aware customer read rules for manager and customer roles.

Local/development/test-only `/system/init-db`, additionally gated by `INIT_DB_ENABLED=true`.

Validation:

compileall passes.

HTTP/database-backed manual checks passed for login, current-user behavior, invalid password 401, missing/invalid token 401 on customer/contact reads, non-manager mutation 403, customer cross-resource read 403, customer own-resource read 200, manager customer/contact read and mutation access, and disabled `/system/init-db` 403.

Task 06 - Activities CRUD API

Status: Implemented at backend API level.

This should come before role-specific UI and before booking/customer ownership behavior.

Required by FR-ACT-01 and FR-ACT-02.

Implemented:

Create/list/search/detail/update/deactivate activities.

Include equipment and preparation notes.

Keep image upload out of this task unless the Gateway is already ready.

Validation:

Hebrew activity data can be searched.

Activity catalog can be read by non-manager roles where permitted.

Mutations are restricted by role after RBAC exists.

FR-ACT-01 is implemented at API level. FR-ACT-02 is implemented at API/persistence level for textual catalog data. FR-ACT-04 is implemented for backend authorization. FR-ACT-03 remains not started until Task 07.

Task 07 - Cloudinary Gateway and Activity Images

Required by FR-ACT-03 and the course Gateway requirement.

Status: Implemented at backend/Gateway/API level.

Implemented:

Gateway interface for activity image upload.

Cloudinary implementation behind the Gateway.

API endpoints for upload, list, and delete.

Store external asset metadata in activity_images.

Activity list/detail image metadata for display.

Safe controlled errors when upload/delete fails.

Validation:

Business logic does not import Cloudinary directly.

Image upload returns asset_id and secure_url.

Activity details can display the saved image URL.

FR-ACT-02 is now implemented for textual catalog data plus activity image URL exposure at API level. FR-ACT-03 is implemented at backend/Gateway/API level. FR-ACT-04 includes read-only image visibility for customers and instructors on active activities. Activity image UI remains not started until the desktop activity screen task.

Task 08 - Booking Event Sourcing and CQRS Core

This is the most important architecture task for the grade.

Required by FR-BKG-01 to FR-BKG-06.

Implement:

Booking aggregate.

Booking command handlers.

Append-only booking_events.

Rebuildable bookings projection.

Versioning and optimistic concurrency.

Replay function.

Tests proving replay reconstructs projection.

Validation:

Creating a booking appends BookingCreated.

Each supported update appends the correct event.

Projection matches replayed state.

Stale expected version is rejected.

Application API does not update/delete event rows.

Task 09 - Booking Queries, History, Instructor Assignment, Dashboard API

Required by booking, instructor, and dashboard requirements.

Implement:

Booking list filters.

Booking details.

Booking history.

Assign/remove instructor through booking events.

Open events requiring instructor.

Dashboard summary counts.

Validation:

Manager sees all relevant data.

Instructor sees assigned and eligible open events only.

Customer ownership rules work after auth is connected.

Task 10 - PySide6 Desktop Shell and Customers Screen

Start UI only after backend basics exist.

Implement:

Login screen or simplified sign-in.

Role-based shell/navigation.

Customers feature package using MVP pattern.

Customer table, search, create/edit/deactivate form.

Validation:

Desktop starts on Windows.

Hebrew RTL layout is readable.

Customer CRUD works through API, not direct DB access.

Task 11 - Activities and Bookings Screens

Implement:

Activity catalog screen.

Booking list screen.

Booking details screen.

Event history display.

Instructor assignment UI.

Validation:

Manager can complete the main scenario from the PRD.

Booking history is visible and chronological.

Task 12 - RAG AI Assistant With Ollama and Docker

Required by AI/RAG and Docker requirements.

Implement:

Docker setup for Ollama.

Knowledge documents/chunks.

Simple ingestion flow.

Retrieval with source references.

Read-only AI chat endpoint.

Role-aware retrieval.

Desktop AI screen.

Validation:

Assistant answers from approved knowledge.

Sources are shown.

When context is missing, assistant says information is unavailable.

AI cannot mutate operational data.

Task 13 - Final Validation and Demo Documentation

Prepare submission evidence.

Include:

Setup instructions.

Demo users and passwords or safe local demo credentials.

Final demo scenario.

Screenshots if useful.

Known limitations.

Requirement traceability table.

Test results.

Validation:

Clean run from setup instructions.

End-to-end demo passes.

No real secrets committed.

Grade-Focused Priorities

Highest priority:

Event Sourcing + CQRS for bookings.

PySide6 desktop with MVP pattern.

Authentication and role-based authorization.

Supabase PostgreSQL persistence.

Gateway for external image service.

Docker/Ollama RAG assistant with source-grounded answers.

PIV documentation for every increment.

Lower priority:

Advanced inventory management.

WhatsApp/email/calendar integrations.

Complex reporting.

Production deployment features.

Rule For Future Tasks

Every new task should include:

PRD requirement IDs.

Scope.

Out of scope.

Backend/frontend files expected.

Validation commands.

Manual acceptance checks.

PIV documentation update.

