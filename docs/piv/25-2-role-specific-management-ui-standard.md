# PIV — Task 25.2 Role-Specific Management UI Standard

## Created

Customer, Instructor, and Manager management now use the same RTL page
hierarchy, list-to-details flow, semantic tables, pagination, information
cards, equal action buttons, dialog conventions, feedback, and password flow.
Instructor and Manager modules no longer use legacy split panes.

Instructor fields remain limited to name, login email, phone, city, notes,
status, and audit data. Manager details contain only name, login email, status,
and audit data. Login email is read-only during edit; passwords remain
write-only and change only through the shared password modal.

## Architecture

`ManagementWorkspace` owns reusable UI composition only. Role-specific Views
remain passive and existing Presenters orchestrate their services. Manager name
editing remains inside the user-administration service and repository boundary.
Authentication, authorization, account creation, and hashing stay centralized.

## Validation

Focused backend, Presenter, service, View, and UI-foundation tests are run with
`compileall` and `git diff --check`. No screenshots, images, diagrams, mockups,
or visual reports were generated.

## Next

Stop and wait for explicit approval before continuing to another screen.

## Final stabilization and completeness audit

- Removed the unlaid `StatePanel`/`FeedbackBanner` children previously created
  by `StatefulWidget`. Showing their loading state produced the apparent empty
  window over Instructor selection. Loading and empty states now live only in
  widgets owned by the visible page layout.
- The Dashboard is selected and its initial request is started before the
  completed Shell replaces Login. The Login Presenter no longer updates its
  deleted View after authentication, so startup exposes one intended top-level
  window and one direct Login-to-Shell transition.
- Customer, Instructor, and Manager headers and toolbar containers now use the
  same margins, spacing, typography, frame, control dimensions, and RTL order:
  Search field, Search, one immediate Sort selector, Reset.
- Instructor sorting uses existing name, city, phone, email, status, created,
  and updated fields. Manager sorting uses existing name, email, status,
  created, and updated fields. Sort values are server-whitelisted and reuse the
  existing list endpoints and repository queries.
- Every displayed management-table item now receives explicit right alignment,
  including emails and technical text. Semantic minimum widths prevent the
  important identity columns from being squeezed; horizontal scrolling remains
  available below the supported minimum.

Backend/Desktop coverage was audited as follows:

- Customer and Instructor create, read, edit, logical lifecycle, linked-account
  creation, password change, business fields, status display, and audit metadata
  are represented in Desktop.
- Manager create, read, name edit, activation/deactivation, password change,
  status, and audit metadata are represented in Desktop.
- Multi-contact CRUD remains intentionally outside these management screens:
  the approved MVP presents and edits one current primary contact through the
  Customer workflow instead of exposing the internal contact collection.
- Raw Customer/Instructor `is_active` mutation is not exposed through Edit;
  the dedicated lifecycle action synchronizes profile and account. Manager
  activation/deactivation uses the canonical account workflow.
- Instructor assignment relationships remain in Booking Management, where the
  CQRS workflow owns assignment changes; duplicating them in Instructor Details
  would violate that boundary.

Focused tests cover top-level-window lifecycle, startup replacement, module
string isolation, toolbar order and immediate sorting, explicit RTL alignment,
semantic widths, and repository sort whitelists. No screenshots or visual
assets were created.

## Final visual parity follow-up

Instructor and Manager Details now use the Customer Details hero as their
literal composition reference: opening Details hides the list-page header,
Back restores it, and the hero owns the title, status, module-specific
subtitle, and equal-width actions. Property cards share the Customer padding,
heading alignment, 140-pixel label column, right-aligned expanding values,
3:2 wide-screen proportions, and stacked narrow-screen composition. Management
status cells use the same active badge while retaining explicit RTL item
alignment. The shared table foundation continues to provide identical row and
header heights, typography, selection, alternation, padding, scrolling, and
column-resize behavior.

## Closing implementation pass

- Customer remains the canonical management reference. Instructor and Manager
  now share its header margins, toolbar frame, empty-state hierarchy, result
  count, table region and scroll behavior, pagination geometry, scrollable
  Details composition, responsive 3:2 cards, and RTL property alignment.
- Customer, Instructor, and Manager create/edit dialogs now call the same
  canonical dialog composition: 760x600 minimum geometry, 820x650 preferred
  geometry, 860 maximum width, title/description/required hierarchy, section
  titles, wrapped form rows, 240-pixel minimum fields, 44-pixel actions, shared
  margins, validation label, and keyboard order.
- Clicking Customers, Instructors, or Managers now resets that Presenter and
  View to its first-page, default-sort, empty-search list state, clears selection
  and Details state, hides stale feedback, and rejects an open module dialog.
- Shared success feedback remains visible for 2.25 seconds and then uses one
  250 ms ease-in/out opacity transition before hiding. Errors remain visible.
- `ShellView` is parented to `MainWindow` while the workspace is assembled, so
  it can never temporarily become a top-level window before replacing Login.

## Backend/Desktop capability audit

The audit records findings only. It does not authorize the recommendations.

### Customers

| Backend capability | Desktop implementation | Missing from Desktop | Reason if omitted | Recommendation |
|---|---|---|---|---|
| List/query: search, city, type, active, name/created sort, paging | Search, name/created sort and paging are exposed | City, type and active filters | Approved compact toolbar deliberately avoids advanced filters | Consider a future optional filter drawer only if operators demonstrate need |
| Customer create/read/update/lifecycle | Full manager list, Details, create, edit, deactivate and reactivate | Physical delete | Normal operations preserve history | Keep physical delete maintenance-only |
| Customer account creation and password reset | Create provisions login; password is write-only; reset action is exposed | Existing password and hash | Security requirement forbids read/display | Keep omitted permanently |
| Customer fields: name, type, city, address, phone, email, notes, status, audit timestamps | Displayed and editable where supported; status and timestamps are read-only | None for the approved single-customer workflow | — | No action |
| Contact list/create/update/soft-delete, active/primary flags, role title, email, notes and timestamps | One current primary contact name/phone is integrated into Customer create/edit/details | Multi-contact management and extended contact metadata | MVP intentionally standardizes one current primary contact; separate CRUD would expand product scope | Reassess as a separately approved contact-management task |
| Customer-scoped read permission | Customer profile uses the ownership-safe endpoint | Manager UI does not surface permission internals | Authorization is enforced server-side, not represented as a control | Keep architecture as-is |
| Customer relationships to bookings | Represented in Booking Management, not Customer Details | Embedded booking history/statistics | CQRS booking projections own booking relationships | Consider a read-only related-bookings panel in a future task |

### Instructors

| Backend capability | Desktop implementation | Missing from Desktop | Reason if omitted | Recommendation |
|---|---|---|---|---|
| List/query: search, city, active, seven whitelisted sort fields, paging | Search, all useful sorts and paging are exposed | City and active filters | Compact Customer-standard toolbar permits one search and one sort control | Consider a future optional filter drawer after usage validation |
| Instructor create/read/update/lifecycle | Full manager workflow with atomic deactivate/reactivate | Physical delete | Normal operations preserve history | Keep physical delete maintenance-only |
| Instructor login creation and password reset | Create provisions login; reset is write-only and shared | Existing password and hash | Security requirement | Keep omitted permanently |
| Fields: name, phone, email, city, notes, status and audit timestamps | All represented; login email is read-only on edit | None | — | No action |
| `/instructors/me` | Separate instructor self-profile screen | Self-edit | Endpoint is read-only and role-specific | Keep read-only unless PRD adds self-service profile editing |
| Booking assignments/open events relationships | Managed in Booking Assignment/Open Events modules | Assignment controls in Instructor Details | Booking CQRS owns assignment changes and permissions | Optionally add read-only workload summary later; do not duplicate commands |

### Managers

| Backend capability | Desktop implementation | Missing from Desktop | Reason if omitted | Recommendation |
|---|---|---|---|---|
| User list/query: search, role, active, five whitelisted sorts, paging | Manager role is fixed; search, all useful sorts and paging are exposed | Active filter and role selection | Screen is intentionally Manager Management, not generic user administration | Consider active filter only if operational volume requires it |
| Manager create/read/name update | Full list, Details, create and edit | Email update | Manager update contract intentionally accepts manager name only; email is permanent login identifier | Keep read-only unless identity-change workflow is explicitly designed |
| Activate/deactivate with self-deactivation guard | Both states are exposed through context-sensitive actions | Hard delete | Backend intentionally uses account activation state | Keep hard delete omitted |
| Password reset | Shared write-only reset dialog | Existing password/hash | Security requirement | Keep omitted permanently |
| Status and audit timestamps | Displayed in list/Details | Additional metadata/statistics | Backend exposes none for manager administration | No action |
| Permissions | Entire API and screen are manager-only; self-deactivation is blocked server-side | Permission editor/role mutation | Roles are fixed MVP identities; access is deny-by-default | Treat future RBAC administration as a separately approved feature |

No module-specific statistics, bulk commands, export endpoint, or additional
management metadata exists in the audited backend. Consequently none is hidden
by these Desktop modules.

## Professional UX review (documented, not implemented)

### Critical improvements

- No unresolved critical usability or accessibility defect was found in the
  bounded Customer/Instructor/Manager workflows after this pass.

### Recommended improvements

- Add an explicitly approved advanced-filter drawer for city/type/status only
  if real operators need narrower lists; preserve the compact default toolbar.
- Add unsaved-change confirmation before a future navigation mechanism can
  dismiss edited form content. Current modal behavior prevents sidebar use, but
  the module reset contract deliberately rejects a dialog if invoked.
- Add visible keyboard shortcut hints for Create, Search, Details and Back, and
  test the complete workflow with Hebrew keyboard layouts and screen readers.
- Consider read-only related-booking/workload summaries on Customer and
  Instructor Details, sourced from booking queries rather than duplicated
  management commands.
- Define a deliberate identity-change process before ever making login email
  editable; it should include uniqueness checks, session implications and audit.

### Nice-to-have improvements

- Persist user-selected table column widths per workstation while retaining a
  reliable Reset Columns action.
- Add optional density modes for operators working with unusually large lists.
- Add non-blocking copy actions for email and phone values in Details cards.
- Add localized relative-time tooltips beside exact audit timestamps.
- Conduct a future usability session measuring task completion time, error rate,
  keyboard-only flow and discoverability with representative operators.

### Review conclusion

Navigation, information hierarchy, action placement, table selection, Details
scannability, form hierarchy, keyboard order and Hebrew RTL behavior are now
consistent across the three modules. The remaining recommendations require
separate product approval and were intentionally not implemented in Task 25.2.

## Final QA closure

The Instructor and Manager status columns previously installed both a backing
text item and an `ActiveBadge` in the same cell. The backing item was removed;
status now follows the Customer implementation exactly and has one non-wrapping
badge per cell. Focused Qt tests cover both `פעיל` and `לא פעיל` at 1024 and
1400 pixel window widths and assert the canonical 40-pixel row height.

The final endpoint-level classification is:

| Module | Backend capability | Desktop support | Status |
|---|---|---|---|
| Customers | `GET /customers`: search, name/created sort, paging | Search, both sorts, pagination | Implemented in Desktop |
| Customers | `GET /customers`: city/type/active filters | No advanced-filter controls | Intentionally hidden |
| Customers | `GET /customers/{id}` | Details and customer self-profile | Implemented in Desktop |
| Customers | `POST /customers` | Customer/account create dialog | Implemented in Desktop |
| Customers | `PUT /customers/{id}` business/contact fields | Customer edit dialog | Implemented in Desktop |
| Customers | `POST /customers/{id}/activate|deactivate` | Mutually exclusive lifecycle action | Implemented in Desktop |
| Customers | `DELETE /customers/{id}` | No Desktop client method or action | Intentionally hidden maintenance endpoint |
| Customers | `POST /customers/{id}/reset-password` | Shared write-only password dialog | Implemented in Desktop |
| Customers | Contact list/create/update/soft-delete endpoints and extended contact metadata | One current primary contact is embedded in Customer workflow | Backend only |
| Instructors | `GET /instructors`: search, all whitelisted sorts, paging | Search, seven sorts, pagination | Implemented in Desktop |
| Instructors | `GET /instructors`: city/active filters | No advanced-filter controls | Intentionally hidden |
| Instructors | `GET /instructors/{id}` | Manager Details | Implemented in Desktop |
| Instructors | `GET /instructors/me` | Instructor self-profile | Implemented in Desktop |
| Instructors | `POST`, `PUT /instructors` | Create and edit | Implemented in Desktop |
| Instructors | `POST /instructors/{id}/activate|deactivate` | Mutually exclusive lifecycle action | Implemented in Desktop |
| Instructors | `DELETE /instructors/{id}` | No Desktop client method or action | Intentionally hidden maintenance endpoint |
| Instructors | `POST /instructors/{id}/reset-password` | Shared write-only password dialog | Implemented in Desktop |
| Managers | `GET /users` with fixed manager role, search, sorts and paging | Manager list/search/sort/pagination | Implemented in Desktop |
| Managers | Generic user role and active filters | Role is fixed; active filter has no control | Intentionally hidden |
| Managers | `POST /users` for manager creation | Manager create dialog | Implemented in Desktop |
| Managers | Generic `/users` creation of customer/instructor identities | Dedicated domain workflows are used instead | Backend only |
| Managers | `GET /users/{id}` and `PUT /users/{id}` manager name | Details and edit dialog | Implemented in Desktop |
| Managers | Application-service email update workflow | No router contract or Desktop action; login identity remains immutable | Backend only |
| Managers | Activate/deactivate endpoints with self/last-manager guards | Deactivate or Reactivate action | Implemented in Desktop |
| Managers | `POST /users/{id}/reset-password` | Shared write-only password dialog | Implemented in Desktop |

No audited capability is marked Deprecated. Internal repository primitives are
implementation details rather than independent Desktop workflows. The dead-UI
scan found no unreachable management dialog, unconnected action, orphan
management Presenter/widget, copied placeholder, TODO UI, or visible temporary
top-level widget. Disabled management actions now carry an accessible reason.

## Shared-foundation closure

The final refactor makes `ManagementWorkspace` the sole layout implementation
for the Customer, Instructor, and Manager list page, module header, framed
toolbar, semantic table, pagination, Details hero, action row, responsive card
composition, and property-sheet rows. Customer no longer carries a separate
copy of that layout. Entity Views now supply only labels, columns, fields,
sorts, actions, and data mapping.

`EntityFormDialog` is likewise the sole create/edit/password dialog builder.
Customer, Instructor, Manager, and password dialogs provide declarative field
and section specifications. Dialog height follows content (with bounded
scrolling for long forms), so short forms no longer inherit blank vertical
space from Customer creation. All management success messages continue through
the shared `FeedbackBanner`, whose dismiss timer and fade total 2.5 seconds.

### Manager lifecycle architectural review

No lifecycle behavior was changed in this pass. Manager deletion remains a
reversible logical deactivation of the login account; activation is explicit
and self-deactivation is rejected by the service. Physical deletion would risk
breaking audit attribution, historical references, incident investigation, and
accountability, and should not be introduced without a formal retention and
referential-integrity policy.

Customer and Instructor Delete currently targets the physical profile record
and is protected by linked-account, booking, and event-history dependency
checks. Because normal creation provisions a linked login, those guards make
physical deletion unavailable for ordinary established profiles. The
recommended long-term model is one audited, atomic deactivate/reactivate use
case that synchronizes profile and account state for all three entity types,
with physical purge reserved for a separately authorized retention workflow.
That recommendation requires product approval and was deliberately not
implemented in Task 25.2.

## Approved lifecycle unification

The product subsequently approved the recommended logical lifecycle. The
normal Desktop UI now exposes Edit, write-only Password Change, and exactly one
status action: Deactivate for an active Customer/Instructor/Manager or
Reactivate for an inactive one. Customer and Instructor physical-delete API
endpoints remain available only as protected legacy/maintenance endpoints and
are not connected to any Desktop View or navigation path.

Customer and Instructor activation/deactivation runs in one database
transaction. It locks the domain profile and linked User, updates both
`is_active` values, commits both changes together, and rolls back both on any
failure. No booking, assignment, event, contact, account, or audit record is
deleted. Manager lifecycle remains account-based, continues to reject
self-deactivation, and now locks the active-manager set and rejects deactivation
of the last active Manager.

The three Details Views use `ManagementWorkspace.add_lifecycle_actions()` and
`show_lifecycle()` for the same labels, dimensions, mutually exclusive
visibility, and active/inactive behavior. Manager Customer listing no longer
implicitly excludes inactive Customers, ensuring every deactivated Customer
remains reachable for reactivation. Login email remains immutable in Desktop,
and password values remain write-only.

## Shared dialog validation feedback

Customer, Instructor, Manager, and password dialogs validate on primary action
instead of disabling that action while fields are incomplete. The shared
dialog builder shows every issue beside its field, applies the common invalid
style, focuses the first invalid field, and clears each issue when corrected.
A non-modal shared red banner summarizes the failure and fades after about
three seconds. Submit is disabled only during an in-flight request; safe Hebrew
messages keep backend validation/conflict failures inside the open dialog.
