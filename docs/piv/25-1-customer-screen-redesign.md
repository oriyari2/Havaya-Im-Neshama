# PIV — Task 25.1 Customer Screen Redesign

## What was created

The Manager Customer screen was rebuilt as a focused browse-to-details flow.
The list is now the dominant surface, with a concise search row, one obvious
Customer-creation action, four decision-relevant columns, and one contextual
View Details action. Advanced sort, city, Customer type, and status controls
remain available but are collapsed until requested.

Customer Details is a dedicated internal Desktop page within the same passive
View. It owns Edit and Delete actions and provides a clear Back action. The
stacked-page design preserves the live table, search text, advanced-filter
state, pagination, scroll position, and selected row instead of rebuilding the
list when the user returns.

## Interaction flow

```text
Customer list
  → single click selects and preloads the record
  → double click / Enter / View Details opens Customer Details
  → Edit or Delete operates through the existing Presenter
  → Back or Escape returns to the preserved Customer list
```

## UX decisions and rationale

- **One purpose per page:** the list supports finding and choosing; the details
  page supports understanding and acting. This removes competing workflows.
- **Four default columns:** name, type, city, and status are sufficient to
  identify and distinguish Customers. Phone, email, contact, address, notes,
  and audit timestamps are complete-record information and therefore belong in
  Details.
- **Progressive filters:** search handles the common case immediately, while
  all existing advanced filters remain discoverable behind one labeled
  control. The first view is calmer without losing capability.
- **Multiple equivalent open paths:** double-click supports fast mouse use,
  Enter supports keyboard users, and View Details supports explicit discovery.
  Single-click performs selection only, matching established Desktop behavior.
- **Actions follow context:** New Customer remains globally visible in the page
  header. Edit and Delete appear only on Customer Details, reducing accidental
  operations and list clutter.
- **State-preserving Back:** an internal `QStackedWidget` changes surfaces
  without recreating the list, so users resume exactly where they were.
- **Full-width table:** removing the permanent split pane gives the primary
  browsing surface substantially more horizontal and vertical room.
- **No visual-identity redesign:** existing colors, typography, borders,
  radii, feedback components, and tokens remain. A selector-specificity rule
  only ensures the existing primary treatment remains visible on New Customer.

## Architecture preservation

- `CustomersPresenter` and its Qt-free View protocol are unchanged.
- Existing signals still own list, detail, create, edit, delete, retry,
  filtering, and pagination orchestration.
- The View performs only local UI navigation and composition.
- Backend, services, authorization, caching, CQRS, Event Sourcing, and business
  rules are unchanged.
- New Customer still invokes the single existing
  `CustomersPresenter.begin_create` / `submit_create` implementation.
- User Administration's Customer-role creation remains a distinct atomic
  user-provisioning workflow; Task 25.1 adds no duplicate standalone Customer
  creation logic.

## Files changed

- `desktop_client/app/views/customers_view.py`
- `desktop_client/app/views/design_tokens.py`
- `desktop_client/tests/test_customer_views.py`
- `desktop_client/tests/test_ui_foundations.py`
- `tasks/25-desktop-visual-design-ui-ux-cohesion.md`
- `docs/piv/requirements-traceability.md`
- `docs/screenshots/task-25-1-customers-before.png`
- `docs/screenshots/task-25-1-customers-list-after.png`
- `docs/screenshots/task-25-1-customer-details-after.png`

## How to run

```powershell
.\.venv\Scripts\python.exe -m desktop_client.app.main
```

Sign in as a Manager and open **Customers**.

## Validation

Affected Desktop tests cover:

- all existing Customer Presenter behavior and boundaries;
- single-click selection without navigation;
- Enter, double-click, and dedicated-action detail navigation;
- return-to-list search and selection restoration;
- progressive advanced-filter disclosure and complete payloads;
- four-column table policy and absence of detail-only columns;
- 1024×640, 1200×760, and 1440×900 list/detail geometry;
- feedback, accessibility, tooltip, form, and Customer dialog behavior.

Compilation is validated with:

```powershell
.\.venv\Scripts\python.exe -m compileall backend desktop_client
```

## Screenshots

- [Before redesign](../screenshots/task-25-1-customers-before.png)
- [Customer list after redesign](../screenshots/task-25-1-customers-list-after.png)
- [Customer Details after redesign](../screenshots/task-25-1-customer-details-after.png)

## Next task

Wait for explicit product-owner direction. Do not redesign another screen as
part of Task 25.1.
