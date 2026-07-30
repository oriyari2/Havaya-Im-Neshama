# Task 21 PIV — Manager User and Role Administration

## Status

The bounded new-entity creation correction is **COMPLETE; READY FOR AUDIT**.
This correction is not committed or pushed.

## Approved requirement

> The system shall manage users and support authentication when entering the
> system.

Task 21 now targets only the smallest clean manager-created account workflow
needed to satisfy this requirement. Existing email/password login, PBKDF2
hashing, generic invalid-credential response, and inactive-account rejection
remain the authentication architecture.

## Evidence inspected

- `AGENTS.md`, README, ARCHITECTURE, PRD, roadmap, traceability, Task/PIV 20;
- backend users schema, user repository, auth service/router/schemas,
  password/JWT helpers, manager dependencies, Customer/Instructor link and
  protected-delete behavior;
- desktop Session/AuthService, login, navigation/composition, Task 20 shared
  foundations, and current Customer/Instructor management patterns;
- relevant backend and desktop tests and current clean Task 20 baseline.

## Current gap

Authentication exists, but no manager user list/create/edit/status/reset API or
desktop screen exists. Database email uniqueness is case-sensitive, and profile
links are neither unique nor constrained by role. These are the bounded Task 21
gaps.

## Final lean design

Managers can:

- list/search users;
- filter by role and active status;
- create an immediately usable Manager account, or atomically create a new
  Customer plus primary Contact or a new Instructor with its linked account;
- read safe user detail;
- edit a user's normalized email;
- activate/deactivate users except the signed-in Manager;
- reset a selected user's password directly.

Roles remain `manager`, `instructor`, and `customer`. Manager stores a required
human-readable `display_name` but has no Customer/Instructor profile.
Customer and Instructor creation always creates a new corresponding entity and
never selects an existing one. The submitted email is the sole login identifier
for every role and is also stored as the Customer/Instructor email. A database
check constraint, normalized email unique index, and partial unique profile
indexes enforce the resulting one-to-one links.

## Selected editing policy

Role and profile link are immutable after creation. Edit supports email only;
status and password use explicit actions. This is the least-complex compliant
policy because the approved requirement requires role support, not role
transition. An incorrectly created identity is deactivated and replaced with a
correct account.

Email remains the sole login identifier. Email-only Edit atomically updates the
User and its linked Customer/Instructor email, preserving that invariant.

The current Manager may Edit or Reset their own account but cannot Deactivate
it. A simple backend self-deactivation check is required; no last-active-manager
rule is added.

## Minimal API

- `GET /users`
- `POST /users`
- `GET /users/{user_id}`
- `PUT /users/{user_id}` — email only
- `POST /users/{user_id}/activate`
- `POST /users/{user_id}/deactivate`
- `POST /users/{user_id}/reset-password`

There is no DELETE, audit-history, role-transition, profile-reassignment,
first-login-change, self-registration, or session-version endpoint.

## Desktop design

The Manager-only page uses Task 20 `PageScaffold`, responsive semantic user
table, email-or-displayed-name search, role/status filters, safe detail context,
pagination, and visible Create User, logical Delete User, Activate, Reset
Password, Refresh, and email-only Edit Email actions. Logical Delete is the
existing confirmed deactivation operation; it never physically deletes a row.
The table and details panel use the business label `שם`: Manager display name,
Customer name, or Instructor name. Single-click selects and updates action
states; double-click explicitly displays email, role, name, status, and
created/updated dates in the side panel.
Loading, empty, validation, conflict, forbidden, connection, server, and success
states remain supported.

Create User dynamically shows common login email/password/role fields. Manager
adds required Name. Customer
adds Customer name, Contact name, and Contact phone. Instructor adds Instructor
name and optional phone. Manager adds no profile fields. There are no existing-
Customer or existing-Instructor selectors and no separate username. Backend
creates Customer+Contact+User or Instructor+User through one connection and one
commit; any failure rolls back the entire operation.

Dialogs follow the Task 20 focus/accessibility/RTL standard. Email, passwords,
and dates retain correct LTR behavior. Password fields are masked and cleared;
no secret appears in table/detail/feedback.

## Explicitly excluded from Task 21

- public self-registration;
- email verification;
- SMS verification;
- MFA and OTP;
- first-login password change;
- password-reset emails and links;
- `auth_version`;
- forced session invalidation;
- advanced audit/event systems;
- optimistic versioning;
- complex role-transition and profile-reassignment workflows;
- physical user deletion, enterprise IAM, branding, and unrelated redesign.

## Architecture boundary

```text
passive UsersView/dialogs
  -> Qt-free UsersPresenter
  -> UserService
  -> generic ApiClient
  -> manager-only FastAPI users router
  -> UserAdministrationService
  -> UserRepository + existing Customer/Instructor repositories
  -> PostgreSQL
```

Existing AuthService/login remains unchanged unless implementation review finds
a real blocking defect and approval is granted first. User administration is
ordinary CRUD, not CQRS/Event Sourcing. Booking, Gateway, RAG, and other domain
boundaries remain unchanged.

## Essential safety retained

- manager-only backend authorization;
- normalized case-insensitive email uniqueness;
- valid role/profile combinations and unique links;
- existing secure password hashing;
- inactive-login rejection;
- no password/hash/token in management responses or UI;
- simple current-manager self-deactivation protection.

No forced invalidation is claimed: after password reset an already-issued token
retains its existing expiry; deactivation is immediately enforced because auth
reloads the active user on each protected request.

## Lean testing evidence required

Backend coverage includes Manager list, non-Manager 403, creation of all roles,
atomic new Customer/Contact/User and Instructor/User creation, rollback on User
failure, duplicate email, invalid role-specific fields, email edit,
activate/deactivate, inactive login, reset, old-password failure,
new-password success, and secret non-exposure.

Desktop/Presenter design covers load/display, search/filters, all three dialogs,
status actions, loading/empty/validation/conflict/forbidden/connection/server
states, duplicate guards, stale selection, accessibility, RTL/LTR, responsive
table geometry, and excluded-screen compatibility.

Full backend/desktop regressions, compileall, architecture/security scans,
`git diff --check`, whitespace, and Windows manual validation remain required.

## Implementation evidence

- Added the manager-only FastAPI user-administration router, application
  service, safe request/response schemas, and repository operations.
- Added normalized case-insensitive email uniqueness, unique Customer and
  Instructor links, and database-enforced role/profile compatibility.
- Added the Task 20-based Manager User Management page, Qt-free presenter,
  desktop service, and Create User, Edit Email, and Reset Password dialogs.
- Manager navigation and composition expose the module only to Managers;
  backend authorization remains authoritative on every endpoint.
- Passwords use the existing PBKDF2 helper. Passwords, hashes, tokens, and
  linked-profile private data are absent from management responses and UI.
- Role and profile links remain immutable; deletion and all other exclusions
  in this document remain excluded.

## Validation evidence

- Updated exact focused/full totals are recorded in the correction report after
  final validation.
- Compile, architecture/security scans, whitespace validation, and
  `git diff --check` are required before audit handoff and recorded in the
  final implementation report.
- Manual interactive Windows review remains an audit/acceptance activity; the
  automated Qt tests cover construction, state behavior, dialogs, RTL/LTR,
  table behavior, accessibility metadata, and navigation.

## Documentation state and approval gate

- Task 21, this PIV, roadmap, and traceability describe the implemented lean
  scope and retain its explicit exclusions.
- PRD, README, and ARCHITECTURE remain unchanged.
- Implementation is complete. Audit, commit, and push remain not started.
- Wait for ChatGPT and product-owner implementation audit approval before any
  commit or push.
