# Requirements Traceability — Final MVP Baseline

## Purpose

This document maps the current implementation to the approved PRD and the
academic Windows Systems Engineering project requirements. Historical Task/PIV
files show how the system evolved; this file records the **final code-level
state**.

## Course requirements traceability

| Course requirement | Current implementation evidence | Status |
|---|---|---|
| Choose a domain | Havaya Im Neshama activity/event management system | Implemented |
| User management and authentication | FastAPI auth, bearer sessions, hashed passwords, Manager/Instructor/Customer roles, manager account administration | Implemented |
| Search data | Customer, Instructor, Manager, Activity, Booking and knowledge search/filter flows | Implemented |
| Show details for a result | Dedicated list-to-details screens and Booking/Activity/Profile details | Implemented |
| Present data in a graph **or table** | Role-aware tables throughout Dashboard and management screens; the requirement allows a table, so QtCharts is not required | Implemented |
| AI consultation about the domain | Authenticated `POST /api/ai/consult` and PySide6 AI Advisor | Implemented |
| Domain data entry | Customer, Instructor, Manager, Activity, Booking, assignment and knowledge-source workflows | Implemented |
| Desktop application | PySide6 Desktop client | Implemented |
| MVP presentation pattern | Passive PySide6 Views, Qt-free Presenters, service/API adapters; architecture tests protect the boundary | Implemented |
| Microfrontend/modular UI | Physical feature-first packages under `desktop_client/app/features/<feature>/`; each role-bounded feature owns its registration, View, Presenter and service adapter while reusable UI/validation code lives under `desktop_client/app/shared/`. `MainWindow` composes only through the registry/public factories. See `docs/architecture/desktop-microfrontends.md` and `test_microfrontends.py` | Implemented and architecture-tested |
| PySide version | Repository pins `PySide6==6.9.1` | **Verify course interpretation** if `6.5` was intended as an exact version rather than PySide6/Qt6 guidance |
| FastAPI application server | FastAPI composition root and routers | Implemented |
| CQRS/MVC organization | Booking commands/event writes are separated from projection queries; backend layers separate routers, application, domain and infrastructure | Implemented |
| Cloud data storage | PostgreSQL/Supabase-compatible persistence via configured `DATABASE_URL` | Implemented; live cloud connection must be shown in demo environment |
| Event Sourcing | Booking event store is append-only source of truth with replay, projection and optimistic concurrency | Implemented |
| Gateway for external services | Application-owned `ImageGateway` with `CloudinaryImageGateway` adapter | Implemented |
| Call an external service and receive processing/data | Cloudinary upload/delete returns external image metadata and secure URLs through the Gateway | Implemented for external image service; **grading note:** if the lecturer expects a second domain-data provider distinct from Cloudinary, the current repository does not contain one |
| Ollama in Docker implementing RAG | `docker/docker-compose.yml`, local Ollama HTTP clients, pgvector ingestion/retrieval, grounded generation | Implemented |
| Full PIV process beginning with PRD | `docs/PRD.md` plus task-by-task `docs/piv/` artifacts and final validation | Implemented |
| Git repository | Repository-oriented project structure and Git documentation | Implementation present; final branch/push/clean status must be verified locally |
| Professional/aesthetic UI | Branded RTL visual system, shared design tokens, role-aware heroes, responsive tables/dialogs and accessibility tests | Implemented |

The course explicitly requires search, details, a graph **or table**, AI
consultation and data entry, and requires Desktop/PySide, MVP/Microfrontends,
FastAPI/CQRS, cloud persistence/Event Sourcing, Gateway, external service,
Ollama/Docker/RAG, PIV and Git. The final project uses tables rather than adding
a chart solely for grading.

## Product/PRD traceability

| Area | PRD scope | Final implementation |
|---|---|---|
| Authentication/RBAC | Role-safe login and ownership | Implemented server-side; Desktop navigation is supplementary only |
| Customers | Manager management + Customer-owned profile | Implemented with one current contact-person workflow, lifecycle actions and linked account handling |
| Instructors | Manager management + owned profile + assignment visibility | Implemented |
| Manager users | Account administration | Implemented in Manager-only `מנהלים` module |
| Activities | Catalog, management, suitability/preparation data | Implemented with role-aware active visibility |
| Activity images | External Gateway upload/display | Implemented through Cloudinary Gateway and Desktop gallery |
| Bookings | Create/read/update/status/history | Implemented through CQRS/Event Sourcing |
| Booking history/replay | Immutable chronological history and rebuildable projection | Implemented and tested |
| Instructor assignment | Assign/remove per Booking Activity | Implemented through booking events and projection |
| Dashboard | Role-specific summaries and operational tables | Implemented |
| Customer self-service | Own bookings, catalog and booking request | Implemented |
| Knowledge ingestion | Approved internal knowledge | Implemented for pasted text and UTF-8 `.txt`/`.md` sources |
| Semantic retrieval | Role-filtered approved chunks | Implemented with pgvector cosine search and fail-closed role filtering |
| Grounded AI | RAG-only answer with citations/abstention | Implemented; no web/general-knowledge fallback |
| AI write safety | AI must not mutate operational data | Implemented as read-only consultation |
| Desktop responsiveness | Slow work off Qt event loop | Implemented through bounded operation executor and stale-result suppression |
| Safe local caching | Bounded/role-scoped cache with invalidation | Implemented; no secrets or disk persistence |
| UI/UX | Professional RTL Desktop | Implemented across major role and management surfaces |

## Architecture evidence

### Desktop MVP

```text
View (PySide6, passive)
  -> Presenter (no PySide6 imports)
    -> Service
      -> ApiClient
        -> FastAPI
```

Feature modules are independently composed for Login, Dashboard, Customers,
Instructors, Managers, Activities, Bookings, profiles, Knowledge Management and
AI consultation. `MainWindow` is the composition root and role-aware navigation
boundary.

### Booking CQRS and Event Sourcing

```text
Command endpoint
  -> command handler
    -> BookingAggregate replay + validation
      -> append immutable booking event
        -> update projections in the transaction

Query endpoint
  -> projection/query repository
    -> read-optimized response
```

The booking event stream contains supported domain events for creation, status,
date, price, location, participant count, notes and instructor assignment/
removal. Stale expected versions are rejected.

### Gateway and external service

`ActivityImageService` depends on the application-level `ImageGateway` protocol.
Only infrastructure instantiates `CloudinaryImageGateway`; business code does
not import the Cloudinary SDK directly.

### RAG

```text
approved source
  -> chunk + metadata + embedding
    -> PostgreSQL knowledge_chunks / pgvector

question + authenticated role
  -> query embedding
    -> role-filtered cosine retrieval
      -> strict grounded prompt
        -> Ollama generation
          -> citation validation / abstention
```

Current code defaults:

- generation model: `llama3.1`;
- embedding model: `nomic-embed-text-v2-moe`;
- `RAG_MAX_COSINE_DISTANCE = 0.58`;
- `RAG_RETRIEVAL_TOP_K = 5`;
- generation timeout: 600 seconds;
- generation `num_predict`: 2000;
- Ollama keep-alive: `30m`;
- bounded PostgreSQL connection pool: 1–5 connections.

The backend also exposes a manager-only AI readiness view covering the database
pool, Ollama reachability, installed generation/embedding models and warm model
state. Startup attempts a non-fatal generation-model warm-up.

## Final validation evidence

Final repository test inventory:

- backend: **229 tests / 18 files**;
- Desktop: **251 tests / 26 files**;
- total: **480 tests / 44 files**.

Backend discovery passed 229/229. Every Desktop module is validated successfully;
long mixed PySide6 GUI discovery may terminate natively on Windows, so final GUI
regression uses fresh-process module isolation. See `final-validation.md`.

`python -m compileall backend desktop_client rag` also succeeds on the supplied
source tree (with two non-fatal existing `SyntaxWarning` messages in demo seed
SQL regular-expression string literals).

## Remaining release/demo checks

These are not missing product features, but must be verified before submission:

1. run `git diff --check` and confirm `git status --short` is clean after the
   documentation commit;
2. confirm the final branch is pushed to the submission repository;
3. verify `.env` and real secrets are ignored;
4. verify live Supabase/PostgreSQL, Cloudinary and Ollama readiness on the demo
   machine;
5. use `llama3.1` in the Ollama setup command, matching the code default;
6. capture current native Windows screenshots (offscreen Qt may render Hebrew
   with fallback square glyphs);
7. rehearse the complete manager → instructor → customer → AI scenario;
8. resolve with the lecturer whether `PySide6==6.9.1` is acceptable if the
   assignment's `6/6.5` wording is intended as a strict version requirement;
9. if required by the lecturer, add a second domain-specific external service;
   currently Cloudinary is the external service isolated by the required
   Gateway.

## Final status

The codebase is functionally complete for the documented academic MVP and has
strong evidence for authentication, Desktop MVP, CQRS/Event Sourcing, Gateway,
cloud persistence integration, Docker/Ollama RAG and professional role-aware
UI. The remaining items above are submission-environment or grading-
interpretation checks and should not be hidden by the documentation.
