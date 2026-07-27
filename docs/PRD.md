# Product Requirements Document (PRD)

## Havaya Im Neshama Management System

| Document field | Value |
|---|---|
| Product | Havaya Im Neshama Management System |
| Document type | Product Requirements Document |
| Version | 1.0 |
| Status | Approved baseline for MVP implementation |
| Date | July 22, 2026 |
| Product owner | Havaya Im Neshama management |
| Primary delivery | Desktop application with a cloud-backed API |
| Target release | Academic MVP |

---

## 1. Executive Summary

Havaya Im Neshama is an experiential-activity business that manages customers, activity offerings, bookings, instructors, preparation information, equipment lists, and pricing. The current operational information is distributed across conversations, documents, and manual processes.

The proposed product is a role-based desktop management system that centralizes these workflows and provides a retrieval-augmented AI assistant grounded in approved business knowledge. The system will support managers and office staff in daily administration, instructors in viewing and claiming relevant events, and customers in viewing the activity catalog and their own bookings.

The MVP will be implemented as a PySide6 desktop client connected to a FastAPI backend and a Supabase PostgreSQL database. Booking changes will use Event Sourcing with CQRS: immutable booking events are the source of truth, while a booking projection supports efficient reads. Cloudinary will be accessed through a Gateway for activity images. A local Ollama service running in Docker will support the RAG assistant.

## 2. Problem Statement

The business currently lacks one authoritative system for operational data. This creates several problems:

- Customer, booking, instructor, pricing, and equipment information is fragmented.
- Staff cannot reliably view the current status and complete history of a booking in one place.
- Instructor assignment and visibility of unassigned events require manual coordination.
- Customers lack a self-service view of their bookings and the activity catalog.
- Repetitive questions about suitability, pricing, preparation, and equipment consume staff time.
- Business knowledge is difficult to reuse consistently when preparing proposals or events.

## 3. Product Vision

Create a single, reliable operational workspace that reduces manual coordination, preserves a complete booking history, and allows users to retrieve approved business knowledge through a secure, role-aware AI assistant.

## 4. Goals and Success Metrics

### 4.1 Product Goals

1. Centralize customers, activities, bookings, instructors, prices, images, and preparation information.
2. Preserve every meaningful booking change as an immutable domain event.
3. Give each role access only to the information and actions required for its work.
4. Enable instructors to see assigned events and future events that require an instructor.
5. Enable customers to view the catalog, their own bookings, and use the AI assistant.
6. Answer common business questions using only approved internal knowledge.
7. Demonstrate the architectural patterns required by the course in a coherent product.

### 4.2 MVP Success Metrics

| Metric | MVP target |
|---|---|
| Core workflow completion | A manager can create a customer, activity, and booking, assign an instructor, change status, and view the resulting history end to end |
| Event completeness | 100% of supported booking mutations create a persisted domain event |
| Projection consistency | Booking read state matches replayed events in all automated tests |
| Authorization | All tested cross-role unauthorized operations are rejected |
| AI grounding | The assistant cites or identifies the internal source used for every knowledge-based answer |
| AI safety | The assistant does not mutate operational data in the MVP |
| Image integration | A manager can upload and display at least one activity image through the external-service Gateway |
| Reliability | No critical or high-severity defects in the demonstrated workflows |

## 5. Users and Roles

| Role | Primary needs | MVP permissions |
|---|---|---|
| Business Manager | Full business oversight and configuration | Full CRUD access; user and role management; all bookings, events, reports, and AI functions |
| Office Manager | Daily customer and booking administration | Same operational access as Business Manager in the MVP; finer separation is deferred |
| Instructor | Understand upcoming work and find available assignments | View own assigned bookings; view future bookings marked as requiring an instructor; request or accept an assignment if enabled by configuration |
| Customer | Review offerings and personal orders | View public activity catalog; view only own bookings; use customer-permitted AI functions |

### 5.1 Authorization Principles

- Access is denied by default and granted by role.
- Server-side authorization is authoritative; hiding a desktop control is not sufficient security.
- A customer may never read another customer's record or booking.
- An instructor may not edit commercial fields such as price or customer details.
- The MVP may use a simplified login, but passwords must never be stored in plaintext.

### 5.2 Course Demonstration Roles

For the academic demo, the system shall include at least three seeded users:

| Demo role | Purpose in demo |
|---|---|
| Manager user | Demonstrates full data entry, booking commands, image upload, dashboard, and event history |
| Instructor user | Demonstrates role-filtered desktop module and restricted operational view |
| Customer user | Demonstrates ownership filtering, catalog access, and customer-scoped RAG |

These users are required so the submission can prove authentication, authorization, search, data entry, and role-specific screens during one short demonstration.

## 6. Assumptions and Constraints

### 6.1 Assumptions

- The first release is an academic MVP, not a production deployment.
- A stable internet connection is required for the API, cloud database, and image service.
- Ollama is available locally through Docker on the demonstration environment.
- Hebrew is the primary content language; the UI should support right-to-left presentation. Technical identifiers and documentation may remain in English.
- Example prices and equipment lists are demonstration seed data until approved by the business owner.

### 6.2 Constraints

- Desktop UI: Python and PySide6.
- Backend: FastAPI.
- Cloud database: Supabase PostgreSQL.
- Local AI runtime: Ollama in Docker.
- Activity images: Cloudinary through an application-owned Gateway abstraction.
- Required architectural concepts: MVP presentation pattern, modular front-end boundaries, CQRS, Event Sourcing, Gateway, cloud database, Docker, and RAG.
- The implementation window is short; scope must remain limited to the workflows explicitly included in this document.
- Code shall be managed in a GitHub repository or equivalent Git-based repository.
- Development artifacts produced during the PIV workflow shall be saved under project documentation so the course requirement is visible.

## 7. Scope

### 7.1 In Scope for the MVP

- Authentication and role-based authorization.
- Customer management.
- Activity catalog management.
- Activity image upload and display.
- Booking creation, viewing, and supported updates.
- Instructor management and booking assignment.
- Event-sourced booking history and replayable booking state.
- Role-specific dashboard.
- Customer view of personal bookings and the activity catalog.
- RAG-based AI assistant for recommendations, preparation, pricing, equipment, and proposal drafting.
- Basic operational filters and summary counts.
- Automated tests for core domain behavior, permissions, APIs, and event replay.

### 7.2 Out of Scope for the MVP

- Payments, invoices, or accounting integrations.
- Actual WhatsApp, SMS, or email delivery.
- Advanced inventory and warehouse management.
- Route planning or vehicle management.
- Advanced calendar scheduling.
- Native mobile application.
- AI-initiated writes to customers, bookings, prices, or assignments.
- Automated web ingestion into the AI knowledge base.
- Complex approval workflows or fine-grained differences between business and office managers.
- Production-grade high availability, disaster recovery, and autoscaling.

## 8. Core User Journeys

### 8.1 Create and Manage a Booking

1. A manager signs in.
2. The manager selects or creates a customer.
3. The manager selects an activity and enters event details.
4. The system validates required fields and creates a `BookingCreated` event.
5. The booking projection is updated and shown in the booking list.
6. The manager changes the date, price, status, notes, or instructor assignment.
7. Each supported change appends an event and updates the projection.
8. The manager opens the booking history and sees the chronological changes, actor, and timestamp.

### 8.2 Instructor Views Work

1. An instructor signs in.
2. The dashboard shows the instructor's upcoming assigned events.
3. A separate list shows future confirmed events that require an instructor.
4. The instructor opens a permitted event to view operational details and equipment guidance.
5. If assignment claiming is enabled, the instructor requests or accepts the assignment; otherwise the manager assigns the instructor.

### 8.3 Customer Self-Service

1. A customer signs in.
2. The customer browses the activity catalog.
3. The customer views only bookings linked to the same customer account.
4. The customer asks the AI assistant for an activity recommendation based on season, audience, participant count, and budget.
5. The assistant responds from approved knowledge and identifies the supporting source.

### 8.4 Ask for Event Preparation Information

1. An authorized user opens the AI assistant.
2. The user asks for the equipment list or preparation instructions for a named activity.
3. The backend retrieves relevant approved knowledge chunks.
4. The model generates an answer limited to the retrieved context.
5. The UI presents the answer and its source references.

## 9. Functional Requirements

Requirements use the priority labels Must, Should, and Could.

### 9.1 Authentication and Authorization

| ID | Requirement | Priority | Acceptance criterion |
|---|---|---|---|
| FR-AUTH-01 | The system shall authenticate registered users. | Must | Valid credentials create a session/token; invalid credentials return a generic error |
| FR-AUTH-02 | The backend shall authorize every protected operation by role and resource ownership. | Must | Unauthorized requests return HTTP 403; unauthenticated requests return HTTP 401 |
| FR-AUTH-03 | The desktop client shall show navigation appropriate to the signed-in role. | Must | Each role sees only its permitted modules in role-based UI tests |
| FR-AUTH-04 | Customers shall access only their own bookings. | Must | A customer requesting another customer's booking receives 403 or 404 without data leakage |

### 9.2 Customer Management

| ID | Requirement | Priority | Acceptance criterion |
|---|---|---|---|
| FR-CUS-01 | Managers shall create, view, update, search, and deactivate customers. | Must | CRUD and deactivation work through UI and API |
| FR-CUS-02 | A customer record shall contain name, phone, optional email, contact role, city, institution type, institution name, notes, active status, and timestamps. | Must | Required fields are validated and persisted |
| FR-CUS-03 | The system shall search customers by name, phone, institution, or city. | Should | Matching records are returned using at least one supported filter |
| FR-CUS-04 | The system shall warn about a likely duplicate phone or email. | Should | Duplicate normalized values produce a visible warning before save |

### 9.3 Activity Management

| ID | Requirement | Priority | Acceptance criterion |
|---|---|---|---|
| FR-ACT-01 | Managers shall create, view, update, search, and deactivate activities. | Must | Activity CRUD works end to end |
| FR-ACT-02 | An activity shall store name, description, target audience, duration, recommended capacity, pricing rule, required equipment, preparation notes, season/tags, and active status. | Must | Data is persisted and displayed in the catalog |
| FR-ACT-03 | Managers shall upload an activity image through the image Gateway. | Must | Upload returns an external asset identifier and secure URL; the image displays in the catalog |
| FR-ACT-04 | Customers and instructors shall have read-only access to permitted activity information. | Must | Mutation controls are absent and mutation APIs reject their roles |

### 9.4 Booking Management and Event Sourcing

| ID | Requirement | Priority | Acceptance criterion |
|---|---|---|---|
| FR-BKG-01 | Managers shall create a booking with customer, activity, event date/time, location, participant count, agreed price, status, instructor requirement, and notes. | Must | A valid command appends `BookingCreated` and produces a readable booking projection |
| FR-BKG-02 | The system shall support booking statuses `NEW`, `CONFIRMED`, `COMPLETED`, and `CANCELLED`. | Must | Invalid transitions are rejected by domain rules |
| FR-BKG-03 | Supported changes shall append immutable domain events rather than overwrite event history. | Must | Event rows cannot be updated or deleted through application APIs |
| FR-BKG-04 | The system shall show a chronological booking history. | Must | UI displays event type, timestamp, actor, and human-readable change summary |
| FR-BKG-05 | Booking state shall be reconstructable by replaying its ordered event stream. | Must | Automated replay tests reproduce the stored projection |
| FR-BKG-06 | Commands shall use optimistic concurrency. | Must | A stale expected version is rejected with a conflict response |
| FR-BKG-07 | Managers shall filter bookings by date, status, customer, activity, and instructor. | Should | Combined filters return correct results |

#### Required Booking Events

| Event | Minimum payload |
|---|---|
| `BookingCreated` | Complete initial booking data |
| `BookingDateChanged` | Previous and new date/time |
| `BookingStatusChanged` | Previous and new status |
| `BookingPriceChanged` | Previous and new agreed price |
| `BookingLocationChanged` | Previous and new location |
| `BookingParticipantCountChanged` | Previous and new participant count |
| `BookingGuideAssigned` | Instructor identifier |
| `BookingGuideRemoved` | Instructor identifier |
| `BookingNotesUpdated` | New notes or an approved change representation |
| `BookingCancelled` | Cancellation reason when supplied |

`booking_events` is the append-only source of truth. `bookings` is a rebuildable read projection and must not be treated as the authoritative history.

### 9.5 Instructor Management

| ID | Requirement | Priority | Acceptance criterion |
|---|---|---|---|
| FR-INS-01 | Managers shall create, update, view, and deactivate instructor profiles. | Must | Instructor records persist and inactive instructors cannot receive new assignments |
| FR-INS-02 | Instructors shall view their upcoming assigned bookings. | Must | The list contains only events assigned to the signed-in instructor |
| FR-INS-03 | Instructors shall view future bookings that are confirmed and require an instructor. | Must | Eligible events appear without exposing restricted commercial/customer data |
| FR-INS-04 | Managers shall assign and remove instructors from a booking. | Must | Each mutation creates the corresponding booking event |
| FR-INS-05 | Instructors may claim/request an open assignment if the feature flag is enabled. | Could | A successful action creates an auditable assignment event or request record |

### 9.6 Dashboard

| ID | Requirement | Priority | Acceptance criterion |
|---|---|---|---|
| FR-DASH-01 | Managers shall see counts of upcoming bookings by status and unassigned events. | Must | Counts match query results for the same filters |
| FR-DASH-02 | Instructors shall see assigned upcoming events and eligible open events. | Must | Dashboard respects instructor permissions |
| FR-DASH-03 | Customers shall see their upcoming bookings and recent statuses. | Must | No other customer's data is shown |

### 9.7 AI Assistant and RAG

| ID | Requirement | Priority | Acceptance criterion |
|---|---|---|---|
| FR-AI-01 | The assistant shall recommend activities using season, audience/age group, participant count, and budget supplied by the user. | Must | Answer uses available catalog and pricing knowledge and explains relevant constraints |
| FR-AI-02 | The assistant shall answer questions about prices, equipment, and preparation. | Must | Answer is grounded in retrieved approved knowledge and identifies sources |
| FR-AI-03 | The assistant shall draft a proposal for staff to copy and review. | Must | Output is clearly a draft and does not send a message or create a booking |
| FR-AI-04 | The assistant shall state that information is unavailable when retrieval does not provide sufficient evidence. | Must | No unsupported price or equipment detail is invented in a no-context test |
| FR-AI-05 | The assistant shall apply role-aware retrieval. | Must | Customer queries cannot retrieve internal-only documents or operational notes |
| FR-AI-06 | The MVP assistant shall be read-only. | Must | No AI endpoint can execute booking/customer mutations |
| FR-AI-07 | Managers shall be able to add or update approved knowledge documents through a controlled ingestion flow. | Should | A valid document is chunked, embedded, indexed, and retrievable |

## 10. Business Rules

1. A booking must reference one active customer and one active activity.
2. Event date/time, participant count, and agreed price are required when a booking is created.
3. Participant count must be a positive integer; agreed price must be non-negative.
4. A completed or cancelled booking cannot be returned to an earlier status without a future privileged correction workflow; that workflow is outside the MVP.
5. A cancelled booking cannot receive a new instructor assignment.
6. Only active instructors may receive new assignments.
7. An event is considered to require an instructor when `requires_instructor = true` and it has fewer than the required number of active assignments.
8. Catalog base prices are guidance. A booking stores the agreed price as a historical commercial fact.
9. Demo pricing and equipment content must be labeled as unverified until approved.
10. All timestamps are stored in UTC and displayed in the user's configured local timezone.

## 11. Information Architecture and Screens

| Module / screen | Main capabilities | Roles |
|---|---|---|
| Sign In | Authenticate and enter role-specific workspace | All |
| Dashboard | Role-specific summaries and shortcuts | All |
| Customers | List, search, create, edit, deactivate | Managers |
| Activities | Catalog, details, pricing, equipment, image | Managers: edit; others: view |
| Bookings | List, filters, create, and permitted views | All, role-filtered |
| Booking Details | Current state, instructor assignments, event history | Managers; restricted views for instructor/customer |
| Instructors | Profiles and assignment management | Managers |
| Open Events | Future events that require instructors | Instructors, managers |
| AI Assistant | Grounded chat and proposal drafts | All, role-filtered |
| Knowledge Sources | Approved RAG content ingestion/status | Managers |
| User Administration | Users, roles, active status | Business Manager |

The desktop UI shall use reusable PySide6 widgets, layouts, signals, and slots. Each business module will have a clear MVP boundary consisting of a View, Presenter, API client/service, and models. This modular structure satisfies the intended microfrontend-style separation within a single desktop executable without introducing independently deployed front ends.

### 11.1 Desktop Microfrontends in PySide6

Because this is a desktop application, "Microfrontends" will be implemented as modular feature packages inside one PySide6 executable. Each module owns its screens, presenter, local models, and API client boundary.

| UI module | Suggested package | Main responsibility |
|---|---|---|
| Authentication | `desktop_client/features/auth` | Login and current-user state |
| Dashboard | `desktop_client/features/dashboard` | Role-specific cards, tables, and charts |
| Customers | `desktop_client/features/customers` | Customer search, form, edit, deactivate |
| Activities | `desktop_client/features/activities` | Catalog, equipment, pricing, image upload |
| Bookings | `desktop_client/features/bookings` | Booking list, commands, details, event history |
| Instructors | `desktop_client/features/instructors` | Instructor list, profile, assignment view |
| AI Assistant | `desktop_client/features/ai_assistant` | RAG chat UI, source display, loading state |
| Shell/navigation | `desktop_client/shell` | Main window, routing, role-based menu |

Each module shall expose a small registration function or navigation descriptor, so the main shell can compose the application without knowing the internal implementation of every screen.

### 11.2 Required Tables and Charts

To satisfy the course requirement for graph/table presentation, the MVP shall include:

| Requirement | MVP implementation |
|---|---|
| Search results table | Customer list, activity list, and booking list use sortable/filterable tables |
| Details screen | Selecting one row opens a full details view |
| Dashboard chart | Manager dashboard shows a booking-status chart using QtCharts where practical |
| Operational table | Manager dashboard shows upcoming bookings requiring an instructor |
| Role-filtered table | Instructor dashboard shows assigned events and open events |

If QtCharts creates installation difficulty in the demonstration environment, a PySide6 table-based fallback may be used, but the preferred implementation is a small chart for bookings by status.

## 12. Data Requirements

### 12.1 Core Entities

| Entity | Purpose | Key fields |
|---|---|---|
| `users` | Authentication and role identity | id, email/username, password_hash or auth_provider_id, role, active, customer_id, instructor_id, timestamps |
| `customers` | Customer and institution CRM data | id, name, phone, email, contact_role, city, institution_type, institution_name, notes, active, timestamps |
| `instructors` | Instructor profile | id, name, phone, email, service_area, notes, active, timestamps |
| `activities` | Activity catalog and commercial guidance | id, name, description, audience, duration_minutes, min/max_participants, pricing_rule, preparation_notes, season_tags, active, timestamps |
| `activity_images` | External image metadata | id, activity_id, provider, asset_id, secure_url, alt_text, is_primary, created_at |
| `activity_equipment` | Structured equipment lists | id, activity_id, item_name, quantity_rule, notes, required |
| `booking_events` | Append-only booking event store | event_id, booking_id/aggregate_id, aggregate_version, event_type, event_data JSONB, actor_user_id, occurred_at, correlation_id |
| `bookings` | Rebuildable current-state projection | id, customer_id, activity_id, event_at, city, venue, participant_count, agreed_price, status, requires_instructor, notes, version, timestamps |
| `booking_instructors` | Read projection for current activity assignments | booking_activity_id, instructor_id, assigned_at, active |
| `knowledge_documents` | Approved RAG source registry | id, title, audience_scope, status, source_type, checksum, timestamps |
| `knowledge_chunks` | Searchable RAG chunks/embeddings | id, document_id, chunk_text, embedding/vector reference, metadata |

### 12.2 Integrity Requirements

- `booking_events` shall enforce a unique `(aggregate_id, aggregate_version)` constraint.
- Event payloads shall include an explicit schema version.
- Referential integrity shall be enforced for operational projections.
- Application code shall provide no general update/delete path for stored domain events.
- Personally identifiable information shall not be copied into event payloads unless necessary; stable identifiers are preferred.
- Database migrations and seed data shall be version controlled.

## 13. Architecture

### 13.1 Logical Components

| Layer | Technology | Responsibility |
|---|---|---|
| Desktop presentation | PySide6 | RTL user interface, navigation, forms, state display |
| Presentation pattern | MVP | Views render; Presenters coordinate user actions; domain/network logic stays outside widgets |
| API | FastAPI | Authentication, authorization, validation, commands, queries, AI orchestration |
| Command side | CQRS application services | Validate commands, load/replay aggregates, append events, trigger projection updates |
| Query side | CQRS query services | Read optimized PostgreSQL projections for lists, details, and dashboards |
| Event store | PostgreSQL `booking_events` | Immutable ordered booking event streams |
| Read models | PostgreSQL projections | Current booking and assignment state |
| Image integration | Cloudinary Gateway | Isolate provider SDK and translate provider failures |
| AI service | Ollama in Docker | Local language-model inference |
| Retrieval | RAG service and vector index | Ingest, chunk, embed, retrieve, and cite approved knowledge |

### 13.2 Architectural Decisions

- The MVP is a modular monolith, not a distributed microservice system. This reduces operational risk while preserving clean module boundaries.
- CQRS separates mutation workflows from optimized read workflows, but both may run in one FastAPI deployment.
- Event Sourcing applies to the booking aggregate only. Other entities use conventional CRUD because event sourcing them would not add enough MVP value.
- The Cloudinary Gateway exposes application-level operations such as `upload_activity_image` and `delete_activity_image`; business code does not import the provider SDK directly.
- External calls shall use timeouts, bounded retries where safe, and meaningful error translation.
- The AI subsystem is isolated behind an interface so the selected Ollama model or embedding implementation can change without altering UI code.

### 13.3 Backend MVC and CQRS Mapping

The FastAPI backend shall combine MVC-style organization with CQRS command/query separation:

| Concept | Backend location | Responsibility |
|---|---|---|
| Controller | `backend/app/api/v1/routers` | HTTP routes, request parsing, response mapping |
| Model / Domain | `backend/app/domain` | Business entities, booking aggregate, rules, events |
| View Model / DTO | `backend/app/schemas` | Pydantic request and response models |
| Command handlers | `backend/app/application/commands` | Mutating use cases such as create booking or assign instructor |
| Query handlers | `backend/app/application/queries` | Read-only use cases such as dashboard and booking history |
| Repositories | `backend/app/infrastructure/repositories` | Database access for entities, events, and projections |
| Gateways | `backend/app/infrastructure/gateways` | Cloudinary and future external provider adapters |

This mapping keeps the course's MVC/CQRS requirement explicit while preserving a practical FastAPI project structure.

### 13.4 Recommended Project Structure

The implementation should be organized as follows:

```text
havaya-im-neshama/
├── docs/
│   ├── PRD.md
│   ├── architecture.md
│   ├── api.md
│   ├── database.md
│   ├── setup.md
│   └── piv/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── application/
│   │   ├── domain/
│   │   ├── infrastructure/
│   │   └── schemas/
│   ├── tests/
│   └── requirements.txt
├── desktop_client/
│   ├── app/
│   ├── shell/
│   ├── features/
│   ├── shared/
│   └── tests/
├── rag/
│   ├── ingestion/
│   ├── retrieval/
│   └── knowledge_base/
├── docker/
│   └── docker-compose.yml
├── migrations/
└── README.md
```

`docs/PRD.md` is the intended final location of this document inside the repository.

## 14. API Requirements

The API shall be versioned under `/api/v1`. Exact endpoint naming may change during design, but the following capabilities are required:

- `/auth/login` and current-user retrieval.
- CRUD/search endpoints for customers, activities, and instructors.
- Booking command endpoints for creation and supported mutations.
- Booking query endpoints for lists, details, history, open assignments, and dashboards.
- Image upload endpoint that delegates to the Gateway.
- AI chat endpoint and controlled knowledge-ingestion endpoints.

Command requests shall support an idempotency key where duplicate submission is plausible. Booking mutation commands shall carry the expected aggregate version. Errors shall use a consistent response format containing an error code, safe message, and correlation identifier.

## 15. Non-Functional Requirements

| ID | Area | Requirement |
|---|---|---|
| NFR-01 | Usability | The primary Hebrew UI shall support RTL layout, clear validation, keyboard navigation, and readable empty/error/loading states |
| NFR-02 | Performance | Under normal MVP load, 95% of non-AI API reads should complete within 1 second, excluding network variability |
| NFR-03 | AI latency | The UI shall show progress and allow cancellation while local AI generation is running; no fixed latency guarantee is required for the academic environment |
| NFR-04 | Security | Credentials and API secrets shall be provided through environment variables or secret management and excluded from source control |
| NFR-05 | Privacy | Logs shall avoid passwords, tokens, and unnecessary customer personal data |
| NFR-06 | Reliability | Event append and projection update shall be transactionally consistent where implemented synchronously, or recoverable through an idempotent projector |
| NFR-07 | Maintainability | Modules shall have explicit interfaces, typed models, documented setup, and automated tests for core business rules |
| NFR-08 | Observability | Backend logs shall include timestamp, severity, operation, user/actor identifier where appropriate, and correlation ID |
| NFR-09 | Accessibility | Forms shall have labels, logical focus order, sufficient contrast, and usable error text |
| NFR-10 | Portability | The desktop client shall run on the course's supported Windows environment; containerized AI services shall start through documented Docker commands |

## 16. AI and Knowledge Requirements

### 16.1 Approved Knowledge Categories

- Activity catalog.
- Approved price list.
- Activity equipment lists.
- Preparation procedures.
- Business description and service rules.
- Approved proposal templates.

### 16.2 Retrieval and Answer Policy

- Documents are assigned an audience scope such as `CUSTOMER`, `INSTRUCTOR`, or `INTERNAL`.
- Retrieval filters by the signed-in user's permitted scope before generation.
- Answers must be grounded in retrieved content and display source titles or references.
- When sources conflict, the assistant shall report the conflict instead of silently choosing one.
- When evidence is insufficient, the assistant shall say so and recommend human review.
- Retrieved text and user input are untrusted data; they shall not override system instructions or authorization rules.
- AI output is advisory and must be reviewed before being sent to a customer.

## 17. Seed Data for Demonstration

The following records are placeholders for development and demonstration. They are not approved commercial commitments.

| Activity | Illustrative pricing rule |
|---|---|
| Catch the Light (`Tfos Et HaOr`) | ILS 1,200 for up to 60 participants; ILS 15 per additional participant |
| Code Race | ILS 1,500 for up to 80 participants |
| Sign Quiz | ILS 900 per session |
| Personalized Bag Workshop | ILS 32 per participant; ILS 1,200 minimum |
| Personalized Sukkah Canvas Decoration | ILS 34 per participant up to 100; ILS 28 above 100 |
| Hanukkah Menorah Workshop | ILS 38 per participant; ILS 1,400 minimum |
| Following the Heritage | ILS 1,800 per seated family activity |

Initial equipment examples include charged game units, group signs, chargers, spare batteries, instruction sheets, and backup equipment for Catch the Light; blank bags, print materials, press equipment, decorating materials, work surfaces, and packaging for the bag workshop. All entries require business-owner verification before non-demo use.

## 18. Analytics and Reporting

The MVP dashboard will provide operational summaries only:

- Upcoming bookings by status.
- Bookings requiring an instructor.
- Bookings assigned to the signed-in instructor.
- Customer's upcoming bookings.
- Activity and customer counts.

Revenue analytics, profitability, tax reporting, and long-term trend analysis are deferred.

## 19. Error Handling and Edge Cases

- Duplicate command submission must not create duplicate bookings or duplicate events when the same idempotency key is reused.
- Concurrent booking edits must reject the stale writer rather than overwrite a newer event.
- If an image upload succeeds but database persistence fails, the system shall report the failure and attempt documented cleanup or mark the asset for cleanup.
- If Cloudinary is unavailable, users can continue managing textual activity data and retry the image operation later.
- If Ollama is unavailable, the AI module shall show a clear unavailable state without blocking core management workflows.
- If no knowledge chunk meets the retrieval threshold, the assistant shall not invent an answer.
- Deactivated customers, activities, or instructors remain visible on historical bookings.

## 20. Validation and Test Strategy

### 20.1 Required Automated Tests

- Domain tests for each booking event and status transition.
- Replay tests proving that the event stream reconstructs booking state.
- Optimistic-concurrency tests.
- API validation and authorization tests for all roles.
- Customer data-isolation tests.
- Repository and projection tests against a test database.
- Gateway contract tests with the external provider mocked.
- RAG tests for grounded answers, insufficient-context behavior, and audience filtering.
- Presenter tests for critical UI workflows where practical.

### 20.2 Required Manual Acceptance Scenario

The demonstration shall show this complete scenario:

1. Sign in as a manager.
2. Create a customer and an activity with an image.
3. Create a booking.
4. Change its date, price, and status.
5. Assign an instructor.
6. Show the booking's complete event history.
7. Sign in as the instructor and view the assigned booking.
8. Sign in as the customer and view only that customer's booking and the catalog.
9. Ask the AI assistant for the activity's equipment and a proposal draft, with source references.

## 21. Delivery Approach: PIV Loop

Implementation work will follow a Plan–Implement–Validate loop at the level of small, testable tickets:

1. **Plan:** define one bounded task, relevant context, constraints, acceptance criteria, and tests.
2. **Implement:** make the smallest coherent change that satisfies the ticket.
3. **Validate:** run tests, check integration and permissions, review code quality/security, and compare the result with the acceptance criteria.
4. If validation fails, revise the plan using the observed failure and repeat.

Recommended implementation increments:

1. Project skeleton, configuration, and health check.
2. Database migrations and seed data.
3. Authentication and RBAC.
4. Customer and activity modules.
5. Cloudinary Gateway and activity images.
6. Booking aggregate, event store, commands, and projector.
7. Booking queries, history, instructors, and dashboards.
8. PySide6 screens and role-based navigation.
9. Ollama/RAG ingestion, retrieval, citations, and role filtering.
10. End-to-end validation, documentation, and demonstration data.

### 21.1 Required PIV Artifacts

For each implementation increment, the repository shall contain a short PIV note under `docs/piv/`.

Recommended format:

```text
docs/piv/
├── 01-project-setup.md
├── 02-auth-rbac.md
├── 03-customers.md
├── 04-activities.md
├── 05-cloudinary-gateway.md
├── 06-bookings-event-sourcing.md
├── 07-dashboard-and-instructors.md
├── 08-desktop-ui.md
├── 09-rag-ai-assistant.md
└── 10-final-validation.md
```

Each file should include:

- Plan: what will be built and which requirements it satisfies.
- Implement: files/modules changed and main design decision.
- Validate: tests/manual checks and result.

### 21.2 GitHub Workflow

The code shall be maintained in a GitHub repository or equivalent Git repository. Commits should be small and aligned with the PIV increments. The repository shall include:

- Source code for backend, desktop client, RAG, Docker, and migrations.
- Documentation under `docs/`.
- Setup instructions in `README.md`.
- `.env.example` without real secrets.
- Test instructions.
- Final demo scenario.

## 22. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Scope is too large for the academic schedule | Incomplete core workflows | Enforce Must/Should/Could priorities; complete the manager booking journey before optional features |
| Event Sourcing is implemented as a simple audit log | Course requirement not truly met | Make events authoritative, add versioning/replay tests, and treat `bookings` as a projection |
| Desktop “microfrontends” are over-engineered | Lost delivery time | Use modular feature packages inside one executable, with explicit interfaces and independent Presenters |
| Local AI is slow or unavailable | AI demo failure | Keep AI isolated, provide readiness checks, use a small supported model, and keep core workflows independent |
| RAG produces unsupported answers | Incorrect business guidance | Require retrieval grounding, source display, confidence threshold, and abstention behavior |
| Demo prices are mistaken for official prices | Commercial error | Mark seed data as unverified and require owner approval before real use |
| External image service fails | Broken catalog workflow | Use Gateway abstraction, timeouts, safe retry, and graceful degraded behavior |

## 23. Release Criteria / Definition of Done

The MVP is ready for submission when:

- All Must requirements used in the acceptance scenario are implemented.
- The end-to-end manual acceptance scenario passes.
- Required automated tests pass in a clean environment.
- Event replay reconstructs every demonstrated booking accurately.
- Role and ownership tests show no unauthorized data access.
- The application starts using documented setup instructions without source-code changes.
- Secrets are absent from the repository.
- Database schema, seed instructions, Docker setup, and system architecture are documented.
- Known limitations and unverified seed data are clearly listed.
- No critical or high-severity defects remain open.

## 24. Future Enhancements

- Online payment and invoicing.
- WhatsApp and email integrations.
- Advanced inventory and equipment checkout.
- Instructor availability and automated matching.
- Calendar view and scheduling conflict detection.
- Customer booking requests and approval workflow.
- AI-assisted actions with explicit confirmation and audit events.
- Revenue, profitability, and customer-retention analytics.
- Mobile client.
- Production deployment, backups, monitoring, and disaster recovery.

## 25. Open Decisions

These decisions do not block the MVP baseline but must be resolved before production use:

1. Which actions, if any, are exclusive to the Business Manager rather than the Office Manager?
2. Can instructors directly claim open events, or can they only request assignment?
3. What are the approved prices, capacity limits, equipment lists, and preparation procedures?
4. Which Ollama chat and embedding models are supported by the demonstration hardware?
5. Will Supabase Auth be used, or will authentication be implemented by the FastAPI application?
6. What information may instructors see about customers and agreed prices?
7. Which documents are customer-visible, instructor-visible, or internal-only?

## 26. Traceability to Course Architecture Requirements

| Course concept | Product implementation | Verification evidence |
|---|---|---|
| Desktop GUI | PySide6 desktop client | Running application and UI tests |
| MVP | View–Presenter separation per feature module | Package structure and Presenter tests |
| Microfrontend/modular UI | Independently bounded desktop feature modules within one executable | Module interfaces and navigation composition |
| FastAPI server | Versioned REST API | OpenAPI documentation and API tests |
| Cloud database | Supabase PostgreSQL | Migrations and configured connection |
| CQRS | Separate booking commands and projection-based queries | Command/query packages and tests |
| Event Sourcing | Booking events as source of truth; replayable projection | Event schema, replay, concurrency tests |
| Gateway | Cloudinary adapter behind application-owned interface | Gateway contract and mock tests |
| Docker | Ollama and supporting local AI services | Docker configuration and setup instructions |
| RAG | Role-filtered retrieval over approved business knowledge | Ingestion/retrieval tests and cited answers |
| AI-assisted workflow | PIV loop applied to implementation tickets | Ticket plans, acceptance criteria, and validation records |

## 27. References

- [MindStudio — PIV Loop: Plan, Implement, Validate](https://www.mindstudio.ai/blog/piv-loop-ai-assisted-software-development)
- [DataCamp — Introduction to PySide6 for Building GUI Applications with Python](https://www.datacamp.com/tutorial/introduction-to-pyside6-for-building-gui-applications-with-python)
- [Code B — Cloud-Native Architecture Patterns and Use Cases](https://code-b.dev/blog/best-cloud-native-architecture-patterns)

---

## Appendix A: Glossary

| Term | Meaning in this product |
|---|---|
| Aggregate | A booking and the rules that govern valid changes to it |
| Command | A request to change system state, such as assigning an instructor |
| CQRS | Separation of state-changing command flows from read-optimized query flows |
| Domain Event | An immutable fact describing a completed business change |
| Event Sourcing | Persisting ordered domain events as the authoritative record of aggregate state |
| Gateway | An application-owned interface that isolates an external provider such as Cloudinary |
| MVP | In architecture sections: Model–View–Presenter; in product scope: Minimum Viable Product. Context determines the meaning |
| Projection | A rebuildable read model derived from events |
| RAG | Retrieval-Augmented Generation: retrieving approved knowledge before generating an answer |

## Appendix B: PRD Approval Checklist

- [ ] Product owner confirms the MVP scope.
- [ ] Course requirements are mapped correctly.
- [ ] Role permissions are approved.
- [ ] Seed prices and equipment are either approved or retained as demo-only.
- [ ] Open decisions needed for implementation are resolved.
- [ ] Acceptance scenario is accepted as the submission demonstration.
