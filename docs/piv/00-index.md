# PIV Documentation Index — Final MVP State

## Purpose

This index is the current entry point for the project PIV artifacts. Historical
PIV notes remain in the repository because they document the Plan → Implement →
Validate decisions made during development. When a historical note describes an
older UI shape or an unfinished later task, the **current implementation and the
final validation documents below are authoritative**.

## Current baseline

The academic MVP currently contains:

- FastAPI application server with explicit router/application/domain/
  infrastructure boundaries;
- Supabase-compatible PostgreSQL persistence;
- authentication, RBAC and manager account administration;
- Customer, Instructor and Activity management;
- Cloudinary activity images behind an application-owned Gateway;
- Booking CQRS and Event Sourcing with immutable events, projection reads,
  replay and optimistic concurrency;
- role-aware Dashboard, Booking, Activity, profile and management workflows;
- PySide6 Desktop MVP organized as feature-first Microfrontends; each business
  package owns its View, Qt-free Presenter, service adapter and registration
  boundary, with shared UI infrastructure under `desktop_client/app/shared/`;
- bounded background execution and process-memory caching for Desktop
  responsiveness;
- local Ollama in Docker, pgvector retrieval, grounded RAG-only consultation,
  citations, abstention and manager knowledge-source management;
- a branded RTL Desktop visual system across Login, Shell, Dashboard,
  Customers, Instructors, Managers, Activities, Bookings, Knowledge and AI
  consultation surfaces.

## PIV artifact map

| Increment | PIV artifact | Final state |
|---|---|---|
| Project and persistence | `01`–`03` | Implemented |
| Customers / auth / activities / Gateway | `04`–`07` | Implemented |
| Booking Event Sourcing / CQRS / dashboard | `08`–`12` | Implemented |
| Ollama / RAG / AI / knowledge management | `13`–`18` | Implemented |
| Activity image Desktop workflow | `19` | Implemented |
| Shared Desktop UX/accessibility foundation | `20` | Implemented |
| Manager user administration | `21` | Implemented |
| Background execution | `22` | Implemented |
| Safe caching / refresh reduction | `23` | Implemented |
| Booking creation and assignment closure | `24`, `24.1`, `24.2`, `24.3` | Implemented |
| Desktop visual/UX redesign | `25.0.1`–`25.5` | Implemented; final state consolidated below |
| Feature-first Desktop Microfrontends | `25.6` | Implemented structurally; run the listed regression validation after applying |
| Dashboard annual Qt Charts trend | `27`, `27-validation.md` | Implemented and validated |
| Final regression and requirements audit | `final-validation.md` | Completed for code-level validation |

## Authoritative final documents

1. `docs/PRD.md` — product baseline and Definition of Done.
2. `docs/piv/requirements-traceability.md` — final course/PRD implementation map.
3. `docs/piv/final-validation.md` — final regression evidence and known
   validation limitations.
4. `ARCHITECTURE.md` — current logical architecture and boundaries.
5. `README.md` — setup/run instructions.

## Task 27 documentation

- `tasks/27-dashboard-yearly-event-trend.md` — specification and acceptance scope.
- `docs/piv/27-dashboard-yearly-event-trend.md` — implementation/PIV record.
- `docs/piv/27-requirements-traceability.md` — Task 27 requirement evidence.
- `docs/manual-testing-task-27.md` — independent manual acceptance guide.
- `docs/piv/27-validation.md` — automated and live-backend validation report.

## Historical-note rule

The task PIV files intentionally preserve the implementation history. Examples
such as an earlier four-column Customer table, earlier dialog dimensions, or a
"next task not started" statement describe the state at that point in time.
They must not be interpreted as the current product contract. Final UI and
validation state is documented in `requirements-traceability.md`,
`final-validation.md`, and the final-state addenda in the Task 25 PIV files.
