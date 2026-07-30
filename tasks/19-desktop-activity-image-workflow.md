# Task 19 - Desktop Activity Image Display and Manager Media Workflow

## Goal

Complete the end-to-end activity-image MVP by connecting the existing Task 07
FastAPI/Gateway endpoints to the existing PySide6 Activities module.

Managers can upload, view, and delete activity images. Instructors and
customers can view images for active activities without mutation controls.

## Motivation and PRD Requirements

- `FR-ACT-03`: complete manager upload through the image Gateway end to end.
- `FR-ACT-02`: display persisted activity images in the desktop catalog.
- `FR-ACT-04`: provide role-safe read-only catalog images to instructors and customers.
- `FR-AUTH-02`, `FR-AUTH-03`, `NFR-01`, `NFR-04`, `NFR-05`, `NFR-07`, `NFR-09`, and `NFR-10`.

## Scope and Functional Requirements

- authenticated multipart upload in the desktop API client
- public HTTPS preview retrieval without the FastAPI bearer token
- centralized upload, preview, and cache limits
- manager upload/delete inside the existing Activities screen
- image metadata and preview display for every permitted role
- primary-image preference with first-image display fallback
- a maximum-three-entry in-memory LRU preview cache
- request identity that prevents obsolete previews replacing current selection
- focused transport, service, presenter, and view tests
- PIV, traceability, README, and architecture documentation

Preview bytes must never be written to disk. Failed, partial, oversized,
invalid, or obsolete results are not cached. Cache entries are invalidated after
mutation and all entries are cleared on logout/session expiry.

## Configuration

- `MAX_UPLOAD_SIZE_BYTES = 10 MiB`
- `MAX_PREVIEW_DOWNLOAD_BYTES = 10 MiB`
- `MAX_PREVIEW_CACHE_ENTRIES = 3`

These defaults have one authoritative definition in desktop configuration.

## Authorization Matrix

| Operation | Manager | Instructor | Customer |
|---|---:|---:|---:|
| View active image | Allow | Allow | Allow |
| View inactive image | Allow | Deny | Deny |
| Upload image | Allow | Deny | Deny |
| Delete image | Allow | Deny | Deny |

FastAPI remains authoritative. Missing authentication returns 401, wrong roles
return 403, missing records return 404, unsupported types return 422, and
Gateway failure returns 502 through the existing Task 07 contract.

## User Flows and Errors

Managers select an activity, choose one `.jpg`, `.jpeg`, `.png`, or `.webp`,
upload through FastAPI, and see refreshed authoritative state. Deletion requires
confirmation. Instructor/customer screens render active-activity images without
mutation controls. Preview failure leaves textual details visible and offers
retry. Mutation connection failures are not automatically retried.

Local files must exist, be regular/readable/non-empty/supported, and fit the
configured limit. Preview URLs must be absolute HTTPS, fit the preview limit,
and never receive the API token. Logs must not contain secure URLs, public IDs,
image bytes, tokens, multipart bodies, or Cloudinary credentials.

## Desktop MVP and Gateway Boundaries

```text
ActivitiesView -> ActivitiesPresenter -> ActivityService -> ApiClient
```

The View owns file dialogs, confirmation, Qt decoding/scaling/rendering. The
Presenter owns selection, request identity, orchestration, and the non-Qt cache;
it imports no Qt classes. The Service owns API adaptation and local-file
validation. The transport owns multipart and bounded byte retrieval.

Upload/delete backend flow remains:

```text
FastAPI -> ActivityImageService -> ImageGateway -> Cloudinary
```

Backend production code must remain unchanged unless a blocking defect is
discovered during implementation review and explicit architectural approval is
given before any backend change.

## Out of Scope

- backend API/Gateway/persistence changes
- new navigation or standalone media administration
- batch upload, drag/drop, captions, reordering, primary reassignment
- editing, transformations, video, documents, OCR, AI analysis
- disk/offline cache or list-row image downloads
- booking, CQRS, Event Sourcing, customer, instructor, dashboard, RAG, or AI changes
- unrelated visual or networking refactors

## Expected Files

- `desktop_client/app/media_config.py`
- `desktop_client/app/api/client.py`
- `desktop_client/app/services/activity_service.py`
- `desktop_client/app/presenters/activities_presenter.py`
- `desktop_client/app/views/activities_view.py`
- `desktop_client/app/main.py`
- focused desktop tests and required documentation

Backend production, booking, authentication, RAG, AI, Docker, and database
schema files must not be modified.

## Validation

```powershell
.\.venv\Scripts\python.exe -m unittest desktop_client.tests.test_api_client desktop_client.tests.test_activity_service desktop_client.tests.test_activities_presenter desktop_client.tests.test_activity_views -v
.\.venv\Scripts\python.exe -m unittest discover -s desktop_client/tests -v
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
.\.venv\Scripts\python.exe -m compileall backend desktop_client rag
git diff --check
git status --short
```

Manual acceptance covers manager upload/display/delete, multiple images,
inactive manager access, instructor/customer read-only access, 403 mutations,
validation failures, stale-preview rejection, token-free preview transport,
no disk persistence, Gateway failure, and cleanup of temporary provider data.

## Risks, Assumptions, and Open Questions

Desktop HTTP remains synchronous and may briefly block Qt; request identity
still rejects obsolete results. Cloudinary secure URLs are assumed to be public
HTTPS resources. Real credentials are needed for live acceptance. There are no
remaining design questions after architecture approval.

## No Commit

Do not commit or push until ChatGPT audits and approves the implementation.
