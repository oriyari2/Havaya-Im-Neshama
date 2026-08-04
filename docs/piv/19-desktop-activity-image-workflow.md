# Task 19: Desktop Activity Image Display and Manager Media Workflow

## Plan

Close the remaining desktop media gap for `FR-ACT-02`, `FR-ACT-03`, and
`FR-ACT-04` by consuming the existing Task 07 API. Preserve MVP, server
authorization, and the image Gateway without changing backend production code.

## Implement

- authenticated multipart JPEG/PNG/WebP manager upload
- manager deletion with confirmation and authoritative refresh
- active-activity image display for instructors/customers
- manager image access for active/inactive activities
- primary preview selection and first-image fallback
- token-free HTTPS-only bounded preview downloads
- configurable 10 MiB upload/preview defaults
- configurable three-entry memory-only LRU cache
- mutation invalidation and logout/session-expiry clearing
- request-generation checks that discard obsolete preview results
- Qt decoding/rendering only inside `ActivitiesView`
- HTTPS-only redirect targets and final preview response validation
- safe local stat/read error translation and defensive optional metadata display

Preview data is never written to disk. Task 19 code does not log secure URLs,
public IDs, image bytes, tokens, multipart bodies, or Cloudinary credentials.

## Architecture

```text
ActivitiesView -> ActivitiesPresenter -> ActivityService -> ApiClient
```

Upload/delete backend flow remains unchanged:

```text
FastAPI -> ActivityImageService -> ImageGateway -> Cloudinary
```

The Presenter owns non-Qt selection/cache/request identity. The View owns file
dialogs, confirmations, `QPixmap` decoding/scaling/rendering. The service owns
file validation/API adaptation. Public previews never attach the bearer token.
`ActivitiesView.show_preview` returns decode success to the presenter so only a
successfully decoded preview is admitted to the memory cache.

## Files Changed

- `desktop_client/app/media_config.py`
- `desktop_client/app/api/client.py`
- `desktop_client/app/features/activities/service.py`
- `desktop_client/app/features/activities/presenter.py`
- `desktop_client/app/features/activities/view.py`
- `desktop_client/app/main.py`
- four focused desktop test modules
- Task 19, PIV, traceability, README, and architecture documents

No backend production file was changed.

## Validate

- Focused Task 19 desktop suite: 43 passed.
- Full desktop suite: 111 passed.
- Full backend suite: 169 passed after installing the already-pinned
  `httpx==0.28.1` locally; no dependency file changed.
- `compileall backend desktop_client rag` passed.
- `git diff --check` passed with line-ending warnings only.
- Boundary scans confirmed Cloudinary SDK imports remain limited to the
  infrastructure Gateway, presenters import no PySide6, and desktop code has no
  PostgreSQL access or preview disk-write path.

## PRD Requirements Advanced

- `FR-ACT-03`: manager upload is connected end to end through the Gateway.
- `FR-ACT-02`: activity images render in the desktop catalog.
- `FR-ACT-04`: instructor/customer active-activity media is read-only.
- `FR-AUTH-02`/`FR-AUTH-03`: backend enforcement and role-safe controls remain.

## Live Validation

Live validation passed against the configured Supabase-compatible PostgreSQL
database and Cloudinary account:

- instructor upload returned 403
- customer delete returned 403
- manager upload returned 201
- manager image list contained the uploaded image
- instructor/customer active-activity reads returned 200 and contained it
- public HTTPS preview returned 68 bytes without an API bearer token
- manager cleanup delete returned 200

The temporary validation image was removed from Cloudinary and its database
metadata was deleted at the end of the check.

## Known Limitations

- Desktop networking remains synchronous.
- Cancellation is logical result rejection, not physical request interruption.
- Deleting a primary does not promote another record; the first remaining image
  is a non-persistent display fallback.
- No batch upload, drag/drop, captions, transformations, disk cache, or row thumbnails.

## Next Task

After audit and approval, define final end-to-end validation and academic
submission/demo packaging as a bounded task.
