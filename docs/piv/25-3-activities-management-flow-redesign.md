# Task 25.3 - Activities Management Flow and Layout Redesign

## Scope

Task 25.3 redesigns only the PySide6 Activities module and the Activity create,
edit, detail, lifecycle, and image workflows opened from it. It does not
redesign Bookings or Open Events and adds no new persistence or API contract.
Customers remains the reference for the shared RTL management hierarchy.

## Backend capability audit

| Capability | Actual implementation | Desktop classification |
|---|---|---|
| List and page Activities | `GET /activities`, limit/offset, role-aware active visibility | Implemented in Desktop |
| Search | Repository searches name, description, audience, pricing, equipment, preparation, season and tags | Implemented through one search field |
| Sort | Repository ordering is fixed to name then ID | Immediate Name sort only; unsupported sorts were not invented |
| Audience filter | Case-insensitive backend filter | Implemented in inline filter panel |
| Season filter | Case-insensitive backend filter | Implemented in inline filter panel |
| Tag filter | Case-insensitive backend filter | Intentionally hidden; broad search still matches tags |
| Active-state filter | Manager may request active/inactive/all; other roles are forced active | Implemented for Manager only |
| Create and update | Manager-only POST/PUT for all Activity fields | Implemented in shared Create/Edit dialog |
| Deactivate | DELETE performs `is_active=false`, preserving the row | Implemented with logical lifecycle wording |
| Reactivate | PUT with `is_active=true` | Implemented as the inactive-state action |
| Images | Detail list plus manager upload/delete through Gateway-backed endpoints | Implemented in Details gallery |
| Image primary flag | Upload makes the new image primary | Reflected by initial gallery selection; no Set Primary endpoint exists |
| Physical deletion | No physical-delete Activity workflow exists | Intentionally unsupported |
| Booking relationships | Booking projections/CQRS reference Activity | Intentionally managed only in Bookings |
| Open-event relationships | Open Events derives Activity data from booking projections | Intentionally managed only in Open Events |
| Related counts/statistics | No efficient Activity count contract exists | Recommended for later; not calculated client-side |
| Dependency protection | Logical deactivation preserves booking/event references | Implemented by the existing lifecycle |

## Desktop implementation

The crowded table/detail/media splitter is replaced by the shared
`ManagementWorkspace` list-to-details flow: reference header, framed toolbar,
progressive filters, semantic RTL table, fixed per-row Details action, and
pagination. Single click selects; row action, double-click, and Enter open
Details.

The toolbar exposes search, truthful immediate Name sort, Filter, and Reset.
The inline panel contains audience, season, and manager-only status and shows
an active-filter summary. Reset clears search, sort, filters, page, selection,
and Details state without opening another window.

Activity Details owns the Activity hero, status, description, Back, mutually
exclusive lifecycle actions, Activity/operation/system property cards, and the
image gallery. Booking creation is absent; Bookings remains the single command
workflow. Booking and Open Event counts are omitted because no efficient
Activity response/query supplies them.

The gallery provides an aspect-ratio-safe centered preview, empty/loading/error
states, previous/next and keyboard navigation, a position indicator, image
metadata, and manager-only upload/remove actions. It reuses the existing image
service, in-memory preview cache, backend endpoints, Gateway, and confirmation.

Activity Create/Edit uses `EntityFormDialog`: shared RTL sections and label
geometry, natural bounded height, enabled primary submit, click-time field
validation, temporary red summary, first-error focus, and in-flight duplicate
submission protection. Status is preserved on Edit and controlled by lifecycle
actions.

Repeated Activities navigation resets Presenter/View state and returns to the
default list. Back preserves current list controls and selection.

## Files changed

- Activities View, dialog, Presenter integration, and shared workspace.
- Focused Activity and shared-foundation tests.
- Task 25 parent documentation and requirements traceability.

## Validation

- Focused Activity View, Presenter, service and backend tests.
- Shared management/UI-foundation regression tests.
- `python -m compileall backend desktop_client`.
- Presenter Qt and Desktop direct-database scans.
- `git diff --check` and clean post-commit status.

No screenshots, images, diagrams, Booking redesign, or Open Events redesign
were created.

## Next

Stop after Task 25.3 and wait for explicit approval.
