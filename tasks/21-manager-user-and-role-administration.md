# Task 21 — Manager User and Role Administration

## 1. Status

- Design: approved lean scope.
- Implementation: **COMPLETE; READY FOR AUDIT**.
- Audit, commit, and push: not started.

Implementation followed the approved scope. No commit or push is authorized
until the implementation audit is approved.

## 2. Requirement and goal

The approved requirement is:

> The system shall manage users and support authentication when entering the
> system.

Task 21 satisfies it with the smallest clean implementation: authenticated
Managers can create and manage accounts for the three existing roles, while the
existing login flow continues to authenticate email/password credentials,
reject invalid credentials, and reject inactive accounts.

## 3. Current-state findings

- `users` already stores email, PBKDF2 password hash, role, active state,
  optional Customer/Instructor links, and timestamps.
- `POST /auth/login` and `GET /auth/me` already implement normal authentication.
- Login normalizes email to lowercase and rejects inactive users.
- `require_roles("manager")` is the existing server authorization mechanism.
- User persistence currently supports authentication lookup and demo seeding
  only; no manager user-management API or desktop screen exists.
- Database email uniqueness is currently case-sensitive.
- Customer/Instructor links are not currently unique and their compatibility
  with the selected role is not database-constrained.
- Task 20 supplies the approved neutral `PageScaffold`, table, dialog, feedback,
  request-state, accessibility, RTL, and responsive behavior.

## 4. Related requirements

- PRD user-management/authentication requirement quoted above.
- PRD sections 5, 5.1, and 5.2: Manager, Instructor, Customer and deny-by-default
  server authorization.
- `FR-AUTH-01`: registered users authenticate with valid credentials.
- `FR-AUTH-02`: protected operations are authorized by role/resource.
- `FR-AUTH-03`: desktop navigation matches the signed-in role.
- PRD User Administration screen: users, roles, and active status.
- PRD `users` entity.
- `NFR-02`, `NFR-04`, `NFR-05`, `NFR-07`, `NFR-09`, and `NFR-10`.
- Course evidence: user management, authentication/RBAC, PostgreSQL, FastAPI,
  PySide6, MVP, search, form/data entry, table/details, and PIV.

No PRD change or new authentication architecture is required.

## 5. Final lean scope

### In scope

- Manager-only user list with search, role filter, active/inactive filter, and
  bounded offset pagination consistent with existing management screens.
- Create an active Manager account, or atomically create a new Customer and
  primary Contact or a new Instructor together with its linked User account.
- Read a selected user for the table/detail/edit context.
- Edit a user's normalized email only.
- Activate and deactivate users, except self-deactivation.
- Manager-controlled password reset.
- Existing secure password hashing and login behavior.
- Case-insensitive normalized email uniqueness.
- Valid role/profile combinations and unique Customer/Instructor links created
  within the account transaction.
- Simple protection against the signed-in Manager deactivating their own account.
- Task 20 desktop foundations, friendly states, accessibility, RTL/LTR handling,
  and focused/full regression validation.
- Task/PIV/roadmap/traceability synchronization.

### Explicitly excluded from Task 21

- public self-registration;
- email verification;
- SMS verification;
- MFA and OTP;
- first-login password change;
- password-reset emails and links;
- reset tokens or invitation workflows;
- `auth_version` or another token/session version;
- forced session invalidation after email/password changes;
- refresh-token, device-session, blacklist, or remote-logout systems;
- advanced audit/event systems or audit-history screens;
- optimistic versioning or enterprise concurrency mechanisms;
- complex role-transition and profile-reassignment workflows;
- role editing after user creation;
- profile-link editing after user creation;
- physical user deletion;
- self-service password change;
- separate Business Manager and Office Manager technical roles;
- arbitrary permissions or fine-grained access-control editing;
- login rate limiting, global correlation/log infrastructure, or Task 23 work;
- branding changes, workflow wizards, advanced identity management, or unrelated
  screen redesign;
- changes to Customer/Instructor profile CRUD, booking CQRS/Event Sourcing,
  activities/images/Gateway, RAG/AI/Ollama, or Docker.

## 6. Supported roles and authorization matrix

Persisted role values remain exactly:

- `manager`
- `instructor`
- `customer`

| Capability | Manager | Instructor | Customer | Enforcement |
|---|---|---|---|---|
| See User Management navigation | Yes | No | No | role-aware composition |
| List/search/filter/read users | Yes | No | No | backend manager dependency |
| Create users | Yes | No | No | backend manager dependency |
| Edit supported user fields | Yes | No | No | backend manager dependency |
| Activate/deactivate users | Yes | No | No | manager dependency plus self-deactivation guard |
| Reset user password | Yes | No | No | backend manager dependency |
| Log in with own valid active account | Yes | Yes | Yes | existing auth flow |

Desktop visibility is not a security boundary. All `/users` routes require an
authenticated current user with `role == "manager"`; missing credentials return
401 and authenticated Instructor/Customer requests return 403.

## 7. Selected editing policy

Role and profile link are immutable after account creation.

The Edit User dialog supports email only. Active status uses explicit Activate
and Deactivate actions, and password changes use the separate Reset Password
dialog. This policy is the least complex compliant option because the approved
requirement requires user management and role support, not role conversion.
Role is assigned during account creation, and immutable role/link prevents partial
cross-role state, complex reassignment, session-role changes, and profile
ownership ambiguity.

If a role or link was created incorrectly, the Manager deactivates that account
and creates a correct account. The existing inactive identity remains stored.
Any future role transition or profile reassignment requires a separate approved
requirement and is not implied by Task 21.

The signed-in Manager may edit or reset their own account but cannot deactivate
it. No complex last-manager counting rule is added. If the signed-in Manager
edits their own email, the Shell may retain the old display value until the next
login; authentication uses the new normalized email immediately.

## 8. Identity relationships and database rules

### Role/profile truth table

| Role | `customer_id` | `instructor_id` |
|---|---|---|
| `manager` | null | null |
| `customer` | exactly one Customer ID | null |
| `instructor` | null | exactly one Instructor ID |

- The linked profile must exist, be active, and match the selected role at user
  creation.
- A Customer profile can link to at most one user.
- An Instructor profile can link to at most one user.
- User and linked Customer/Instructor emails are kept identical and updated in
  one transaction because email is the sole login identifier.
- User activation/deactivation does not modify the linked profile.
- Existing Customer/Instructor protected deletion continues to reject deletion
  while any user link exists, including an inactive user.

### Database enforcement

The current `users` table remains the identity table. No user-audit table and no
new version/session columns are added.

Schema initialization adds:

- one check constraint enforcing the role/profile truth table;
- one unique index on `lower(email)` for case-insensitive uniqueness;
- one unique partial index on non-null `customer_id`;
- one unique partial index on non-null `instructor_id`.

Application validation supplies friendly errors; constraints close simple race
conditions. Constraint installation must detect incompatible existing rows and
stop with a clear local diagnostic rather than silently rewriting identities.

## 9. User lifecycle

### Create

1. Manager opens User Management and selects Create User.
2. Manager enters the one login email, password, role, and the required new
   Customer/Contact or Instructor fields when applicable.
3. Desktop performs basic validation and submits once.
4. Backend normalizes email, creates the new business entity and primary Contact
   when applicable, hashes the password, links the active User, and commits all
   inserts atomically.
5. The new user can immediately log in with that email and password.

Manager accounts require no profile. Customer and Instructor creation never
selects or reuses an existing profile. For all roles, the submitted email is the
unique User account identifier and authentication login; there is no username.
The same email is stored on the new Customer or Instructor. Any insert failure
rolls back the new Customer/Contact or Instructor and the User together.

### Read/list/search/filter

Managers can list users, search normalized email or the already-displayed linked
Customer/Instructor name, filter by role, filter by active state, page through
bounded results, select a row, and view safe details.
Passwords and hashes never enter list/detail responses.

### Edit

Manager edits a user's email. Backend normalizes and verifies case-insensitive
uniqueness, then atomically updates the User login and linked Customer or
Instructor email so the single login identifier remains consistent. Role,
profile links, active state, and password are not part of this request.

### Activate/deactivate

- Deactivate retains the user and links but makes future login fail.
- Activate restores login eligibility when the unchanged linked profile remains
  present and active; otherwise backend returns 409 until the profile condition
  is corrected in its owning module or the account remains inactive.
- Self-deactivation is rejected with 409.
- No physical delete endpoint exists.

### Reset password

Manager enters and confirms a new password for a selected user. Backend validates
and hashes it with the existing PBKDF2 helper. No plaintext or hash is returned,
logged, audited, or retained by Presenter/service state. After success, new
login attempts use the new password and the old password fails.

Reset does not activate an inactive user and does not force first-login change.
Existing access tokens are not forcibly invalidated; they retain existing expiry
and current-user checks. Deactivation still rejects an existing token on its
next protected request because current auth reloads `is_active` from PostgreSQL.

## 10. Validation rules

### Email

- Required; strip whitespace and lowercase before lookup/storage.
- Existing project email format rule; maximum 254 characters.
- Unique case-insensitively across active and inactive users.

### Password

- Required for create/reset; 8–128 characters.
- No trimming or normalization; leading/trailing whitespace and control
  characters are rejected to avoid accidental credentials.
- Confirmation is desktop-only and must match before submission.
- Request models forbid extra fields and public response models contain no
  password/password-hash fields.

This deliberately uses a small MVP policy and the existing password hasher; it
does not introduce password history, forced rotation, temporary-password state,
or recovery tokens.

### Role/profile

- Role is a strict enum of the three lowercase values.
- Manager rejects all Customer/Instructor creation fields.
- Customer requires Customer name, Contact name, and Contact phone; `email` is
  both Customer email and login email.
- Instructor requires Instructor name and permits phone; `email` is both
  Instructor email and login email.
- Existing Customer/Instructor IDs are forbidden in the create request.
- Client cannot supply ID, timestamps, active state, password hash, or role/link
  changes through the email-edit request.

## 11. Minimal API design

All endpoints follow the current unversioned FastAPI convention.

| Method and path | Request | Success |
|---|---|---|
| `GET /users` | `search`, `role`, `is_active`, `limit`, `offset` | `200 list[UserResponse]` |
| `POST /users` | `UserCreateRequest` | `201 UserResponse` |
| `GET /users/{user_id}` | none | `200 UserResponse` |
| `PUT /users/{user_id}` | `UserEmailUpdateRequest` | `200 UserResponse` |
| `POST /users/{user_id}/activate` | empty JSON object | `200 UserResponse` |
| `POST /users/{user_id}/deactivate` | empty JSON object | `200 UserResponse` |
| `POST /users/{user_id}/reset-password` | `PasswordResetRequest` | `204` |

There is no user DELETE, event-history, role-transition, profile-reassignment,
first-login-change, or self-registration endpoint.

### Request/response models

- `UserCreateRequest`: common `email`, `password`, and `role`; Customer requires
  `customer_name`, `contact_name`, and `contact_phone`; Instructor requires
  `instructor_name` and permits `instructor_phone`; Manager has no profile fields.
- `UserEmailUpdateRequest`: `email` only.
- `PasswordResetRequest`: `new_password` only.
- `UserResponse`: safe User fields including Manager `display_name`, plus role-appropriate Customer name/email,
  primary Contact name/phone, or Instructor name/email/phone and timestamps.

All request models use `extra="forbid"`. Responses never include password,
password hash, bearer token, JWT data, or credentials.

### Query and status behavior

- `search`: optional case-insensitive email substring.
- `role`: optional strict role.
- `is_active`: optional boolean.
- `limit`: 1–200, default 50; `offset`: non-negative, default 0.
- Default ordering: normalized email ascending, then ID for stability.
- Repository SQL is parameterized; no caller-controlled SQL expression exists.

Status codes:

- 400 or 422: invalid request values/role-link combination/password.
- 401: missing/invalid authentication.
- 403: authenticated non-Manager.
- 404: requested user does not exist.
- 409: duplicate email, self-deactivation, inactive linked profile during later
  reactivation, or invalid activate/deactivate state.
- 500: sanitized unexpected error with no SQL/security detail.

## 12. Backend architecture

```text
FastAPI users router
  -> UserAdministrationService
  -> UserRepository
  -> PostgreSQL users/customer/instructor reads
```

- Router owns HTTP schemas, manager dependency, and safe status translation.
- Application service owns normalization, password hashing orchestration,
  role/new-profile validation, self-deactivation check, and atomic transaction
  boundaries across Customer/Contact/Instructor/User inserts.
- Repository owns parameterized list/get/insert/update/status/password SQL and
  safe joined profile reads.
- Existing AuthService/login continues to own credential verification and active
  user rejection. It needs no new architecture or token format.
- User management is ordinary transactional CRUD. It is not CQRS or Event
  Sourcing and does not affect booking event boundaries.

## 13. Desktop architecture and UX

```text
UsersView / User dialogs (passive PySide6)
  -> UsersPresenter (Qt-free orchestration)
  -> UserService (endpoint adapter)
  -> ApiClient (generic authenticated transport)
  -> FastAPI
```

- Add `users` / “ניהול משתמשים” only to Manager navigation and composition.
- View never imports service/API/repository/database logic.
- Presenter never imports PySide6/Qt and owns filters, selection, friendly error
  mapping, duplicate-action guards, and stale selection/request identity.
- UserService owns paths/payload transport only.
- ApiClient remains domain-neutral.

### User Management page

Use Task 20 `PageScaffold` with:

- visible action bar with Create User (`יצירת משתמש`), logical Delete User
  (`מחיקת משתמש` through deactivation), Activate, Reset Password, and the
  existing email-only Edit Email action;
- Filter Area containing email-or-displayed-name search, role filter, status filter, apply/reset,
  and refresh;
- Main Content containing responsive semantic table and safe details panel;
- pagination footer;
- `StatePanel` for initial loading/empty/blocking read failure;
- `FeedbackBanner` for mutation success/conflict/forbidden/connection failure
  while current content remains usable.

Table columns:

| Column | Semantic policy | Direction |
|---|---|---|
| Email | Primary/Technical | LTR with full tooltip |
| Role | Compact | localized text/badge |
| Name | Secondary | Manager display name, Customer name, or Instructor name |
| Status | Compact | active/inactive text and badge |
| Updated | Technical | direction-safe date |

The table fills its viewport, supports keyboard row selection, preserves full
values in direction-aware tooltips, and remains usable at 1024×640, 1200×760,
and 1440×900 without redesigning other pages.

### Create User dialog

- Opens with the invalid placeholder `בחר תפקיד`, no role-specific fields, and
  Save disabled. No role is selected by default.
- The role combo ignores mouse-wheel changes so dialog scrolling, focus changes,
  validation, and field visibility updates cannot alter the selected role.
- Login email (LTR), password (masked), password confirmation (masked), role,
  and conditional new-entity fields.
- Manager shows common account fields only.
- Customer shows Customer name, the same login/Customer email, Contact name,
  and Contact phone; there is no existing-Customer selector.
- Instructor shows Instructor name, the same login/Instructor email, and
  optional phone; there is no existing-Instructor selector.
- Changing role clears incompatible local fields.
- Save creates an immediately usable active account.
- Validation retains non-secret fields; submitted password fields are cleared
  after a server response and on close.

### Edit User dialog

- Displays the business Name and role/status read-only and permits email edit only.
- Role/profile/status/password are not silently submitted.

### Reset Password dialog

- Displays target email, new password, confirmation, Save and Cancel.
- Password fields are masked and cleared after submission/close.
- No temporary/first-login/email/reset-token wording.

### Activate/deactivate

- Selection-dependent explicit actions. The visible Delete User action is a
  conventional label for logical deletion and calls the existing Deactivate
  operation after Task 20 destructive confirmation naming the target and login
  consequence; no row is physically deleted.
- Self-deactivation is disabled in the View/Presenter and rejected by backend.
- Activate is enabled only for an inactive selection and does not use a
  destructive confirmation.

### Selection and safe details

- A single click selects the row and updates action availability.
- A double click explicitly loads the selected user's complete safe response
  into the existing details panel: email, role, business Name, active status,
  created date, and updated date.
- Create, logical Delete, Activate, Reset Password, and email-only Edit remain
  visible actions and never require double click.
- Passwords, hashes, tokens, and secrets never appear in the table or details.

### States and errors

- Loading blocks only conflicting actions; duplicate submissions are ignored.
- Empty state explains that no users match current filters.
- Inline validation handles email/password/role/profile errors.
- Duplicate email/link or invalid activation uses friendly 409 feedback.
- 401 follows existing session-expiry behavior; 403 is friendly and nontechnical.
- Connection/server errors preserve safe content and release guards for retry.
- Raw SQL, constraint names, hashes, passwords, tokens, and exception text never
  reach the View.

## 14. User flows

### Registration

1. Manager opens User Management and selects Create User.
2. Manager enters the one login email, password, role, and required new
   Customer/Contact or Instructor fields.
3. Presenter validates required fields and submits once.
4. Backend atomically inserts the new business entity, primary Contact where
   applicable, and linked active account with a password hash.
5. Desktop refreshes/selects the new user and shows success.
6. New user logs in normally using the created email/password.

### Search/filter/read

1. Manager enters email-or-displayed-name search and optional role/status filters.
2. Presenter loads the bounded list and ignores obsolete list results.
3. Single-click selects the row; double-click explicitly displays all available
   safe identity/name/status/timestamp details in the side panel.

### Edit email

1. Manager selects a user and opens Edit.
2. Email is updated after normalization/uniqueness validation on both the User
   login and linked Customer/Instructor in one transaction.
3. List/detail refresh; role, link, status, and password remain unchanged.

### Activate/deactivate

1. Manager selects another user.
2. Deactivate requires explicit confirmation; Activate is a direct safe action.
3. Backend changes `is_active`; inactive login fails and reactivated login works.

### Reset password

1. Manager selects a user and enters a new matching password.
2. Backend validates/hashes it and returns 204.
3. Old password fails on the next login; new password succeeds.

## 15. Error handling and edge cases

- Duplicate normalized email, including inactive account: 409.
- Same email with different case: 409.
- Any failure while creating Customer/Contact/Instructor/User rolls back the
  entire account-creation transaction.
- Manager with profile, Customer without Customer profile, Instructor without
  Instructor profile, or cross-role profile fields: 422.
- Self-deactivation: 409; no change.
- Activate already active/deactivate already inactive: 409.
- Reactivating with a now-inactive linked profile: 409.
- Reset inactive user: allowed but does not activate the account.
- Incorrect old password after reset: existing generic invalid credentials.
- User disappears between selection and action: 404, clear stale detail, refresh.
- Selection/filter changes invalidate obsolete list/detail results.
- Concurrent duplicate email/profile insert is resolved by DB uniqueness and
  mapped to 409; no optimistic user version is introduced.
- Any user-management response serialization is explicitly checked for secret
  fields.

## 16. Expected implementation files

Expected new files:

- `backend/app/schemas/user_admin.py`
- `backend/app/application/services/user_admin_service.py`
- `backend/app/routers/users.py`
- `backend/tests/test_user_administration.py`
- `desktop_client/app/services/user_service.py`
- `desktop_client/app/presenters/users_presenter.py`
- `desktop_client/app/views/users_view.py`
- `desktop_client/app/views/user_dialogs.py`
- focused desktop user service/presenter/View tests following current conventions.

Expected modified files:

- `backend/app/db/schema.py`
- `backend/app/infrastructure/repositories/user_repository.py`
- `backend/app/main.py`
- `desktop_client/app/presenters/navigation.py`
- `desktop_client/app/main.py`
- relevant existing auth/navigation tests;
- Task 21/PIV 21, roadmap, traceability, and after implementation only the
  relevant README/ARCHITECTURE current-state sections.

`backend/app/application/services/auth_service.py`, auth schemas/router, core
security, and desktop Session/AuthService should remain unchanged unless a real
blocking defect is discovered during implementation review and approved before
the change. Existing login already satisfies the lean authentication scope.

## 17. Files and areas that must not be modified

- `docs/PRD.md`;
- historical Task/PIV documents;
- booking aggregate/events/commands/queries/repositories/projections;
- activity/image/Cloudinary Gateway code;
- RAG/AI/Ollama/knowledge/Docker code;
- Customer and Instructor production CRUD/routes/services/Views;
- Dashboard, Activities, Bookings, Open Events, Knowledge, and AI screens;
- Task 20 shared foundations except a blocking compatibility defect approved
  before modification;
- final branding assets or visual identity.

No unrelated refactoring or package restructuring is permitted.

## 18. Lean testing plan

### Backend

- Manager can list users and use search/role/status filters.
- Missing authentication returns 401; Instructor and Customer return 403.
- Create Manager with required human-readable name and no business profile.
- Create new Customer, primary Contact, and linked User atomically using one email.
- Create new Instructor and linked User atomically using one email.
- Duplicate normalized/case-variant email is rejected.
- Existing Customer/Instructor profiles are never selected or reused.
- Invalid/missing/cross-role new-profile fields are rejected.
- Edit email succeeds, including the Manager's own email; role/link/status/
  password cannot be edited through that request.
- Activate and deactivate succeed; self-deactivation is rejected.
- Inactive user cannot log in; reactivated user can log in.
- Reset password hashes the new value; old password fails and new password logs in.
- Reset does not activate an inactive user.
- Password, password hash, and token never appear in management responses.
- No user DELETE, role-transition, first-login-change, audit-event, or session-
  version endpoint/model exists.
- Parameterized SQL and database constraints are tested.

### Presenter/Desktop

- Manager-only navigation/composition; non-manager direct API denial remains.
- Load and display users; search, role filter, status filter, and pagination.
- Select and display safe details.
- Create dialog conditional new Customer/Contact or Instructor fields, no
  existing-profile selectors, and validation.
- Edit dialog permits only email.
- Reset Password dialog masks/clears secret fields.
- Activate/deactivate action and self-action disabled explanation.
- Loading, empty, validation, duplicate/conflict, forbidden, connection, server,
  success, and session-expiry behavior.
- Duplicate action prevention and stale list/selection rejection.
- Task 20 accessibility, focus, keyboard, dialog, RTL/LTR, tooltip, and semantic
  table geometry at 1024×640, 1200×760, and 1440×900.
- Excluded screens construct and behave unchanged.

### Regression and scans

- focused Task 21 backend/desktop tests;
- full backend and desktop suites;
- compileall for `backend`, `desktop_client`, and `rag`;
- Presenter Qt scan, View data-layer scan, desktop database scan;
- secret-field/log scan;
- confirm booking/Event Sourcing, Gateway, RAG, PRD, and excluded screens are
  unchanged;
- `git diff --check` and trailing-whitespace validation.

## 19. Manual acceptance plan

On Windows at 1024×640, 1200×760, and 1440×900:

1. Manager sees User Management; Instructor/Customer do not and receive API 403.
2. Create one Manager, Customer, and Instructor account.
3. Log in successfully with every new account using the created password.
4. Verify invalid credentials and inactive-account login rejection.
5. Verify duplicate email/case variant, invalid role-specific fields, and atomic
   rollback behavior.
6. Search by email; filter role and status; page/reset/refresh.
7. Edit a user's email and confirm role/link/status remain unchanged.
8. Deactivate another user and verify login fails; reactivate and verify login.
9. Attempt self-deactivation and verify it is rejected.
10. Reset a user's password; verify old fails and new succeeds.
11. Reset an inactive user's password and verify the user remains unable to log in.
12. Inspect API/UI data and logs for password/hash/token exposure.
13. Exercise loading, empty, validation, conflict, forbidden, connection, server,
    success, stale selection, and duplicate-click behavior.
14. Complete keyboard-only, focus, accessibility metadata, Hebrew/RTL, mixed LTR
    email/date, resize, scrolling, table elision/tooltip, and dialog review.
15. Regression-check existing role navigation and operational workflows.

Use demo data only. Because physical deletion is excluded, manually created
acceptance users are cleaned up by deactivation.

## 20. Final acceptance criteria

1. Only authenticated Managers can access all user-management API/UI operations.
2. Managers can list, search, role-filter, status-filter, and inspect safe users.
3. Managers can create immediately usable accounts for all three roles.
4. Role/new-profile truth table, one-to-one links, and atomic creation are
   enforced by service and DB constraints.
5. Email is normalized and case-insensitive unique across active/inactive users.
6. Managers can edit a user's email without changing role/profile.
7. Managers can activate/deactivate another user; inactive users cannot log in.
8. Simple self-deactivation protection works without a complex last-manager rule.
9. Manager password reset uses existing hashing; old password fails and new works.
10. No password, hash, token, or secret appears in management responses/UI/logs.
11. No physical deletion, role transition, profile reassignment, audit system,
    optimistic version, forced password change, or token-version feature exists.
12. Task 20 layout, request-state, accessibility, RTL, table, and dialog contracts
    are satisfied without redesigning excluded modules.
13. MVP/backend boundaries remain intact and no booking/Gateway/RAG behavior changes.
14. Focused/full tests, compileall, scans, whitespace, and manual acceptance pass.
15. Documentation is synchronized and implementation remains uncommitted until
    the normal ChatGPT audit and product-owner approval.

## 21. Risks, assumptions, and limitations

| Item | Lean decision |
|---|---|
| Incorrect role/new-profile fields | create-time schema/service validation |
| Duplicate email race | database unique index mapped to 409; transaction rolls back |
| Manager deactivates self | simple actor/target check |
| Last manager deactivated | not prevented; no PRD requirement and complex rule excluded |
| Password reset with existing session | no forced invalidation; token lives until expiry unless account is deactivated |
| Incorrect immutable role/link | deactivate account and create the correct one |
| Brute-force protection | deferred to Task 23 |
| Synchronous desktop calls | current CRUD convention; Task 29 owns background execution |

Assumptions:

- one technical `manager` role remains sufficient for the MVP;
- direct Manager-created passwords are acceptable for the academic workflow;
- role and profile-link immutability is approved as least-complex compliance;
- no existing Customer/Instructor selector is used during normal account creation;
- existing PBKDF2 hashing and auth flow remain the approved implementation;
- schema initialization is the current academic upgrade mechanism.

## 22. Documentation after implementation

- Update Task/PIV 21 from design to actual evidence.
- Update roadmap lifecycle status and traceability only after verified progress.
- Update README current scope/API/schema/validation after implementation.
- Update ARCHITECTURE only with implemented User View–Presenter–Service–API–
  repository flow; do not redefine MVP/authentication.
- Keep PRD and historical Task/PIV documents unchanged.

## 23. Approval gate

Implementation may begin only after ChatGPT and product-owner approval of this
lean design, including immutable role/profile links and the explicit exclusions.

## 24. Final cross-screen consistency correction

The post-implementation Windows review confirmed two presentation defects and
one expected legacy-data difference:

- The Manager Customers screen previously exposed the historical multi-contact
  CRUD surface. The normal workflow now presents one Contact-person name and
  phone as ordinary Customer fields in the Customer dialog and selected-Customer
  detail panel. The separate contacts table, role/title, primary/status controls,
  and Contact New/Edit/Deactivate/Reactivate actions are not shown. Existing
  `customer_contacts` rows and APIs remain intact; the UI reads and updates the
  active primary contact (or the first active contact) and creates one primary
  contact when none exists.
- The Manager Instructors screen now uses the Task 20 `PageScaffold`, semantic
  table sizing, tooltips/elision, a 3:2 list-to-detail stretch policy, a readable
  scrolling detail form, and accessible filters/actions/paging across supported
  Windows sizes. Name receives the principal flexible width, email receives an
  explicit readable minimum, and phone, city, and status use bounded semantic
  minimums. The three screens label status explicitly as account, Customer, or
  Instructor status so login eligibility is not confused with profile state.
- User Management remains an account list, not a list of every business entity.
  The pre-smoke read-only database audit found 20 Customers and 5 Customer-role Users, with
  15 unlinked deterministic demo Customer rows; it also found 14 Instructors and
  5 Instructor-role Users, with 9 unlinked deterministic demo Instructor rows.
  Their deterministic seed IDs and catalog emails prove that the missing account
  rows are expected seed/legacy business profiles, not a refresh, cache,
  pagination, filtering, or Task 21 synchronization defect. No accounts,
  passwords, or silent links are created for them.

The required live smoke added two uniquely identified Customer/User and two
Instructor/User pairs across its evidence runs and then logically deactivated
all smoke accounts. The final non-destructive database state is therefore 22
Customers / 7 Customer Users and 16 Instructors / 7 Instructor Users, while the
unlinked counts remain exactly 15 and 9. No smoke account remains active.

The Task 21 invariant is unchanged: every newly created Customer-role account
atomically creates Customer + Contact + User, and every newly created
Instructor-role account atomically creates Instructor + User. The list APIs have
no cache and expose those active business records immediately after refresh.
Account activation/deactivation affects login eligibility only and does not
delete or deactivate the linked business profile or Contact data.

The final creation-field completion also carries the existing Customer type and
city fields through Create User into the new Customer, and carries the existing
city field into the new Instructor. These are required fields in the combined
account-creation dialog; no new domain concept, module, or screen is introduced.
