# Experience-with-Soul: Authoritative Remaining-Project Roadmap

## 1. Purpose and authority

This document is the authoritative planning baseline for work after Task 19.
It is subordinate to `docs/PRD.md` and `AGENTS.md`, but supersedes stale
"next task" suggestions in historical task and PIV records. Tasks 01–19 are
complete and must not be redefined. The baseline commit is
`1783cdc01ef731eb51ecb68565c994455cfc11b4` (`Task 19: Desktop activity image
workflow`).

The roadmap is evidence-based: a folder, class, route, test, or document alone
does not establish completion. "Complete" below means that the capability has
an intended application path and credible end-to-end demonstration evidence.
The roadmap does not declare the wider project complete.

No Task 20+ specification is created here. Before implementation, each roadmap
item requires its own approved design proposal and normal PIV cycle.

### Roadmap status tracking

| Task | Title | Status | Product-owner input | Design | Implementation | Audit | Commit/push |
|---|---|---|---|---|---|---|---|
| 20 | Neutral Desktop UX, Accessibility, and Request-State Foundations | Planned | Not required for neutral structure | Not started | Not started | Not started | Not started |
| 21 | Manager User and Role Administration | Planned | Identity-policy decisions required | Not started | Not started | Not started | Not started |
| 22 | Runtime Readiness and Ollama/Docker Operations | Planned | Demo hardware/model confirmation required | Not started | Not started | Not started | Not started |
| 23 | API Reliability, Security, Idempotency, and Observability | Planned | Error-language approval helpful | Not started | Not started | Not started | Not started |
| 24 | Mandatory Branding and Content Approval Checkpoint | Awaiting product-owner input | Mandatory brand/content assets and rules | Not started | Not applicable | Not started | Not started |
| 25 | Branded Shell, Login, and Operational Dashboard | Planned | Task 24 approval required | Not started | Not started | Not started | Not started |
| 26 | Manager Operations UX and Data-Quality Completion | Planned | Workflow terminology and duplicate policy required | Not started | Not started | Not started | Not started |
| 27 | Instructor and Customer Experience Completion | Planned | Role wording/claim decision required | Not started | Not started | Not started | Not started |
| 28 | Professional AI Consultation and Knowledge UX | Planned | Suggested questions/disclaimer approval required | Not started | Not started | Not started | Not started |
| 29 | Desktop Responsiveness and Long-Running Operation Closure | Planned | None initially | Not started | Not started | Not started | Not started |
| 30 | Domain-Relevant External-Service Decision and Gateway Closure | Awaiting product-owner input | Mandatory product-owner/course decision | Not started | Not started | Not started | Not started |
| 31 | End-to-End Acceptance, Demo Data, and Operational Rehearsal | Planned | Demo content approval required | Not started | Not started | Not started | Not started |
| 32 | Submission Documentation, Windows Packaging, and Demo Materials | Planned | Submission assets/screenshots approval required | Not started | Not started | Not started | Not started |
| 33 | Final Architecture, Security, Product, UX, and Submission Audit | Planned | Final approval required | Not started | Not started | Not started | Not started |

Allowed lifecycle states are `Planned`, `Awaiting product-owner input`,
`Design approved`, `In implementation`, `Audit required`, `Fixes required`,
`Approved`, and `Committed and pushed`. The roadmap must be updated after every
approved task and again after its clean commit and push. Status must describe
actual repository state, not intended progress.

## 2. Current baseline after Task 19

The system is a working academic modular monolith with:

- a FastAPI backend and Supabase-compatible PostgreSQL schema;
- a PySide6 RTL desktop client using View, Presenter, service, and API layers;
- token authentication and server-enforced manager/instructor/customer access;
- manager customer/contact, instructor, activity, image, booking, assignment,
  and RAG-source workflows;
- instructor assigned/open-event views and a read-only activity catalog;
- customer-owned booking/profile views and a read-only activity catalog;
- booking CQRS, immutable domain events, replay, projections, and optimistic
  concurrency;
- Cloudinary behind an application-owned image Gateway;
- Ollama generation and embedding clients, Docker Compose, pgvector ingestion
  and retrieval, role-aware grounding, abstention, citations, desktop chat, and
  manager knowledge management;
- 169 backend and 111 desktop tests at the Task 19 baseline.

This is a strong functional baseline, not a submission-ready product. The
largest mandatory gap is user and role administration. Runtime readiness,
consistent API reliability/observability, professional UI/UX, AI interaction
quality, purposeful graph evidence, complete manual acceptance, branding, and
submission packaging also remain.

## 3. Repository areas inspected

The planning review covered:

- `AGENTS.md`, `README.md`, `ARCHITECTURE.md`, and `docs/PRD.md`;
- every task file under `tasks/` (including the intentionally empty Task 01
  placeholder) and every PIV file under `docs/piv/`;
- requirement traceability and historical decisions from Tasks 01–19;
- all FastAPI routers, schemas, application services, booking commands/queries,
  booking aggregate/events, repositories, database schema/seed paths, auth
  helpers, image Gateway interfaces/providers, and composition root;
- all desktop API, model, service, presenter, View, dialog, navigation, shell,
  and composition-root code;
- Ollama LLM/embedding clients, RAG formatting/evaluation/reset/cleanup code,
  knowledge ingestion/retrieval/management, and AI consultation orchestration;
- `docker/docker-compose.yml`, backend environment examples, runtime health
  endpoints, and Windows setup commands;
- backend and desktop automated tests, architecture scans, authorization tests,
  replay/concurrency tests, Gateway tests, and RAG tests;
- current Git state and the Task 19 baseline commit.

## 4. Course-requirement compliance matrix

| Requirement | Repository evidence | End-to-end user-visible evidence | Status | Remaining gap | Closing task | Manual submission proof |
|---|---|---|---|---|---|---|
| User management | `users` table, user repository, seeded accounts | Users can sign in, but no user administration route or screen exists | Missing | Manager cannot create, activate/deactivate, link, or role-manage users | Task 21 | Manager creates a user, assigns an allowed role/profile, disables it, and disabled login fails |
| Authentication | `/auth/login`, `/auth/me`, password hashing, JWT, desktop login | All three demo roles can sign in and enter a scoped workspace | Complete | Final clean-environment/live proof only | Task 31 | Successful and failed sign-in plus session expiry |
| Role-based behavior | `require_roles`, resource checks, role navigation, role-safe schemas | Manager/instructor/customer see different modules and data | Complete | Final matrix regression and screenshots | Tasks 27, 31 | Execute one allowed and one denied action per role |
| Data search | Customer/activity/instructor/booking queries and desktop filters | Module-specific searches and filters are usable | Complete | Consistency/usability polish; no cross-module search is justified | Tasks 26, 27 | Search Hebrew data in each demonstrated module |
| Selected-result details | Detail endpoints, presenters, detail panels/dialogs | Customers, activities, instructors, bookings, open events, and sources expose details | Complete | Visual hierarchy and resize polish | Tasks 26, 27 | Select rows and show full, role-safe detail views |
| Table or graph presentation | Reusable booking tables and entity tables | Operational lists and dashboard tables are visible | Complete for tables; graph partial | Add one purposeful manager operational graph, not decorative charts | Task 25 | Show graph values matching the underlying filtered data |
| Domain data entry | Manager dialogs and command workflows | Manager can enter customers, contacts, activities, images, bookings, instructors, assignments, and knowledge | Complete | Duplicate warning and form consistency remain | Task 26 | Create the complete manager scenario through desktop forms |
| Domain AI consultation | `/api/ai/consult`, RAG service, desktop chat | Authenticated roles can ask grounded questions and see sources | Complete functionally | Professional interaction, cancellation, retry/reset, and source distinction | Task 28 | Relevant, restricted, unsupported, proposal-draft, and unavailable-service questions |
| Desktop application | `desktop_client/app/main.py` | One Windows desktop executable flow | Complete | Packaging/startup, responsiveness, and visual polish | Tasks 20, 25–29, 32 | Launch from documented clean setup on supported Windows |
| PySide6 | Views/dialogs and Qt composition root | All intended application screens use PySide6 | Complete | Accessibility and responsive behavior | Tasks 20, 25–29 | Keyboard and resize walkthrough |
| MVP | Separate views, presenters, services, API client; architecture tests | UI intents flow through presenters/services | Complete | Preserve boundaries during redesign and background work | Tasks 20–30, 33 | Explain one feature flow and show boundary tests |
| Modular desktop UI / microfrontends | Separate feature presenters/views/services composed by `MainWindow` | Role navigation loads independently bounded modules | Complete | Make module ownership and shared UI/request-state contracts more visible | Task 20 | Demonstrate navigation and describe module boundaries |
| FastAPI | Routers and OpenAPI application | Desktop operations traverse HTTP API | Complete | Versioning remains divergent from PRD but is not worth disruptive migration unless required by assessor | Tasks 32, 33 | Open health/OpenAPI and execute representative calls |
| Server MVC/CQRS organization | routers, schemas, application, domain, infrastructure | Thin route-to-use-case flows are demonstrable | Complete | Standardize reliability contract without broad restructuring | Task 23 | Trace one CRUD flow and one booking command/query flow |
| CQRS | Booking command handlers and query handlers | Manager commands refresh projection-backed screens | Complete | Final projection/replay demonstration tooling | Task 31 | Show command, query result, history, and replay |
| Event Sourcing | booking aggregate/events/event repository/projection repository | Supported booking changes appear in chronological history | Complete | Demo evidence and event/projection consistency audit | Tasks 31, 33 | Change date/price/status/assignment and replay the booking |
| Cloud-hosted database | PostgreSQL/pgvector connection and Supabase-compatible schema | Live PIV records show configured database workflows | Complete | Clean setup and live submission verification | Tasks 31, 32 | Show database reachability and persisted cross-session data |
| Gateway pattern | `ImageGateway`, Cloudinary adapter/provider | Manager image upload/display/delete works end to end | Complete | Preserve boundary and obtain assessor ruling on domain-service criterion | Tasks 30, 33 | Upload/delete while explaining provider isolation |
| Domain-relevant external service | Cloudinary supports the activity catalog, but is media infrastructure | Activity images are user-visible and business-relevant | Unclear | Confirm whether Cloudinary satisfies the course wording; if not, approve one genuinely useful domain service | Task 30 | Demonstrate the approved external data in a real activity/booking decision |
| Ollama through Docker | Compose file, Ollama HTTP clients, documented model pulls | AI works when Docker/Ollama/models are manually ready | Partial | No Compose health check, model/readiness preflight, or unified runtime diagnostic | Task 22 | Start Compose, prove model readiness, then show graceful unavailable/recovery states |
| RAG | pgvector ingestion/retrieval, role filtering, grounded prompt, citations | Manager manages sources; all roles receive scoped grounded answers | Complete functionally | UX and final live corpus verification | Tasks 28, 31 | Ingest, retrieve, answer with citations, abstain, and deny restricted source |
| Git-based development | Git repository and Tasks 01–19 commit history | Task-aligned commits and review-before-commit workflow | Complete | Final release tag/evidence only | Task 32 | Show history, clean tree, and release commit/tag |
| PIV beginning from PRD | Task and PIV documents plus traceability | Every completed increment has planning/validation evidence | Complete | Continue PIV for Tasks 20+ and perform final consistency audit | Tasks 20–33 | Trace a PRD ID to task, code, tests, and manual evidence |
| Cloudinary selected by project | Configuration, Gateway, metadata persistence, desktop flow | Real Task 19 validation uploaded, displayed, and cleaned an image | Complete | Final demo asset and credential-safe rehearsal | Tasks 24, 31 | Upload an owner-approved activity image without exposing credentials |

## 5. Current functional coverage

| Product area | Evidence and usable workflow | Status | Remaining work |
|---|---|---|---|
| Login/session lifecycle | Login, JWT, `/auth/me`, logout, 401 expiry callback | Complete | Improve branded presentation and final manual expiry proof |
| User administration | Seeded accounts and authentication records only | Missing | Manager CRUD/activation/role/profile-link management |
| Customers/contacts | Manager CRUD/search/filter/page/detail and protected deletion | Complete | Duplicate phone/email warning required by `FR-CUS-04`; UX consistency |
| Instructors | Manager CRUD and instructor self-profile | Complete | UX consistency and final active-assignment validation |
| Activities | Manager CRUD/deactivation; role-safe active catalog | Complete | UX consistency and owner-approved content/assets |
| Activity images | Manager upload/delete; all permitted roles preview | Complete | Owner-approved real demo images and final degraded-provider proof |
| Bookings | Manager create and supported event-sourced mutations; role-scoped reads | Complete | Final idempotency/reliability proof and polished forms/details |
| Instructor assignments | Manager assignment/removal through events | Complete | Final multi-activity demonstration; instructor claiming remains optional/out of scope |
| Booking history/replay | Manager raw history and replay endpoint/tests | Complete | Human-readable demo narrative and final live consistency proof |
| Dashboard | Role-specific counts, shortcuts, and booking tables | Partial visually | Add activity/customer counts required by PRD analytics and one purposeful operational graph |
| Search/filter/sort/page | Strong module-specific coverage; booking combined filters | Complete with uneven UX | Align controls and feedback; cross-module search is not required |
| Reports/export | No manager report/export workflow | Not required for MVP | Exclude unless owner identifies a concrete operational need |
| External integration | Cloudinary image workflow | Complete for selected Gateway; course interpretation unclear | Owner/course decision before any second provider |
| AI consultation | Grounded, role-aware, cited, abstaining, read-only | Complete functionally | Interaction/runtime UX and explicit draft/source presentation |
| Knowledge management | Manager create/upload/list/detail/replace/delete | Complete functionally | Usability, status/diagnostic feedback, and brand polish |
| Runtime health | Backend and database checks; AI failures translated | Partial | Unified DB/Ollama/model readiness and Docker health |
| Errors/validation/feedback | Broad validation and loading/empty/error states | Partial | Consistent API envelope/correlation, retry semantics, form accessibility |
| Notifications | Inline success/error feedback and confirmations | Partial | Consistent non-blocking feedback pattern during UI foundation work |
| Desktop responsiveness | Most presenter network calls are synchronous; Task 19 has local stale-preview guards | Functional calls may freeze the Qt event loop while network work runs | Partial | Shared safe background-execution pattern and remaining slow-workflow closure in Task 29 |

There is no evidence of a currently unusable backend-only Must workflow except
user administration, which is absent at both layers. Existing image-list and
RAG-search endpoints support their intended application flows even where the
desktop consumes richer aggregate endpoints instead.

## 6. Current architecture coverage and risks

### Strong and complete

- Desktop-to-database access is prohibited and architecture-tested.
- Presenters do not import PySide6; Views do not import services or database
  code.
- FastAPI routers delegate business and persistence responsibilities.
- Booking commands and projection queries are separated.
- Booking events are authoritative, ordered, replayable, and versioned.
- Gateway interfaces isolate Cloudinary; no provider SDK exists in desktop.
- RAG authorization is derived from the authenticated role and enforced in SQL.
- AI is read-only and abstains without approved evidence.
- Secrets are configured outside tracked source; `.env.example` contains only
  placeholders.

### Partial or risky

- `docker-compose.yml` starts Ollama but declares no health check, model
  readiness, or automated preflight.
- `/health` reports only FastAPI process health; DB and Ollama readiness are
  fragmented.
- PRD-standard safe error codes and correlation identifiers are not consistently
  returned across APIs; raw event correlation exists only in booking data.
- Duplicate submission is blocked in presenters, but the PRD's API idempotency
  requirement is not consistently implemented for booking creation/commands.
- Desktop HTTP calls, including AI generation, are synchronous. The UI displays
  loading but cannot satisfy `NFR-03` cancellation while work is in progress.
- No shared application-wide worker/lifecycle contract prevents slow upload,
  search, dashboard, save, or detail completion from updating an obsolete
  module/session; Task 20 defines request-state contracts and Task 29 closes the
  justified long-running paths.
- UI modules are separated by class/layer rather than feature packages. This is
  sufficient for the course's modular UI requirement; a repository-wide package
  migration would add risk without user value and is not proposed.
- API paths are not uniformly under `/api/v1`. A disruptive re-versioning is not
  proposed unless the assessor explicitly requires literal path versioning.
- Logging lacks a consistent operation/user/correlation policy required by
  `NFR-08`.

## 7. Role-by-role completeness

### Manager

The manager has the broad operational workflow required for customers,
contacts, instructors, activities, images, bookings, assignments, history,
dashboard, AI, and knowledge sources. The role is not complete because the PRD
explicitly grants user/role administration and no such module exists. The
manager experience is also visually dense and inconsistent, with limited
responsive behavior and no graph-based operational overview.

### Instructor

The instructor can sign in, view a profile, active activities, assigned
bookings, and eligible open events, and use role-scoped AI. Commercial/customer
data is constrained by backend schemas. Instructor claim/request is a Could
requirement conditioned on a feature flag and is intentionally excluded unless
the product owner enables it. Remaining work is primarily navigation clarity,
mobile-not-required window resizing, accessible tables/details, and final
manual role proof.

### Customer

The customer can sign in, view an owned profile, active catalog/images, only
their own bookings, dashboard information, and customer-scoped AI. There is no
customer mutation requirement in the MVP. Remaining work is clearer self-service
language, empty/error states, responsive details, and final isolation proof.

## 8. AI/RAG status

### Implemented

- authenticated question submission for all three roles;
- pgvector retrieval using the production embedding formatter/model/dimensions;
- fail-closed role filtering before generation;
- strict retrieved-context-only prompt construction;
- fixed no-information behavior when retrieval is empty or the model signals
  insufficient context;
- rejection of uncited generated answers;
- return/display of only cited source records;
- conversation transcript for the current in-memory screen session;
- loading and basic error states;
- manager-controlled pasted text and UTF-8 `.txt`/`.md` source management;
- Ollama unavailability translation without affecting core operational modules;
- extensive mocked tests and live Hebrew retrieval evidence.

### Remaining professional-experience gaps

- the synchronous call cannot be cancelled, despite `NFR-03`;
- there is no retry action tied to the failed prompt;
- there is no explicit new-conversation/reset control;
- suggested questions and purpose guidance are absent;
- sources are appended as plain text rather than a clearly distinguished source
  panel;
- proposal drafts are not visually labeled as drafts requiring human review;
- the empty state does not teach users what approved questions can be answered;
- there is no visible Ollama/model readiness diagnostic;
- conversation history is only in-memory, which is acceptable for the MVP and
  should not become persisted chat history without a new privacy requirement.

Task 28 closes only these bounded experience gaps; it must not weaken grounding,
add web/general-knowledge fallback, or introduce AI writes.

## 9. UI/UX status

The desktop is functional but visually and ergonomically unfinished. It has RTL
direction, Hebrew labels, reusable search/pagination/state widgets, role-scoped
navigation, tables, dialogs, confirmations, and basic loading/empty/error
feedback. The current global stylesheet is a small fixed palette; many screens
use compressed one-line construction, dense forms, plain text controls, and
limited resize/scroll behavior. There is no established spacing/type/icon/token
system, formal minimum resolution, consistent focus policy, or accessibility
acceptance suite.

UI/UX work must be staged:

1. Task 20 establishes neutral structural foundations—layout, component APIs,
   resizing, scrolling, focus, accessible labels, and state behavior—without
   inventing branding.
2. Task 24 is a mandatory product-owner branding checkpoint and approved visual
   specification.
3. Tasks 25–28 apply the approved system to shell/dashboard, manager modules,
   role experiences, and AI/knowledge respectively.

### Work allowed before branding approval

- layout and reusable component structure;
- navigation behavior and MVP contracts;
- accessible names, keyboard order, focus visibility, and contrast validation
  machinery;
- resize, minimum-size, scroll, overflow, and state behavior;
- neutral temporary tokens explicitly labeled temporary.

### Work blocked on branding approval

- final palette and typography;
- official logo treatment and placement;
- branded login/dashboard surfaces;
- activity-card/image treatment;
- AI-chat visual identity;
- final icons, imagery, and polished tone.

The project must not generate, redraw, or replace the organization's logo.

## 10. External-service status

Cloudinary is a real external provider, is relevant to the catalog, and already
demonstrates the Gateway pattern end to end. It may nevertheless be judged as
media infrastructure rather than a domain-information service. No second
domain-relevant service exists.

Before Task 30 is specified, the product owner and, preferably, course assessor
must decide whether Cloudinary satisfies the requirement. If it does, Task 30
becomes a short evidence/documentation closure task and adds no provider. If it
does not, select exactly one useful service. Candidate categories—not selected
decisions—are weather for outdoor activity planning, geocoding/location
validation, or travel-time information. The chosen capability must have a real
role, workflow, data source, graceful unavailable state, and application-owned
Gateway. Decorative API use is forbidden.

## 11. Major remaining gaps

1. Missing manager user/role administration (`User Administration` is a PRD
   screen and manager permission).
2. Incomplete Docker/Ollama/model readiness and unified health evidence.
3. Partial API idempotency, safe error/correlation, and observability behavior.
4. Functional but structurally inconsistent desktop UX and incomplete
   accessibility/responsiveness proof.
5. Missing official branding/assets and product-owner visual decisions.
6. Dashboard lacks PRD-listed activity/customer counts and a purposeful graph.
7. Manager modules need consistent validation, duplicate warning, layout, and
   feedback.
8. Instructor/customer experiences need final role-specific UX and manual proof.
9. AI chat and knowledge screens need cancellation/retry/reset/source/draft UX.
10. Remaining long-running desktop workflows need a shared non-blocking,
    thread-safe, stale-result/session-safe execution pattern.
11. Domain-relevant external-service compliance is unclear.
12. The full PRD acceptance scenario has not been rehearsed and captured as one
    clean, repeatable end-to-end submission proof.
13. Final setup, screenshots, demo script, limitations, traceability, and clean
    environment verification remain.

## 12. Ordered Task 20+ roadmap

### Task 20 — Neutral Desktop UX, Accessibility, and Request-State Foundations

1. **Goal:** Establish structural, neutral desktop foundations before new
   modules or brand-dependent design.
2. **Why required:** Existing screens work but lack consistent layout,
   component, focus, resize, overflow, feedback, and request-state conventions.
3. **Evidence:** The global style is small, screen construction is uneven and
   dense, and no documented minimum resolution, keyboard audit, or reusable
   asynchronous request-state contract exists.
4. **User-visible outcome:** Consistent, space-efficient screens with readable
   hierarchy, predictable actions and states, keyboard access, RTL behavior,
   and robust resizing in a neutral temporary theme.
5. **Main scope:** Shared spacing/layout foundations; reusable form, table,
   card, toolbar, dialog, state, and feedback components; accessible names and
   labels; visible keyboard focus and logical focus order; RTL/Hebrew behavior;
   minimum supported window size; resize and scroll behavior; table overflow,
   long-text handling, and tooltips for truncation; primary, secondary, and
   destructive action hierarchy; loading, empty, error, success, and validation
   conventions; and request-state contracts needed by future asynchronous work.
   Neutral temporary tokens must be explicitly documented as temporary.
6. **Out of scope:** Final colors, fonts, official logo treatment, invented
   branding, screen-specific business redesign, or conversion of all network
   operations to background execution.
7. **Roles affected:** All.
8. **Architecture:** Shared passive Views and presenter-facing state contracts;
   no Qt imports in presenters and no data access in Views.
9. **Course requirements:** PySide6, MVP, modular UI, RTL, accessibility,
   Windows portability, professional design, testability.
10. **Dependencies:** Task 19 baseline.
11. **Automated acceptance:** Architecture scans; component state contracts;
    accessible properties; focus order; resize/scroll/overflow construction;
    tooltips; action hierarchy; full desktop regressions.
12. **Manual acceptance:** Keyboard-only walkthrough, Hebrew/RTL review,
    minimum/larger window sizes, long values and tables, every shared state, and
    screenshots showing neutral—not final—styling.
13. **Product-owner input:** None; this task must not make brand decisions.
14. **Size:** Large.
15. **Risk:** Medium.

### Task 21 — Manager User and Role Administration

1. **Goal:** Implement the missing manager-only identity administration flow on
   the stable Task 20 foundations.
2. **Why required:** The PRD grants managers user/role management and lists a
   User Administration screen; only seeded/login users currently exist.
3. **Evidence:** `auth.py` exposes login/me only; navigation has no user module;
   the user repository is read-only for authentication.
4. **User-visible outcome:** Managers can list, create, inspect, update, and
   deactivate users, with safe role-compatible customer/instructor links.
5. **Main scope:** Approved password policy; password hashing/non-exposure;
   unique normalized email; role-compatible profile linkage; prevention of
   duplicate profile links; safe role transitions; last-active-manager and
   self-deactivation protection; session behavior after deactivation;
   audit-safe administration events/logs; manager-only API/UI; and an explicit
   login-abuse/rate-limit decision. Deactivation is the default instead of
   physical deletion unless the product owner explicitly approves otherwise.
6. **Out of scope:** Self-registration, reset-email delivery, MFA, enterprise
   identity, Supabase Auth migration, fine-grained permissions, and physical
   deletion by default.
7. **Roles affected:** Manager directly; instructor/customer session lifecycle
   indirectly.
8. **Architecture:** Schema/repository/application/router plus desktop
   service/presenter/passive View and composition root.
9. **Course requirements:** User management, authentication, RBAC, security,
   data entry/search/details/tables, MVP, FastAPI, cloud database, PIV.
10. **Dependencies:** Task 20.
11. **Automated acceptance:** Password policy/hash/non-exposure; unique email;
    role/link rules; duplicate-link rejection; safe role transitions;
    last-manager and self-deactivation guards; disabled-session/login behavior;
    audit-safe evidence; manager authorization; rate-limit decision tests where
    adopted; presenter/View tests and full regressions.
12. **Manual acceptance:** Manager creates each role, tests invalid links and
    self/last-manager protection, changes a safe role, deactivates another user,
    verifies session/login behavior, and reviews loading/error/empty states,
    RTL, resize, and screenshots.
13. **Product-owner input:** Approve password policy, password-reset scope,
    deactivation/deletion policy, and session invalidation expectation.
14. **Size:** Large.
15. **Risk:** High because identity linkage and authorization are critical.

### Task 22 — Runtime Readiness and Ollama/Docker Operations

1. **Goal:** Make the runtime diagnosable and reliably demonstrable.
2. **Why required:** Compose starts Ollama but has no health/model readiness;
   backend health does not cover AI dependencies.
3. **Evidence:** Compose declares image/port/volume only; `/health` reports
   process health; AI errors tell users to check Ollama.
4. **User-visible outcome:** Operators can verify API, database, Ollama,
   generation model, and embedding model readiness; AI users receive a friendly
   unavailable state and recovery path.
5. **Main scope:** Compose health check, bounded readiness endpoint/service,
   model-presence diagnostics, Windows startup order, safe error translation,
   and retry/status behavior where appropriate.
6. **Out of scope:** Kubernetes, cloud Ollama, automatic large downloads,
   monitoring platforms, or high availability.
7. **Roles affected:** All AI users; manager/operator setup.
8. **Architecture:** Docker, configuration, system/AI health boundary, desktop
   status presentation.
9. **Course requirements:** Docker/Ollama, RAG demonstrability, runtime health,
   portability, error handling.
10. **Dependencies:** Task 21 only by authoritative sequence.
11. **Automated acceptance:** Ready/unreachable/model-missing/timeout states,
    no secret leakage, and Compose validation.
12. **Manual acceptance:** Start/stop Docker, validate model readiness, ask a
    question, stop/restart Ollama, and prove friendly failure/recovery.
13. **Product-owner input:** Confirm demo hardware and generation model.
14. **Size:** Medium.
15. **Risk:** Medium.

### Task 23 — API Reliability, Security, Idempotency, and Observability

1. **Goal:** Close concrete reliability/security gaps without reorganizing
   working modules.
2. **Why required:** Error bodies/logging are inconsistent, request correlation
   is incomplete, and duplicate prevention is mostly desktop-local.
3. **Evidence:** Routers return varied details; booking events can store
   correlation IDs, but no consistent request/error or idempotency policy exists.
4. **User-visible outcome:** Failures are understandable, duplicate booking
   submissions do not duplicate events, and safe diagnostic IDs can be reported.
5. **Main scope:** Common safe error/correlation contract, structured logging,
   security/privacy log policy, idempotency for duplicate-prone booking creation
   and selected commands, timeout audit, and compatibility tests.
6. **Out of scope:** Tracing vendor, global API rewrite, `/api/v1` migration,
   generic retry framework, or event-store redesign.
7. **Roles affected:** All.
8. **Architecture:** FastAPI composition/middleware, command boundary, schemas,
   and desktop error translation.
9. **Course requirements:** Reliability, security, maintainability,
   observability, CQRS/Event Sourcing correctness.
10. **Dependencies:** Tasks 20–22.
11. **Automated acceptance:** Idempotent duplicate behavior; conflicting reuse;
    safe correlation in responses/logs; token/password/PII scans; existing-client
    compatibility and full regressions.
12. **Manual acceptance:** Duplicate submit, conflict, DB/provider outage, and
    friendly Hebrew feedback with safe diagnostic ID.
13. **Product-owner input:** Approve generic user-facing error language.
14. **Size:** Large.
15. **Risk:** High because the changes are cross-cutting.

### Task 24 — Mandatory Branding and Content Approval Checkpoint

1. **Goal:** Obtain and document the real organization's approved visual and
   content assets before final styling.
2. **Why required:** The organization has an existing identity; inventing a
   palette, logo, typography, or imagery would be incorrect.
3. **Evidence:** Current code uses temporary colors/text and repository contains
   no approved brand asset package or usage rules.
4. **User-visible outcome:** None yet; this produces the approved specification
   that safely enables Tasks 25–28.
5. **Main scope:** Asset inventory, usage rights, approved logo variants,
   colors, font guidance, real activity images, reference links/materials,
   visual tone, restrictions, content verification, and an approved design-token
   mapping plan.
6. **Out of scope:** Generating/replacing the logo, changing production UI,
   inventing missing brand decisions, or implementing screen redesigns.
7. **Roles affected:** All future screen experiences.
8. **Architecture:** Documentation/assets only; define how assets will be loaded
   without coupling presenters to Qt resources.
9. **Course requirements:** Professional design, product-owner validation, PIV.
10. **Dependencies:** Tasks 20–23; Task 20 identifies structural slots and
    constraints.
11. **Automated acceptance:** Asset/license/path checks where applicable; no
    production behavior change.
12. **Manual acceptance:** Product owner reviews a brand/reference board and
    signs off the exact assets/tokens/tone.
13. **Product-owner input:** Mandatory: official logo files and variants, brand
    colors, font guidance, real activity images, website/social references,
    marketing materials, preferred tone, and restrictions on logo/color use.
14. **Size:** Small.
15. **Risk:** High schedule risk because later visual tasks are blocked without
    owner response.

### Task 25 — Branded Shell, Login, and Operational Dashboard

1. **Goal:** Apply approved branding to the application frame and turn the
   dashboard into a clear operational overview.
2. **Why required:** Shell/login are functional but generic; dashboard lacks
   PRD-listed activity/customer counts and graph-based evidence.
3. **Evidence:** `APP_STYLE` is minimal; dashboard has numeric cards and tables
   only; no chart implementation exists.
4. **User-visible outcome:** Branded login/shell/navigation and a role-appropriate
   dashboard with readable cards, tables, and one useful manager graph.
5. **Main scope:** Approved logo/tokens; clear, space-efficient shell hierarchy;
   role-specific welcome and purpose guidance; selected navigation; branded
   login states; clear primary actions; accessible icons with text; consistent
   cards, status badges, tables/column sizing, truncation tooltips, readable
   details, non-blocking feedback, helpful empty states, dashboard
   customer/activity counts, and one operational chart such as upcoming
   bookings by status with a clear query source and drill-down.
6. **Out of scope:** Revenue/profit analytics, decorative charts, export,
   unrelated module forms, or invented branding.
7. **Roles affected:** All; graph/count additions primarily manager.
8. **Architecture:** Dashboard query/read model, presenter, passive chart View,
   shell/login Views; chart calculations stay outside widgets.
9. **Course requirements:** Graph/table presentation, dashboard, MVP, PySide6,
   professional design, role behavior.
10. **Dependencies:** Tasks 23 and 24.
11. **Automated acceptance:** Count/query correctness, graph mapping, role data
    scope, drill-down, presenter passive-view tests, resize/accessibility tests.
12. **Manual acceptance:** All three roles; empty/populated/error/loading
    dashboards; graph-to-list comparison; RTL, keyboard, resize, screenshots,
    owner visual approval.
13. **Product-owner input:** Approve dashboard priorities, graph choice, and
    final shell/login appearance.
14. **Size:** Large.
15. **Risk:** Medium.

### Task 26 — Manager Operations UX and Data-Quality Completion

1. **Goal:** Professionally finish manager customer, instructor, activity,
   image, booking, assignment, and detail workflows.
2. **Why required:** Core flows exist but forms/tables/actions are visually
   inconsistent; `FR-CUS-04` duplicate warnings remain unimplemented.
3. **Evidence:** Separate functional screens use varying dense layouts and
   feedback; no likely duplicate customer warning path is present.
4. **User-visible outcome:** Consistent manager workbench with clear forms,
   validation, destructive actions, details, filters, and duplicate guidance.
5. **Main scope:** Apply approved components/branding; clear visual hierarchy
   and efficient space use without oversized empty areas; likely duplicate
   phone/email check and non-blocking warning; consistent tables, column sizing,
   status badges, filters/sort/page behavior, selection preservation after
   refresh where appropriate, long-content tooltips, readable detail/image/
   history/assignment panels, clear primary actions, visibly distinct
   destructive actions, friendly Hebrew errors, non-blocking feedback, helpful
   empty states, and timezone display audit.
6. **Out of scope:** New CRM entities, inventory management, payments,
   reporting/export, booking event redesign, or batch media.
7. **Roles affected:** Manager.
8. **Architecture:** Existing feature MVP paths; add only bounded query/service
   support needed for duplicate detection or documented presentation gaps.
9. **Course requirements:** Data entry/search/details/tables, manager workflow,
   usability, accessibility, validation, notifications.
10. **Dependencies:** Tasks 23–25.
11. **Automated acceptance:** Duplicate normalization/warning, all existing CRUD
    and command tests, role guards, focus/state/resize tests, architecture scans.
12. **Manual acceptance:** Full manager journey including duplicates,
    validation failures, conflicts, empty states, provider error, RTL, resize,
    screenshots, owner approval.
13. **Product-owner input:** Confirm duplicate-warning policy and approved
    terminology/content for customer/activity fields.
14. **Size:** Large.
15. **Risk:** Medium.

### Task 27 — Instructor and Customer Experience Completion

1. **Goal:** Finish the two read-oriented role experiences without broadening
   permissions.
2. **Why required:** Functionality exists but needs role-specific clarity,
   responsive detail layouts, and manual isolation evidence.
3. **Evidence:** Shared operational screens are role-filtered but remain generic
   and visually dense; no final product-owner-reviewed walkthrough exists.
4. **User-visible outcome:** Instructors clearly see assigned/open work and
   preparation information; customers clearly see their bookings and catalog.
5. **Main scope:** Branded role navigation/copy and role-specific welcome/purpose
   guidance; clear, space-efficient dashboard/list/detail hierarchy; consistent
   tables, columns, status badges, accessible icons/text, primary actions,
   truncation tooltips, stable selection after refresh where appropriate,
   activity image/content treatment, readable detail panels, helpful empty
   states, friendly Hebrew errors, non-blocking feedback, filters,
   accessibility, and restricted-field presentation audits.
6. **Out of scope:** Instructor claiming (unless separately approved), customer
   booking creation, commercial data exposure, or new permissions.
7. **Roles affected:** Instructor and customer.
8. **Architecture:** Existing role-scoped query/presenter/View paths; backend
   schemas remain fail-closed.
9. **Course requirements:** Role behavior, ownership, search/details/tables,
   professional UI, accessibility.
10. **Dependencies:** Tasks 23–26.
11. **Automated acceptance:** Navigation and schema isolation, owned/assigned
    filters, inactive visibility, responsive/focus/state tests, full regressions.
12. **Manual acceptance:** Log in as both roles; exercise all pages and states;
    attempt forbidden API actions; check Hebrew/RTL, keyboard, resize, and
    screenshots; owner visual approval.
13. **Product-owner input:** Confirm instructor/customer wording and whether
    instructor claim remains disabled.
14. **Size:** Medium.
15. **Risk:** Medium.

### Task 28 — Professional AI Consultation and Knowledge UX

1. **Goal:** Complete the user experience around the already-correct RAG core.
2. **Why required:** Chat lacks cancellation, retry, reset, guidance, and clear
   source/draft presentation; knowledge management is minimal.
3. **Evidence:** `AIChatView` has transcript/input/send only; synchronous
   presenter call disables input; sources are plain appended text.
4. **User-visible outcome:** Guided, cancellable consultation with retry/reset,
   explicit grounding/source presentation, draft labeling, and clearer manager
   source administration.
5. **Main scope:** AI-specific background execution with safe cancellation and
   result identity, retry last failed prompt, reset in-memory conversation,
   approved suggested questions and purpose guidance, clear visual hierarchy,
   efficient transcript space, empty/loading/error/unavailable states, friendly
   Hebrew errors, non-blocking feedback, accessible source distinction/panel,
   draft disclaimer, consistent actions/tooltips, and knowledge-source
   instructions/forms/lists/statuses understandable to a non-technical manager.
6. **Out of scope:** Persisted chat history, web/general-model fallback, AI
   writes, streaming unless separately justified, reranking, OCR/PDF, or prompt
   policy weakening.
7. **Roles affected:** All chat users; manager knowledge administration.
8. **Architecture:** Presenter-controlled orchestration/cancellation identity,
   passive Qt View/worker boundary, existing AI/RAG services and APIs.
9. **Course requirements:** AI consultation, RAG, sources, role awareness,
   `NFR-03`, accessibility, professional UX.
10. **Dependencies:** Tasks 21–27 and approved brand assets.
11. **Automated acceptance:** Submit/loading/cancel/stale/retry/reset, grounded
    vs no-answer source states, role source isolation, unavailable recovery,
    draft label, no AI mutations, MVP scans.
12. **Manual acceptance:** Relevant equipment/recommendation/proposal questions,
    unsupported query, restricted source by each role, cancel and retry, Ollama
    outage/recovery, knowledge replace/delete, RTL/resize/screenshots, owner
    visual approval.
13. **Product-owner input:** Approve suggested questions, draft disclaimer,
    source terminology, and AI visual tone.
14. **Size:** Large.
15. **Risk:** High because Qt concurrency and cancellation must be safe.

### Task 29 — Desktop Responsiveness and Long-Running Operation Closure

1. **Goal:** Apply one reusable, safe responsiveness pattern to remaining
   application-wide long-running desktop operations.
2. **Why required:** Synchronous network work can freeze the Qt event loop;
   Task 28 owns AI cancellation semantics but does not close other slow flows.
3. **Evidence:** API/service calls are generally invoked synchronously from
   presenters; Task 19 has logical stale-preview identity but no shared worker
   pattern exists.
4. **User-visible outcome:** Slow uploads, dashboard/search/detail loads, saves,
   and other justified network workflows keep the window responsive with clear
   state and safe completion behavior.
5. **Main scope:** Identify genuinely slow operations; reusable background
   execution; Qt thread safety; loading state; duplicate-action prevention;
   configured timeouts; retry only where safe; stale-result rejection using
   activity/module/session identity; logout/session-expiry safety; ignoring
   completion after a View/presenter becomes obsolete; and migration of upload,
   dashboard, search, save, detail-loading, and comparable slow workflows where
   evidence justifies it.
6. **Out of scope:** Moving trivial local operations to threads, changing domain
   behavior, unsafe automatic mutation retry, replacing MVP, or duplicating
   Task 28 chat-specific semantics.
7. **Roles affected:** All.
8. **Architecture:** Presenter-owned orchestration and identity; passive Views;
   services remain UI-independent; Qt worker/thread interaction stays in a
   bounded desktop infrastructure layer.
9. **Course requirements:** Desktop usability, MVP, reliability, performance,
   session safety, Windows responsiveness.
10. **Dependencies:** Tasks 20 and 23; Task 28 provides the AI-specific case.
11. **Automated acceptance:** Main-thread non-blocking behavior, thread-safe UI
    dispatch, loading/duplicate guards, timeout/error mapping, safe retry,
    stale/module/session/logout/expiry/obsolete-View rejection, and full MVP
    architecture regressions.
12. **Manual acceptance:** Exercise slow upload, search, dashboard, save, and
    detail paths; navigate/log out/expire session while work runs; verify no
    freeze, stale render, duplicate mutation, or post-destruction callback.
13. **Product-owner input:** None unless a workflow's retry behavior changes
    user expectations.
14. **Size:** Large.
15. **Risk:** High because Qt threading and session teardown require care.

### Task 30 — Domain-Relevant External-Service Decision and Gateway Closure

1. **Goal:** Resolve the course interpretation and, only if necessary, add one
   approved domain-relevant external integration.
2. **Why required:** Cloudinary clearly proves Gateway/external integration but
   may be judged media infrastructure rather than domain information.
3. **Evidence:** No weather, geocoding, travel-time, or comparable provider is
   present.
4. **User-visible outcome:** Either documented assessor acceptance of
   Cloudinary, or one useful external datum integrated into a real planning
   workflow with graceful degradation.
5. **Main scope:** Written decision first. If a provider is required, specify one
   bounded use case, application Gateway, configuration/timeouts, role-safe API,
   desktop presentation, caching/privacy policy, tests, and manual proof.
6. **Out of scope:** Selecting a provider without approval, multiple providers,
   decorative widgets, route planning platform, or provider SDK in business/UI
   code.
7. **Roles affected:** Determined by chosen use case; likely manager and possibly
   instructor.
8. **Architecture:** New application Gateway and infrastructure adapter only if
   required; FastAPI remains the desktop boundary.
9. **Course requirements:** Domain external service, Gateway, configuration,
   error handling.
10. **Dependencies:** Product-owner/course decision; stable UI foundation.
11. **Automated acceptance:** Gateway contract, adapter errors/timeouts, no
    secrets, role rules, unavailable behavior, presenter/View tests.
12. **Manual acceptance:** Demonstrate a real decision improved by provider
    data, then provider outage without blocking core operations.
13. **Product-owner input:** Mandatory approval of whether Cloudinary suffices;
    if not, approve use case, provider, data/privacy implications, and costs.
14. **Size:** Small if evidence-only; Medium if one integration is approved.
15. **Risk:** High until the decision is resolved; Medium after scope approval.

### Task 31 — End-to-End Acceptance, Demo Data, and Operational Rehearsal

1. **Goal:** Prove the complete PRD scenario in one repeatable live environment.
2. **Why required:** Individual PIV live checks exist, but submission requires a
   coherent cross-role scenario with clean data and captured evidence.
3. **Evidence:** PRD Section 20 defines a nine-step scenario; no single final
   acceptance artifact covers the completed product.
4. **User-visible outcome:** Stable demo accounts/data and a rehearsed manager →
   instructor → customer → AI journey.
5. **Main scope:** Safe repeatable demo preparation/verification, official vs
   demo-only content labels, full role workflow, event/replay comparison,
   external services, all states, performance observations, screenshots, and
   defect triage.
6. **Out of scope:** New features, production migration, destructive reset of
   non-demo data, or cosmetic redesign.
7. **Roles affected:** All.
8. **Architecture:** End-to-end only; changes require separately approved defect
   fixes, not hidden enhancements.
9. **Course requirements:** Every functional and architectural demonstration.
10. **Dependencies:** Tasks 20–30.
11. **Automated acceptance:** Full suites, database-backed integration where
    configured, replay/projection verification, security scans, compile,
    whitespace, Docker configuration, and clean-environment startup.
12. **Manual acceptance:** Execute PRD Section 20, all role denials, loading/
    success/empty/error states, RTL/keyboard/resize, screenshots, owner sign-off.
13. **Product-owner input:** Verify demo prices/equipment/preparation content and
    approve the final demonstrated scenario/data.
14. **Size:** Large.
15. **Risk:** High because it exposes cross-system integration defects.

### Task 32 — Submission Documentation, Windows Packaging, and Demo Materials

1. **Goal:** Make the verified product reproducible, Windows-usable, and
   assessable.
2. **Why required:** Setup and PIV documents exist but are distributed and do
   not yet form a final submission package.
3. **Evidence:** README has evolving task-era validation; no final demo script,
   release checklist, consolidated API/database/setup guide, or screenshot set.
4. **User-visible outcome:** A reviewer can install, start, understand, and
   demonstrate the project without source changes or tribal knowledge.
5. **Main scope:** Clean-checkout startup verification; a simple Windows
   launcher or documented one-command start flow; secret-free environment
   examples; stable relative paths; Ollama/model startup and readiness
   instructions; demo credentials; approved screenshots; architecture diagrams;
   requirements traceability; API/runtime/database guide; demo script and
   materials; test matrix; known limitations; credential/artifact checklist;
   Git/PIV evidence; and release commit/tag instructions. A PyInstaller
   executable is optional only when stable and justified; a fragile installer
   is not required for appearance.
6. **Out of scope:** New workflows, speculative production operations, a fragile
   installer, or rewriting historical PIV evidence.
7. **Roles affected:** Reviewer/operator and all demonstrated roles.
8. **Architecture:** Documentation and optional non-invasive packaging scripts.
9. **Course requirements:** Git, PIV, Windows, architecture evidence, submission
   readiness.
10. **Dependencies:** Task 31 acceptance evidence.
11. **Automated acceptance:** Documentation links/commands, secret/generated
    artifact scans, clean checkout setup verification, full tests.
12. **Manual acceptance:** A second person follows the guide on the target
    machine and completes the demo; owner approves screenshots/branding.
13. **Product-owner input:** Approve public screenshots, organization assets,
    content, and known-limitations wording.
14. **Size:** Medium.
15. **Risk:** Medium.

### Task 33 — Final Architecture, Security, Product, UX, and Submission Audit

1. **Goal:** Perform the final independent release gate; this is the final task.
2. **Why required:** Submission cannot rely on accumulated task claims; the
   actual final tree and live product must be audited.
3. **Evidence:** Every earlier task can introduce regression or documentation
   drift; final DoD requires no critical/high defect.
4. **User-visible outcome:** No new behavior; an evidence-backed release
   recommendation and final defect list, if any.
5. **Main scope:** PRD/traceability audit, all roles/permissions, MVP/passive
   Views, CQRS/Event Sourcing/replay, Gateways, secrets/logging, DB isolation,
   RAG grounding, Docker/runtime, UI/accessibility, tests, live scenario,
   documentation, Git cleanliness, and submission artifact review.
6. **Out of scope:** Implementing fixes during the audit, new features,
   refactoring, or expanding MVP scope.
7. **Roles affected:** All.
8. **Architecture:** Entire repository, read-only audit.
9. **Course requirements:** All.
10. **Dependencies:** Tasks 20–32 complete and approved.
11. **Automated acceptance:** Every documented suite/scan passes from a clean
    tree and clean setup; coverage gaps are explicitly assessed.
12. **Manual acceptance:** Repeat the final demo and visual/accessibility review
    on the course machine; compare screenshots and documented expected results.
13. **Product-owner input:** Final product and submission approval.
14. **Size:** Medium.
15. **Risk:** Low implementation risk; high release-gate significance.

## 13. Dependency map

```text
Task 19 baseline
  |
  +--> Task 20 Neutral UX/Request-State Foundations
          |
          +--> Task 21 User Administration
                  |
                  +--> Task 22 Runtime/Ollama Readiness
                          |
                          +--> Task 23 Reliability/Security/Observability
                                  |
                                  +--> Task 24 Branding Checkpoint
                                          |
                                          +--> Task 25 Shell/Dashboard
                                                  |
                                                  +--> Task 26 Manager UX
                                                          |
                                                          +--> Task 27 Role UX
                                                                  |
                                                                  +--> Task 28 AI/Knowledge UX
                                                                          |
                                                                          +--> Task 29 Responsiveness Closure
  Product-owner/course external-service decision                                  |
          +---------------------------------> Task 30 Gateway Closure --------------+
                                                                                   |
                                                                                   v
                                                              Task 31 End-to-End Acceptance
                                                                                   |
                                                              Task 32 Windows Packaging
                                                                                   |
                                                              Task 33 Final Audit (final task)
```

Task 20 establishes the neutral structures and request-state contracts used by
all later screens. Task 23 must finish before screen-by-screen error-state
polish. Task 22 must finish before Task 28 and final AI acceptance. Task 24
blocks all final branded visual work but does not block Task 20. Task 30 may
proceed after its mandatory decision, but must close before Task 31. Task 33 is
the final roadmap task and a read-only release gate.

## 14. Recommended execution sequence

1. Approve and specify Task 20 to establish neutral UX, accessibility, and
   request-state foundations before adding another screen.
2. Implement Task 21 user administration on those foundations.
3. Complete Task 22 runtime readiness and Task 23 reliability/security
   contracts before broad visual closure.
4. Hold the mandatory Task 24 branding checkpoint; do not guess assets.
5. Apply the approved system in Tasks 25–28, from shared shell/dashboard to
   manager, role, and AI/knowledge experiences.
6. Complete Task 29 application-wide responsiveness after the AI-specific
   concurrency case and shared request-state contracts are established.
7. Resolve external-service compliance in Task 30 as soon as owner/course input
   is available; do not delay the decision until final week.
8. Freeze features and execute Task 31 acceptance.
9. Package only verified behavior and Windows startup in Task 32.
10. Run Task 33 as the final, read-only release gate.

## 15. Branding checkpoint

Task 24 is mandatory before final visual implementation. The product owner must
provide or explicitly state the absence of:

- official logo source files and available variants;
- approved colors with values and usage guidance;
- approved fonts or Hebrew typography guidance;
- real activity images and permission to use them in the demo;
- website and social-media references;
- existing brochures, proposals, signage, or other marketing materials;
- preferred visual tone and audiences;
- restrictions on cropping, recoloring, spacing, or modifying the logo;
- approval for screenshots included in course submission.

Until approval, only neutral temporary styling is allowed and must be labeled
temporary. No AI-generated replacement logo or invented final brand is allowed.

## 16. Manual-review strategy

Every user-visible task includes a mandatory manual checkpoint. The default
protocol is:

1. Start PostgreSQL-backed FastAPI using documented environment configuration.
2. Start Docker/Ollama and verify required models for AI-related tasks.
3. Start the PySide6 desktop application on supported Windows.
4. Log in as every affected role.
5. Execute the success workflow and at least one validation, empty, loading,
   authorization, connection, and server/provider error path where applicable.
6. Verify Hebrew text, RTL alignment, focus order, keyboard operation, minimum
   resolution, resize behavior, scrolling, and table overflow.
7. Confirm sensitive data and forbidden controls are absent.
8. Capture named screenshots with no credentials or private real data.
9. Record actual backend/desktop/Docker versions and commands.
10. Obtain product-owner visual/content approval for branded tasks.

Automated tests complement this protocol; they do not replace it.

## 17. Documentation synchronization and task lifecycle

Every Task 20+ must inspect and update every relevant member of this review set:

- `tasks/<task>.md`;
- `docs/piv/<task>.md`;
- `docs/piv/requirements-traceability.md`;
- `docs/PROJECT-ROADMAP.md`, including the status table;
- `README.md`;
- `ARCHITECTURE.md`;
- `docs/PRD.md` only when an approved product requirement changes;
- runtime/setup documentation when commands, dependencies, models,
  configuration, launch behavior, or environment variables change;
- test counts and automated/manual validation evidence;
- accepted limitations and deferred product-owner/course decisions.

A task is not complete merely because production code and automated tests pass.
Completion requires consistency between implementation, tests, architecture,
traceability, PIV evidence, roadmap status, and manual validation. Historical
task and PIV records must remain honest historical evidence; they must not be
rewritten to pretend that later work existed earlier. Current-state documents
may explain that a later task has closed an earlier deferral.

The standard lifecycle for every remaining task is:

```text
Design
  -> Product-owner/ChatGPT approval
  -> Implementation
  -> Automated validation
  -> ChatGPT audit
  -> Required fixes
  -> Final approval
  -> Manual application review
  -> Documentation synchronization
  -> Commit
  -> Push
  -> Roadmap status update
```

Stages with no required fixes must still record the audit result. Every task
must receive its own clean commit and push after final approval. The roadmap
status table must be updated when approval is granted and after the commit/push,
so planning state and repository state cannot silently diverge.

## 18. Definition of final product completion

The product is functionally complete only when:

- every PRD Must requirement used by the acceptance scenario is demonstrable;
- manager user administration is implemented and secure;
- all three roles complete their intended workflows with server-side isolation;
- booking commands produce immutable events and replay matches projection;
- image and any approved second external service remain behind Gateways;
- Ollama/RAG startup, readiness, grounding, citations, abstention, and failure
  recovery are demonstrable;
- the UI is product-owner-approved, branded with real assets, accessible,
  readable in Hebrew/RTL, and usable at the documented resolution;
- no critical/high defect remains and accepted limitations are documented;
- the full manual acceptance scenario and automated suites pass.

## 19. Definition of submission readiness

Submission readiness additionally requires:

- a clean checkout can be configured and started from documentation without
  editing source code;
- no secret, real private customer data, cache, generated test artifact, or
  temporary provider asset is tracked;
- schema/seed/model/Docker/API/desktop commands are current;
- traceability maps requirements to code, automated tests, manual evidence, and
  PIV records;
- architecture diagrams visibly explain MVP, CQRS, Event Sourcing, projections,
  Gateways, PostgreSQL, Docker/Ollama, and RAG;
- screenshots and demo content are approved for course use;
- the repository has a clean working tree, coherent task commits, and an
  identified release commit/tag;
- Task 33 returns approval.

## 20. Explicitly excluded features

Unless a new PRD decision explicitly promotes them, the remaining roadmap does
not include:

- payments, invoices, tax, accounting, or profitability;
- WhatsApp, SMS, email, calendar, or mobile applications;
- inventory reservation/warehouse or instructor payroll;
- instructor claim/request while the feature remains disabled;
- customer booking creation or approval workflows;
- AI writes, web search, general-knowledge fallback, OCR, PDF/DOCX ingestion,
  reranking, or persistent chat history;
- batch image upload, image editing, primary reordering, or offline image cache;
- cross-module global search, generic report builder, or decorative charts;
- advanced analytics, export, production deployment, autoscaling, backup/DR,
  or a distributed microservice rewrite;
- repository-wide package restructuring or literal `/api/v1` migration unless
  course review makes it mandatory;
- invented branding or replacement of the official logo.

## 21. Open product-owner decisions

1. May a manager reset passwords, and must users always be deactivated rather
   than deleted?
2. What are the official logo variants, colors, fonts, image assets, visual
   tone, and usage restrictions?
3. Which real images and screenshots may appear in the academic submission?
4. Which prices, capacities, equipment lists, and preparation instructions are
   approved, and which remain explicitly demo-only?
5. Which Ollama generation model is supported by the final demonstration
   hardware?
6. Does the course assessor accept Cloudinary as the required domain-relevant
   external service? If not, which single real planning need and provider should
   be approved?
7. Should instructor claiming remain disabled, as currently assumed?
8. Which manager dashboard graph best supports actual daily decisions?
9. What suggested AI questions and proposal-draft disclaimer should be shown?
10. Are any actions exclusive to a future Business Manager versus Office
    Manager? The roadmap retains the current single `manager` role unless this
    is promoted into MVP scope.

## PRD change decision

No PRD change is made with this roadmap. The mandatory user-administration,
runtime, accessibility, AI-cancellation, reliability, observability, dashboard,
branding-sensitive product quality, and final acceptance needs already follow
from existing PRD requirements or release criteria. A second external-service
requirement must not be added to the PRD until product-owner/course approval
determines that Cloudinary is insufficient and selects a genuine use case.
