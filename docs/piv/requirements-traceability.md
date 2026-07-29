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

FR-CUS-01, FR-CUS-02, FR-CUS-03

Task 12 Milestone 12B implemented

Manager customer/contact management and customer-owned read-only profile are
implemented through `CustomerService`, role-specific presenters, and passive
PySide6 views. Contacts remain nested in Customer Details. Manager customer
Delete is physical only for profiles without booking/event/user dependencies;
protected references return 409 and owned contacts alone cascade.

Authentication and RBAC

FR-AUTH-01, FR-AUTH-02

Backend implemented and hardened

Task 05 adds login, current-user retrieval, hashed demo users, PyJWT bearer tokens, environment-backed AUTH_SECRET_KEY configuration, reusable auth helpers, manager-only customer/contact mutations, authenticated customer/contact reads, customer-owned customer/contact reads, instructor read denial until a clear relationship exists, and local-only guarded /system/init-db. Task 09 implements booking ownership and Task 10 implements role-based desktop navigation and authenticated API sessions for `FR-AUTH-03` and `FR-AUTH-04`.

Activity catalog

FR-ACT-01, FR-ACT-02, FR-ACT-04

Backend and Task 12 desktop workflows implemented

Task 06 adds authenticated activity list/search/detail/create/update/soft-delete API, additive PostgreSQL persistence fields for target audience, duration, recommended capacity, pricing rule, required equipment, preparation notes, season, and tags, manager-only mutations, active-only instructor/customer reads, Hebrew search validation, and PIV documentation. Task 12 Milestone 12C adds manager textual management and the active-only instructor/customer desktop catalog with search, filters, pagination, details, and role-safe controls.

Activity image Gateway

FR-ACT-03, Gateway course requirement

Backend API implemented

Task 07 adds activity image persistence, manager-only upload/delete endpoints, customer/instructor read visibility for active activities, activity response image URLs, and a Cloudinary adapter behind an application-owned Gateway abstraction. Desktop image UI remains not started.

Booking Event Sourcing

FR-BKG-01 to FR-BKG-06

Backend core and manager desktop command workflows implemented

Task 08 adds booking-only Event Sourcing and CQRS core: `booking_events` append-only event store, `bookings` projection, `booking_instructors` activity-scoped current-assignment projection keyed by `booking_activity_id` and `instructor_id`, booking aggregate replay, manager command handlers, projection-based query handlers, optimistic concurrency, chronological history API, and replay API. Implemented events are `BookingCreated`, `BookingStatusChanged`, `BookingDateChanged`, `BookingPriceChanged`, `BookingLocationChanged`, `BookingParticipantCountChanged`, `BookingNotesUpdated`, `BookingInstructorAssigned`, and `BookingInstructorRemoved`. Dashboard/open-event queries are deferred to Task 09. Activity images and activities are not event-sourced.

Task 11 connects the desktop manager workflow to creation, status, schedule,
price, location, participant-count, and notes command endpoints. Each update
sends the current projection version and refreshes the query views afterward.

Instructor management

FR-INS-01 to FR-INS-04

Instructor CRUD/profile, assigned/open booking backend, and role UI implemented

Task 12D implements `FR-INS-01` manager instructor profile CRUD and the
instructor-owned read-only profile. Manager Delete is physical only when no
user, active/removed assignment, or immutable event references the profile;
protected references return 409. `FR-INS-02` and `FR-INS-03` are visible in
Task 10. Task 08 implements assignment/removal commands for `FR-INS-04`; its
manager desktop assignment UI and focused role-safe read models are implemented
in Task 12 Milestone 12E using the existing event-sourced commands.
Task 12 Milestone 12F adds paged/filtered role-scoped desktop booking lists,
readable projection names, manager completion through the existing status
event, operational dashboard drill-down, local Open Events search, and
role-synchronized navigation without weakening server authorization.

Dashboard

FR-DASH-01 to FR-DASH-03

Backend API and Task 10 desktop presentation implemented

Task 09 adds role-aware upcoming status and assignment counts, assigned-booking
views, eligible instructor open events, and customer-owned compact booking
summaries. Task 10 presents these through role-specific PySide6 dashboard,
booking, open-event, detail, and my-bookings screens.

RAG AI assistant

FR-AI-01 to FR-AI-06

Infrastructure started

Task 13 adds local Ollama connection infrastructure: `OLLAMA_URL` configuration
defaulting to `http://localhost:11434`, an importable `rag` package, an
application-facing `LLMClient` interface, and an `OllamaLLMClient` that posts
non-streaming generation requests to `/api/generate`. Retrieval, role-filtered
knowledge access, citations, API endpoints, and desktop UI remain future tasks.
Task 14 adds authenticated `POST /api/ai/consult`, injects the `LLMClient`
through an AI consultation service, and adds a PySide6 MVP chat screen available
from manager, instructor, and customer navigation. The assistant remains
read-only and currently answers from the base model only; approved-knowledge
retrieval, role-filtered citations, and abstention behavior remain future work.
Task 15 adds the approved-knowledge ingestion foundation for `FR-AI-07`: a
PostgreSQL `knowledge_chunks` table using pgvector, an Ollama embedding client,
a manager-only `POST /api/rag/knowledge` endpoint, chunking and hashing in an
application service, and repository-layer persistence tests. Retrieval,
role-filtered similarity search, citations, and insufficient-context abstention
remain future work.
Task 16 implements standalone role-aware semantic retrieval for `FR-AI-02`,
`FR-AI-05`, and `FR-AI-07`: authenticated `POST /api/rag/search` embeds the
query with the existing Ollama embedding client, searches `knowledge_chunks`
with pgvector cosine distance, filters by embedding model/dimensions and
authenticated role inside the repository SQL, excludes weak matches using the
code-level cosine-distance threshold constant in
`backend/app/core/environment.py`, and returns ordered approved chunks without
exposing embeddings. The request schema rejects unexpected authorization fields,
and temporary Task 16 live-validation rows must be cleaned up after validation.
Focused Task 16 tests passed at 14 tests and the full backend suite passed at
141 tests. Hebrew unrelated-query validation showed very low cosine distances
for unrelated text, so Task 16 is completed retrieval infrastructure rather than
proof of reliable Hebrew semantic retrieval. A controlled diagnostic verified
that the two Hebrew paraphrase queries produce different outgoing request text
and different vectors through both `OllamaEmbeddingClient` and direct
`POST /api/embed`; the earlier identical-vector observation is classified as a
validation-script/input-encoding defect. Retrieved context is not yet integrated
into the AI consultation prompt, so AI citations and abstention during answer
generation remain future work. Next recommended task: Task 16.1, investigate and
validate Hebrew embedding quality. Task 17 remains blocked until Hebrew
retrieval quality is understood or corrected, or an evidence-based mitigation is
selected.

Required course/PRD concept

Docker/Ollama

Docker, AI service

Ollama client configuration implemented

Docker setup and model download were handled manually outside this task. Task
13 connects backend Python infrastructure to the expected local Ollama service
at `http://localhost:11434`.

PySide6 desktop MVP

Desktop GUI, MVP pattern, modular UI

Booking/dashboard read and manager command slices implemented

Task 10 adds FastAPI-backed sign-in, Hebrew RTL role navigation, passive views,
UI-independent presenters, dashboard summaries, assigned/my booking lists,
booking details, manager history, eligible open events, and standard loading,
empty, and error states. Task 11 adds manager-only create, confirm, cancel, and
supported field-edit workflows while keeping instructor/customer views
read-only. Customer/activity management and instructor assignment UI remain
future desktop work.

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

FR-ACT-01 is implemented at API level. FR-ACT-02 is implemented at API/persistence level for textual catalog data. FR-ACT-04 is implemented for backend authorization. FR-ACT-03 is implemented by Task 07 at backend/Gateway/API level; desktop media mutation remains deferred.

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

FR-ACT-02 is implemented for textual catalog data plus activity image URL exposure at API level. FR-ACT-03 is implemented at backend/Gateway/API level. FR-ACT-04 includes read-only image visibility for customers and instructors on active activities. Desktop image mutation/display is explicitly deferred to a later media task.

Task 08 - Booking Event Sourcing and CQRS Core

This is the most important architecture task for the grade.

Required by FR-BKG-01 to FR-BKG-06.

Status: Implemented at backend core/API level for booking creation, supported updates, booking-activity instructor assignment/removal, history, replay, projection reads, optimistic concurrency, and role-aware booking read authorization. Managers can see all bookings, customers see only their own bookings, and instructors see only bookings where they are an active assignment.

Task 09 - Dashboard and Booking Queries

Required by FR-DASH-01 to FR-DASH-03 and FR-BKG-07.

Status: Implemented at backend/API level for filtered booking lists, dashboard
summaries at `GET /bookings/dashboard`, eligible instructor open-event queries at
`GET /bookings/open-events`, and customer-owned compact summaries at
`GET /bookings/my-bookings`. The dashboard exposes upcoming status counts plus
mutually exclusive `assigned_count` and `unassigned_count` booking counts.
Instructor list/detail responses exclude customer ID, agreed price, and notes;
open-event responses additionally omit participant count.

Implement:

Booking aggregate.

Booking command handlers.

Append-only booking_events.

Rebuildable bookings projection.

Versioning and optimistic concurrency.

Replay function.

Tests proving replay reconstructs projection.

Assign/remove instructor for a booking activity through booking events.

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

Task 10 - Desktop Booking and Dashboard UI

Status: Implemented.

Implement:

FastAPI-backed login and bearer-token session.

Role-based shell/navigation.

Dashboard, bookings, details/history, open events, and my-bookings packages
using MVP boundaries.

Role-safe booking presentation plus loading, empty, and error states.

Validation:

Desktop starts on Windows.

Hebrew RTL layout is readable.

All operational data flows through FastAPI, not direct database access.

Task 11 - Desktop Booking Command Workflows

Status: Implemented.

Implemented:

- Manager booking creation using active customer/activity selectors.
- Confirm, cancel with confirmation, and supported granular field edits.
- Optimistic version propagation, duplicate-submit prevention, projection
  refresh, and command error states.

Deferred after Task 11: instructor assignment UI and customer/activity
management. Customer management is now implemented in Task 12B and activity
management/catalog in Task 12C.

Task 12 - Complete Desktop Functional Management Coverage

Status: Complete with documented limitations.

Implemented across Milestones 12A-12G:

- customer/contact, activity, and instructor profile management
- role-scoped catalogs, profiles, booking lists, dashboards, and Open Events
- event-sourced booking create/edit/status and instructor assignment/removal
- named filters, sorting where supported, real offset pagination, retry/error
  states, authorization-safe navigation, and final OpenAPI coverage
- final hardening: SQL removed from system routers, raw history made
  manager-only, customer directory made manager-only, and both terminal booking
  statuses made immutable for operational commands
- post-closure product correction: customer/instructor desktop lifecycle
  controls use protected physical Delete (204) with dependency conflicts (409);
  activity soft-deactivation remains unchanged

Evidence: `tasks/12-desktop-functional-management-coverage.md`,
`docs/piv/12-desktop-functional-management-coverage.md`, and
`docs/manual-testing-task-12.md`.

Task 13 - Ollama RAG Infrastructure

Status: Implemented for Python backend infrastructure.

Implemented:

- `OLLAMA_URL` configuration in backend environment loading and env examples.
- `rag.LLMClient` abstraction for future RAG orchestration.
- `rag.OllamaLLMClient` using `httpx` against local `/api/generate`.
- Optional context injection for future approved-knowledge snippets.
- Focused mocked HTTP tests and PIV documentation.

Deferred:

- Retrieval, embeddings, approved knowledge ingestion, citations, FastAPI AI
  endpoints, and desktop AI screens.

Later tasks

- Activity media/Cloudinary desktop mutations through the existing Gateway.
- Read-only AI/RAG with Ollama and approved grounded knowledge.
- Final submission/demo packaging after the remaining product tasks.

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

