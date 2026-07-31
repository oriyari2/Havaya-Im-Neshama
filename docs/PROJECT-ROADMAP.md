# Experience-with-Soul: Authoritative Project Roadmap

## 1. Authority and planning baseline

This document is the authoritative execution-order baseline after the final
closure of Task 21. It is subordinate only to `docs/PRD.md` and `AGENTS.md` and
supersedes future-task numbers or sequencing suggestions preserved in historical
Task/PIV records. Historical descriptions of completed work remain evidence;
they are not current scheduling authority.

Tasks 01–21 are complete, committed, and pushed. The current baseline includes
FastAPI, PySide6 MVP, PostgreSQL/Supabase persistence, authentication and RBAC,
manager user administration, booking CQRS/Event Sourcing, the Cloudinary image
Gateway, desktop operational workflows, and an already functional grounded RAG
capability. The project is not complete or release-ready.

The approved priority is now:

```text
Phase 1 — completed foundations
  -> Phase 2 — performance and responsiveness
  -> Phase 3 — Desktop visual design, UI consistency, and UX
  -> Phase 4 — remaining AI/RAG/Ollama work
  -> Phase 5 — stabilization, verification, and release preparation
```

No Phase 3 visual redesign starts before the Phase 2 performance acceptance
gate. No remaining AI expansion starts before both foundations are verified.

## 2. Status tracking

Allowed lifecycle states are `Planned`, `Audit complete`, `Design proposed`,
`Awaiting product-owner input`, `Design approved`, `In implementation`,
`Audit required`, `Fixes required`, `Approved`, and `Committed and pushed`.
The roadmap is updated after design approval and again after implementation,
audit, commit, and push.

| Task | Phase | Title | Status | Design | Implementation | Audit | Commit/push |
|---|---:|---|---|---|---|---|---|
| 01–21 | 1 | Core/backend/desktop/CQRS/Event Sourcing/User Administration baseline | Committed and pushed | Complete | Complete | Approved | Complete |
| 22 | 2 | Desktop Background Execution and Non-Blocking UI | Complete | Approved | Complete | Complete | Complete |
| 23 | 2 | API Performance, Refresh Reduction, and Safe Local Caching | Committed and pushed | Approved | Complete | Complete | Complete |
| 24 | 2 | End-to-End Booking Request and Creation Workflow | Committed and pushed | Approved | Complete | Complete | Complete |
| 24.1 | 2 | Remaining Functional Integration and Product-Completeness Audit | Committed and pushed | Approved | Complete | Complete | Complete |
| 25 | 3 | Desktop Visual Design System and UI/UX Cohesion | Planned | Not started | Not started | Not started | Not started |
| 26 | 3 | Shell, Login, Navigation, and Dashboard Experience | Planned | Not started | Not started | Not started | Not started |
| 27 | 3 | Manager Operational Screens UI/UX Completion | Planned | Not started | Not started | Not started | Not started |
| 28 | 3 | Instructor, Customer, and AI-Surface Visual Consistency | Planned | Not started | Not started | Not started | Not started |
| 29 | 4 | Ollama and RAG Runtime Readiness | Planned | Not started | Not started | Not started | Not started |
| 30 | 4 | AI/RAG, Semantic Search, and Professional AI Experience Completion | Planned | Not started | Not started | Not started | Not started |
| 31 | 5 | End-to-End Stabilization and Performance Verification | Planned | Not started | Not started | Not started | Not started |
| 32 | 5 | Windows Packaging, Submission Documentation, and Demo Materials | Planned | Not started | Not started | Not started | Not started |
| 33 | 5 | Final Architecture, Security, Product, UX, and Release Audit | Planned | Not started | Not started | Not started | Not started |

## 3. Phase definitions

### Phase 1 — Completed foundations (Tasks 01–21)

Completed scope:

- core architecture and repository foundation;
- FastAPI/backend/application/infrastructure boundaries;
- PySide6 desktop composition with passive Views and Qt-free Presenters;
- PostgreSQL/Supabase-compatible persistence and demo data;
- authentication, role authorization, and Manager user administration;
- Customer, Instructor, Activity, image, Booking, Dashboard, and role workflows;
- booking CQRS, immutable events, replay, projections, and optimistic concurrency;
- Gateway-isolated Cloudinary integration;
- implemented Ollama/RAG ingestion, retrieval, grounding, citations, desktop
  chat, and manager knowledge management;
- neutral Task 20 tokens, `PageScaffold`, request-state, accessibility, dialog,
  table, and RTL foundations.

Phase 1 is closed. Future work must preserve these boundaries and contracts.

### Phase 2 — Performance and responsiveness (Tasks 22–24)

Priority outcomes:

- long-running desktop operations do not freeze the Qt event loop;
- background workers have session/module/request identity and safe cancellation;
- screen loading and API interaction are measurably faster;
- unnecessary detail/list/dashboard refreshes are removed;
- bounded caching is used only where freshness, invalidation, authorization,
  and memory limits are explicit;
- API/query performance, reliability, idempotency, logging, and diagnostics are
  verified without weakening Event Sourcing, CQRS, or authorization.

Phase 2 exit gate: defined latency/responsiveness scenarios pass, obsolete
results never overwrite current state, caches are bounded and cleared safely,
and full regression passes.

### Phase 3 — Desktop visual design, consistency, and UX (Tasks 25–28)

Priority outcomes:

- one coherent professional desktop visual language;
- application-wide use of approved tokens and shared components;
- consistent page hierarchy, spacing, typography, controls, dialogs, feedback,
  tables, filters, details panels, focus, and accessibility;
- responsive layouts across supported Windows sizes;
- improved shell, dashboard, manager, Instructor, Customer, and AI-surface UX;
- professional look and feel without changing domain behavior.

Phase 3 is primarily desktop View work. Backend changes are prohibited unless a
real blocking contract defect is documented and separately approved. Branding
assets may be incorporated only when supplied or explicitly approved.

Phase 3 exit gate: all included screens use the shared design language, remain
keyboard/RTL accessible, preserve MVP, and pass desktop regression plus manual
Windows review.

### Phase 4 — Remaining AI/RAG/Ollama work (Tasks 29–30)

Existing AI functionality is retained but no new AI priority displaces Phase 2
or Phase 3. Remaining work includes:

- Docker/Ollama/model health and readiness;
- graceful unavailable/recovery behavior;
- performance-aware ingestion, retrieval, and generation;
- semantic-search quality and live-corpus verification;
- professional AI consultation and knowledge-management interaction;
- source/citation clarity, cancellation, retry, reset, and role-safe grounding;
- any remaining approved AI-assisted feature, always read-only for operational
  data in the MVP.

Phase 4 exit gate: grounded answers, abstention, citations, role filtering,
runtime readiness, semantic-search quality, and failure recovery pass live tests.

### Phase 5 — Stabilization and release preparation (Tasks 31–33)

Priority outcomes:

- feature freeze and full end-to-end acceptance;
- performance verification and complete regression testing;
- Windows packaging and clean-environment startup;
- approved demo data, screenshots, rehearsal, documentation, and PIV evidence;
- final architecture, security, product, UX, external-service, and submission
  audit.

Task 33 is the final release gate. It must not implement features.

## 4. Remaining-task specifications

### Task 22 — Desktop Background Execution and Non-Blocking UI

First Phase 2 task and the next unfinished task. Introduce one reusable, bounded
worker/lifecycle pattern for justified slow desktop operations. Preserve passive
Views and Qt-free Presenters by placing Qt execution mechanics in an approved
adapter/composition boundary. Cover stale results, cancellation, logout/session
expiry, duplicate actions, safe shutdown, and responsive progress/error state.
See `tasks/22-desktop-background-execution-non-blocking-ui.md` for the planning
audit. A full design proposal and approval are required before implementation.

### Task 23 — API Performance, Refresh Reduction, and Safe Local Caching

Implemented across every appropriate reachable desktop screen. Real API
measurement justified a bounded session/user/role-scoped GET cache with
resource TTL/SWR policies, complete keys, identical-flight coalescing, targeted
mutation invalidation, logout/expiry clearing, latest-intent queue removal and
stale suppression, and unchanged-table rebuild avoidance. No backend contract,
schema, authorization, CQRS/Event Sourcing, Gateway, or AI behavior changed.
Task/PIV 23 contain policies, matrices, evidence, and the native-run limitation.

Dependency: Task 22 lifecycle contract.

### Task 24 — End-to-End Booking Request and Creation Workflow

Complete role-aware Booking creation through the existing event-sourced command:
Customer self-service requests, Manager creation for a selected Customer,
Instructor denial, shared Activity/Bookings entry points, targeted cache
reconciliation, and native lifecycle safety.

Dependency: Tasks 22–23.

### Task 25 — Desktop Visual Design System and UI/UX Cohesion

Establish the professional visual and interaction system consumed by Tasks
26–28. Finalize professional non-domain visual foundations, audit all desktop
screens, implement approved shared primitives/tokens, and migrate only the pilot
selected by its later design proposal.

Dependency: Phase 2 complete.

### Task 26 — Shell, Login, Navigation, and Dashboard Experience

Apply Task 25 foundations to the application frame, login/session states,
navigation hierarchy, dashboard summaries, responsive cards/tables, and one
purposeful operational visualization if still justified by the PRD. Do not
change dashboard data semantics or authorization.

Dependency: Task 25 approved and committed.

### Task 27 — Manager Operational Screens UI/UX Completion

Apply the established system to Customers, Users, Instructors, Activities,
Bookings, Booking Details/history/assignments, images, and Knowledge Management.
Close inconsistent filters, dialogs, detail panels, table geometry, action
hierarchy, validation, duplicate warnings where required, and responsive layout.

Dependency: Tasks 25–26.

### Task 28 — Instructor, Customer, and AI-Surface Visual Consistency

Complete role-specific desktop visual/interaction consistency for Instructor
and Customer dashboards, activities, bookings, profiles, Open Events, and the
existing AI consultation surface. This task is visual/UX only; AI behavior and
runtime work remain Phase 4.

Dependency: Tasks 25–27.

### Task 29 — Ollama and RAG Runtime Readiness

Add Docker/Ollama health checks, model readiness/preflight, unified diagnostics,
documented startup/recovery, and responsive failure handling. Reuse Phase 2
execution/cancellation contracts. Do not add unrelated AI product behavior.

Dependency: Phases 2–3 complete.

### Task 30 — AI/RAG, Semantic Search, and Professional AI Experience Completion

Complete approved AI interaction, semantic-search quality, live-corpus
verification, source/citation distinction, retry/reset/cancel behavior, and
knowledge-management usability. AI remains grounded, role-aware, and read-only;
there is no web fallback or operational mutation.

Dependency: Task 29 and the Phase 3 visual system.

### Task 31 — End-to-End Stabilization and Performance Verification

Freeze features; run the complete role/authorization, CRUD, booking event/replay,
Gateway, AI/RAG, cross-screen identity, accessibility, responsive-layout,
failure/recovery, and latency acceptance matrix. Rehearse approved demo data and
resolve only verified defects.

Dependency: Tasks 22–30.

### Task 32 — Windows Packaging, Submission Documentation, and Demo Materials

Create the verified Windows packaging/startup path, clean-environment setup,
configuration/secret guidance, screenshots, architecture diagrams, PIV index,
traceability evidence, demo script, and release materials. Package only behavior
already accepted in Task 31.

Dependency: Task 31.

### Task 33 — Final Architecture, Security, Product, UX, and Release Audit

Perform the final read-only release audit against PRD, architecture, MVP,
authorization, CQRS/Event Sourcing, Gateway, RAG grounding, security, UX,
performance, packaging, documentation, and Git cleanliness. Return approval or
required fixes; do not add features.

Dependency: Task 32.

## 5. Dependency sequence

```text
Tasks 01–21 complete
        |
        v
Task 22 Desktop Background Execution / Non-Blocking UI
        v
Task 23 API Performance / Refresh / Safe Caching
        v
Task 24 Role-Aware Booking Request / Creation
        |
        v
Task 25 Visual System / UI-UX Cohesion
        v
Task 26 Shell / Login / Dashboard
        v
Task 27 Manager Operational UX
        v
Task 28 Instructor / Customer / AI-Surface Visual Consistency
        |
        v
Task 29 Ollama / RAG Runtime Readiness
        v
Task 30 Remaining AI / RAG / Semantic Search UX
        |
        v
Task 31 Stabilization / Performance Verification / Regression
        v
Task 32 Windows Packaging / Submission Materials
        v
Task 33 Final Audit
```

## 6. Cross-cutting rules

- The PRD remains the product source of truth.
- Work task by task; do not implement later phases early.
- Every task requires design review, Codex implementation, complete ChatGPT
  audit, product-owner approval, then commit/push.
- Preserve desktop MVP: passive PySide6 Views, Qt-free Presenters, service/API
  adapters, and FastAPI-only operational data access.
- Preserve thin FastAPI routers and application/domain/infrastructure ownership.
- Preserve booking CQRS, immutable Event Sourcing, replay, projections, and
  optimistic concurrency.
- Preserve Gateway isolation for external providers.
- Preserve server-side authorization and role/resource ownership.
- Preserve grounded, cited, role-aware, read-only AI behavior.
- Do not create secrets, default passwords, legacy accounts, or silent identity
  links.
- Do not use unbounded caches or background work without lifecycle ownership.
- Update Task/PIV, this roadmap, traceability, and architecture only when the
  task changes implemented architectural evidence.

## 7. Immediate next action

Task 24 is implemented, validated, committed, and pushed. Task 25 is the next
unfinished task. Do not begin Task 25 until a separate design/audit prompt is
approved.
