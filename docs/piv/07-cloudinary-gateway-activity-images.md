# Task 07 - Cloudinary Gateway and Activity Images

## Plan

Implement backend activity image support only, using a Gateway abstraction so Cloudinary SDK access is isolated to infrastructure.

Supported PRD requirements:

- FR-ACT-03: managers can upload an activity image through the image Gateway.
- FR-ACT-02: activity catalog responses include displayable image URLs.
- FR-ACT-04: customers and instructors have read-only access to images for active activities.
- Gateway course requirement: external image service access is behind an application-owned interface.

## Implement

Created:

- `backend/app/application/gateways/image_gateway.py` with the `ImageGateway` protocol, `UploadedImage`, and provider-neutral errors.
- `backend/app/infrastructure/gateways/cloudinary_image_gateway.py` with the only Cloudinary SDK usage.
- `backend/app/infrastructure/gateways/providers.py` to provide the configured image Gateway.
- `backend/app/infrastructure/repositories/activity_image_repository.py` for parameterized PostgreSQL access.
- `backend/app/application/services/activity_image_service.py` for upload, list, delete, file type validation, and activity visibility rules.
- `backend/app/schemas/activity_image.py` for image API responses.
- `backend/app/routers/activity_images.py` with `POST /activities/{activity_id}/images`, `GET /activities/{activity_id}/images`, and `DELETE /activities/{activity_id}/images/{image_id}`.

Updated:

- `backend/app/db/schema.py` adds `activity_images` persistence and indexes.
- `backend/app/schemas/activity.py` exposes `primary_image` and `images` fields on activity responses.
- `backend/app/infrastructure/repositories/activity_repository.py` includes primary image metadata for catalog list/detail reads.
- `backend/app/application/services/activity_service.py` includes full image metadata on activity detail reads.
- `backend/app/main.py` registers the activity image router.
- `backend/requirements.txt` adds `cloudinary` and `python-multipart`.
- `backend/.env.example` contains Cloudinary placeholder variables only.

## Configure Cloudinary

Add real values only to the local, ignored `backend/.env` file:

```powershell
CLOUDINARY_CLOUD_NAME=real_cloud_name
CLOUDINARY_API_KEY=real_api_key
CLOUDINARY_API_SECRET=real_api_secret
CLOUDINARY_ACTIVITY_FOLDER=havaya-im-neshama/activities
CLOUDINARY_URL=cloudinary://real_api_key:real_api_secret@real_cloud_name
```

Do not commit real secrets.

## Run

Install backend dependencies if needed, configure `DATABASE_URL` and Cloudinary in `backend/.env`, initialize the database when locally enabled, then run:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```

## Validate

Compile validation:

```powershell
.\.venv\Scripts\python.exe -m compileall backend desktop_client
```

Result: passed.

FastAPI import smoke check:

```powershell
.\.venv\Scripts\python.exe -c "from backend.app.main import app; print(app.title)"
```

Result: passed after installing the updated backend requirements.

Gateway boundary validation:

```powershell
rg "import cloudinary|from cloudinary" backend
```

Expected result: direct SDK imports appear only in `backend/app/infrastructure/gateways/cloudinary_image_gateway.py`.

Result: passed.

Manual acceptance checks to run with real Cloudinary credentials:

- Manager can upload an image to an existing activity.
- Upload returns saved metadata including `public_id` and `secure_url`.
- Manager can list and delete activity images.
- Instructor and customer can list images for active activities.
- Instructor and customer cannot upload or delete images and receive 403.
- Missing activities or images return 404.
- Unsupported content types return 422.
- Activity list/detail responses expose image URLs.

## Out Of Scope

- PySide6 activity image UI.
- Bookings, CQRS, Event Sourcing, dashboard, RAG, and desktop navigation.
- Advanced image editing, transformations, or messaging integrations.

## Next Task

Task 08 should implement the Booking Event Sourcing and CQRS core.
