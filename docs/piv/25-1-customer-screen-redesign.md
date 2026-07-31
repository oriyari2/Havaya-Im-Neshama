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

The final polish completes all directly owned Customer surfaces. The list uses
a shorter Customer-specific header, tighter scaffold spacing, a right-first RTL
search flow, a visually primary Search action, stronger name/city column
weighting, more table height, and a compact centered pager. Expanded filters
have an explicit optional-use explanation and aligned field groups. Customer
Details separates the record into Customer Information, Contact Information,
and System Information groups. Create and Edit dialogs share a visible heading,
sectioned fields, required-field guidance, comfortable fixed bounds with
scrolling fallback, a bounded notes area, equal-size actions, and a clearly
dominant Create/Save action using the existing primary style.

Final review keeps the title/subtitle on the RTL right and New Customer on the
left, simplifies the optional-filter trigger to `סינון לפי`, and replaces the
low-value Refresh action with `איפוס`. Reset clears search, city, Customer type,
status, and sort, collapses optional filters, and returns to page one by emitting
the existing complete filter payload. The list and Details surfaces now rely on
whitespace instead of nested frames. Counts use `לקוחות • N`. Empty datasets
show a first-Customer action, while filtered zero-results show guidance and a
Reset action; neither state displays an empty table or irrelevant pager.

Create/Edit dialogs are finalized as an 820×650 two-column RTL Desktop form:
Customer Information starts on the right, Contact Information and Notes sit on
the left, all fields are visible without horizontal or vertical scrolling, and
the existing Create/Save signal and validation behavior are unchanged.

The completion pass replaces the expanded advanced-filter row with a compact
RTL `סינון לפי` menu. It reveals only the editor selected by the manager and
allows more filters to be added deliberately. Name, city, type, status, email,
phone, and creation/update date editors are available without permanently
crowding the list. Deleting a Customer now always returns to the preserved
list; if the deletion leaves the current page empty, the preceding valid page
is requested automatically while search, filters, sorting, and list context
remain intact. Confirmation and session-expired dialogs use RTL alignment and
Hebrew action ordering.

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
- **Efficient vertical composition:** Customer-only scaffold/header spacing is
  reduced and the pager is bounded, leaving the table as the dominant region
  at supported Desktop sizes.
- **RTL search priority:** the search field begins the visual reading flow,
  immediately followed by its primary Search action; Reset and optional
  filtering remain secondary.
- **Semantic Details groups:** stable Customer, Contact, and System sections
  reduce scanning time and make labels predictable without changing data.
- **Coherent Customer dialogs:** Create and Edit use the same dimensions,
  headings, section order, label alignment, whitespace, and button sizing.
  Action text is contextual (`Create Customer` or `Save Changes`) while both
  still emit the same existing submission signal.
- **Useful reset behavior:** one clearly labeled action restores the complete
  default list state instead of merely repeating the current request.
- **Purposeful empty states:** first-use and filtered-empty contexts explain
  what happened and offer exactly one relevant next step.
- **Lighter surfaces:** removing the search container border, outer Details
  frame, and group-box borders reduces nested-panel noise without changing the
  shared visual identity.
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
- `desktop_client/app/views/customer_dialogs.py`
- `desktop_client/app/views/design_tokens.py`
- `desktop_client/app/views/management_common.py`
- `desktop_client/app/main.py`
- `desktop_client/tests/test_customer_views.py`
- `desktop_client/tests/test_ui_foundations.py`
- `tasks/25-desktop-visual-design-ui-ux-cohesion.md`
- `docs/piv/requirements-traceability.md`
- `docs/screenshots/task-25-1-customers-before.png`
- `docs/screenshots/task-25-1-customers-list-after.png`
- `docs/screenshots/task-25-1-customer-details-after.png`
- Existing Task 25.1 screenshot evidence remains unchanged; this completion
  pass intentionally creates no visual assets or screenshots.

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
- compact filter-menu field selection and type-specific editors;
- delete navigation from an emptied final page to the previous valid page;
- RTL session-expired and delete-confirmation dialog composition;
- four-column table policy and absence of detail-only columns;
- compact header/search/pager composition and dominant table height;
- Customer, Contact, and System Details grouping;
- Create/Edit dialog hierarchy, dimensions, field grouping, and primary action;
- complete Reset payload, first-use/no-results actions, and removal of dialog
  scrolling at normal Desktop size;
- 1024×640, 1200×760, and 1440×900 list/detail geometry;
- feedback, accessibility, tooltip, form, and Customer dialog behavior.

Compilation is validated with:

```powershell
.\.venv\Scripts\python.exe -m compileall backend desktop_client
```

## Screenshots

- [Before redesign](../screenshots/task-25-1-customers-before.png)
- [List before final polish](../screenshots/task-25-1-customers-list-before-final-polish.png)
- [Customer Details before final polish](../screenshots/task-25-1-customer-details-before-final-polish.png)
- [Create dialog before final polish](../screenshots/task-25-1-customer-create-before-final-polish.png)
- [Edit dialog before final polish](../screenshots/task-25-1-customer-edit-before-final-polish.png)
- [Customer list finalized](../screenshots/task-25-1-customers-list-after.png)
- [Optional filters finalized](../screenshots/task-25-1-customers-filters-after.png)
- [Customer Details finalized](../screenshots/task-25-1-customer-details-after.png)
- [Create dialog finalized](../screenshots/task-25-1-customer-create-after.png)
- [Edit dialog finalized](../screenshots/task-25-1-customer-edit-after.png)
- [List before final UX polish](../screenshots/task-25-1-customers-list-before-final-ux-polish.png)
- [Details before final UX polish](../screenshots/task-25-1-customer-details-before-final-ux-polish.png)
- [Create dialog before final UX polish](../screenshots/task-25-1-customer-create-before-final-ux-polish.png)
- [Edit dialog before final UX polish](../screenshots/task-25-1-customer-edit-before-final-ux-polish.png)
- [First-use empty state finalized](../screenshots/task-25-1-customers-empty-after.png)
- [Filtered no-results state finalized](../screenshots/task-25-1-customers-no-results-after.png)

## Next task

Wait for explicit product-owner direction. Do not redesign another screen as
part of Task 25.1.
