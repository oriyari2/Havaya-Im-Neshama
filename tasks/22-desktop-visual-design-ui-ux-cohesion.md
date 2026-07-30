# Task 22 Audit — Desktop Visual Design System and UI/UX Cohesion

## Status

**PLANNING AUDIT COMPLETE — DESIGN NOT STARTED — IMPLEMENTATION NOT STARTED**

This document identifies and bounds the next task after Task 21. It is not an
implementation specification and authorizes no code or test changes.

## Why Task 22 is next

Task 21 closes the Phase 1 architecture and identity baseline. The approved
roadmap now prioritizes a coherent professional desktop experience before
performance work and before remaining AI expansion. Task 22 must therefore
establish the shared visual/UX system that later screen migrations consume.

## Objectives

1. Audit every desktop screen against the Task 20 foundation and identify
   visual, spacing, typography, hierarchy, feedback, table, dialog,
   accessibility, RTL, and responsive-layout inconsistencies.
2. Define one professional visual language using centralized tokens rather than
   per-screen hardcoded styling.
3. Define the approved application-wide component variants and interaction
   rules for pages, headers, actions, filters, tables, details, forms, dialogs,
   feedback, navigation, empty/loading/error states, and focus.
4. Select a strictly bounded implementation pilot for Task 22. Tasks 23–25 own
   full screen-by-screen migration.
5. Preserve domain workflows and architecture while improving clarity,
   consistency, accessibility, responsiveness, and professional presentation.

## Acceptance criteria

- A complete desktop visual inventory and inconsistency matrix exists.
- Final Task 22 design names the pilot screens and explicit exclusions.
- Central tokens cover approved color roles, typography, spacing, control/icon
  sizes, radii, borders, elevations, motion, dialog geometry, and table density.
- Shared components have documented states, accessibility metadata, RTL/LTR
  behavior, keyboard behavior, and responsive rules.
- No pilot uses local hardcoded visual constants when an approved token exists.
- Supported 1024×640, 1200×760, and 1440×900 layouts remain usable without
  overlap, clipped actions, inaccessible paging, or unexplained blank regions.
- Loading, empty, validation, authorization, connection, server, success, and
  disabled states are visually distinguishable and use the Task 20 feedback
  strategy.
- Manager, Customer, and Instructor roles retain the same functionality,
  authorization, and visible permitted modules.
- Presenters remain Qt-free and Views remain passive.
- No backend/API/database/domain behavior changes.
- Focused desktop tests, full desktop regression, compileall, architecture
  scans, whitespace checks, and manual Windows visual/keyboard review pass.

## Affected desktop modules

Audit coverage includes:

- shared design tokens, theme, `PageScaffold`, feedback/state, dialog, table,
  accessibility, and RTL helpers;
- composition root, Login, Shell/navigation, and Dashboard compatibility;
- Customers, Users, Instructors, Activities, Bookings, Booking Details/history,
  Open Events, profiles, AI Chat, and Knowledge Management compatibility.

The design proposal must choose a smaller implementation pilot. Audit coverage
does not authorize migrating every module in Task 22.

## Affected backend modules

None expected. Task 22 is a desktop presentation-foundation task. Backend
routers, schemas, services, repositories, database schema, authorization,
booking CQRS/Event Sourcing, image Gateway, and RAG behavior remain unchanged.

If a genuine blocking contract defect is found during design or implementation,
work must stop and explicit architectural approval is required before any
backend production change.

## Documentation impact

The later design/implementation cycle is expected to synchronize:

- this Task 22 document from audit to approved design and actual evidence;
- `docs/piv/22-desktop-visual-design-ui-ux-cohesion.md` when implementation is
  authorized;
- `docs/PROJECT-ROADMAP.md` status;
- `docs/piv/requirements-traceability.md` for advanced NFR-01, NFR-03, NFR-07,
  NFR-09, NFR-10, and desktop/module evidence;
- `ARCHITECTURE.md` only for implemented shared View-layer contracts;
- README only if launch, supported-size, or user-visible operating guidance
  actually changes.

`docs/PRD.md` must remain unchanged unless the product owner approves a product
requirement change.

## Architecture impact

Expected impact is confined to the desktop View foundation:

```text
central design tokens/theme
        -> passive shared PySide6 components
        -> passive feature Views
        <- plain state/intents from Qt-free Presenters
```

Task 22 must not redefine MVP, add desktop database access, move business logic
into Views, move Qt into Presenters, change backend responsibilities, weaken
server authorization, or alter CQRS/Event Sourcing/Gateway/RAG boundaries.

No new dependency should be introduced unless the design proves it necessary,
bounded, Windows-compatible, academically appropriate, and explicitly approved.

## Implementation risks

| Risk | Required mitigation |
|---|---|
| Unbounded redesign across every screen | Select a bounded pilot; defer full migration to Tasks 23–25 |
| Styling changes break layouts | Token/component tests plus three supported-size checks |
| Visual polish hides architecture regression | Presenter/View/service/import scans remain release gates |
| Hardcoded colors/spacing proliferate | Central tokens and source scans |
| Hebrew RTL breaks emails, dates, IDs, or URLs | Explicit mixed-direction tests and tooltips |
| Accessibility regresses | Names, descriptions, focus order/visibility, keyboard, contrast tests |
| Missing brand assets block work | Use an approved professional neutral system; never invent logos/assets |
| Shared stylesheet affects excluded modules | Scope selectors and compatibility construction tests |
| UI work changes domain behavior | Freeze API/business contracts and compare regression behavior |
| Scope absorbs Phase 3 performance work | Loading visuals only; background execution remains Task 26 |

## Recommended implementation order

1. Inspect current screens at all supported sizes and produce an evidence matrix.
2. Confirm product-owner inputs: desired tone, available logo/assets, and any
   prohibited colors/imagery; record neutral fallback decisions.
3. Finalize token semantics and theme application boundaries.
4. Finalize component/state/accessibility/RTL/responsive specifications.
5. Select and approve a bounded pilot plus files that must not change.
6. Add token/component/foundation tests before migrating pilot Views.
7. Implement shared foundations, then migrate the pilot without presenter or
   backend changes.
8. Run focused/full desktop tests, compileall, scans, and manual Windows review.
9. Synchronize PIV, roadmap, traceability, and implemented architecture evidence.
10. Await complete audit and approval before commit/push.

## Estimated implementation complexity

**Medium–High.** The domain behavior is unchanged, but shared visual foundations
have broad regression potential. A bounded pilot is medium complexity; the
application-wide inventory, accessibility/RTL validation, responsive behavior,
and compatibility proof raise overall Task 22 complexity. Full screen migration
is deliberately distributed across Tasks 23–25.

## Explicitly out of scope

- backend/API/database changes;
- new modules, screens, domain workflows, roles, or permissions;
- background workers, API optimization, caching, and performance work;
- new AI/RAG/Ollama behavior;
- final packaging or submission work;
- invented brand assets or unrelated refactoring.

## Approval gate

The next activity is a complete Task 22 design proposal. No implementation may
begin until ChatGPT and product-owner approval is recorded.
