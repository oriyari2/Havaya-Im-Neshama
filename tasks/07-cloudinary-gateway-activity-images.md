Task 07 - Cloudinary Gateway and Activity Images

Goal

Implement activity flyer/image support through a Gateway abstraction in theHavaya Im Neshama Management System.

Managers should be able to attach a flyer or image to an activity. Customers andinstructors should be able to see the saved image URLs as part of permittedactivity catalog data.

This task supports:

FR-ACT-03 - managers can upload an activity image through the image Gateway.

FR-ACT-02 - activity catalog details include displayable image information.

FR-ACT-04 - customers and instructors have read-only access to permittedactivity information, including images.

Gateway course requirement - external image service access must go through anapplication-owned Gateway abstraction.

This task should come after Task 06 Activities CRUD API and before desktopactivity screens, bookings, dashboard, RAG, and advanced UI work.

Branch

Use this branch name:

task-07-cloudinary-gateway-activity-images

Required Context

Before implementing, read:

AGENTS.md

PRD_Havaya_Im_Neshama.md

docs/piv/requirements-traceability.md

tasks/05-authentication-rbac.md

tasks/06-activities-crud-api.md

docs/piv/06-activities-crud-api.md, if it exists

Existing backend configuration/auth/database patterns

If implementation details conflict, follow the PRD and AGENTS.md.

Cloudinary Setup Required Before Running

Create or use a Cloudinary cloud for this project.

Recommended Cloudinary cloud/folder naming:

Cloud/display name: havaya-im-neshama
Activity image folder: havaya-im-neshama/activities

Add these variables to the real local backend environment file, usuallybackend/.env.

Do not commit real secrets:

CLOUDINARY_CLOUD_NAME=real_cloud_name
CLOUDINARY_API_KEY=real_api_key
CLOUDINARY_API_SECRET=real_api_secret
CLOUDINARY_ACTIVITY_FOLDER=havaya-im-neshama/activities
CLOUDINARY_URL=cloudinary://real_api_key:real_api_secret@real_cloud_name

Update backend/.env.example with placeholder values only:

CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
CLOUDINARY_ACTIVITY_FOLDER=havaya-im-neshama/activities
CLOUDINARY_URL=cloudinary://your_api_key:your_api_secret@your_cloud_name

Verify that real .env files are ignored by Git before committing.

Current State

The project should already have:

FastAPI backend.

PostgreSQL/Supabase-compatible persistence.

Authentication and RBAC.

Activities CRUD API from Task 06.

Backend structure using schemas, application services, infrastructurerepositories, and routers.

Activity images are not implemented yet.

Business Context

An activity may have one or more visual assets, such as:

flyer image

product/example photo

catalog display image

For the MVP, the most important case is that a manager can upload or attach aflyer/image when creating or managing an activity, and customers can later seethe image in the activity catalog.

The backend should store Cloudinary metadata, not raw image files in PostgreSQL.

Required Architecture

External image service access must go through a Gateway abstraction.

Allowed:

backend/app/application/gateways/image_gateway.py
backend/app/infrastructure/gateways/cloudinary_image_gateway.py

Required rule:

Routers and activity business services must not directly import Cloudinary.

Only the infrastructure Gateway implementation may import Cloudinary SDK code.

Application code should depend on the ImageGateway abstraction.

Suggested interface methods:

upload_activity_image(file_bytes, filename, content_type) -> UploadedImage
delete_image(public_id) -> None

Use different method names if the existing project has a clearer local pattern.

Database / Persistence

Add persistence for activity images.

Prefer a separate table, for example:

activity_images

Suggested fields:

id
activity_id
public_id
secure_url
original_filename
content_type
width
height
bytes
is_primary
created_at
updated_at

Notes:

activity_id should reference activities(id).

Store Cloudinary public_id so images can be deleted later.

Store secure_url so API clients can display images.

Keep schema Supabase/PostgreSQL compatible.

Use the existing schema initialization/migration style.

If supporting multiple images feels too large, implement one primary image peractivity while keeping the design easy to extend.

Required API Behavior

Add routes using the existing FastAPI pattern.

Suggested endpoints:

POST /activities/{activity_id}/images
GET /activities/{activity_id}/images
DELETE /activities/{activity_id}/images/{image_id}

Also update existing activity responses so permitted users can see imagemetadata/URLs where useful.

POST /activities/{activity_id}/images

Upload or attach an image/flyer to an activity.

Authorization:

manager only.

Behavior:

Validate that the activity exists.

Accept an uploaded image file using FastAPI UploadFile.

Validate content type for common safe image types:

image/jpeg

image/png

image/webp

Upload the file through the ImageGateway.

Store the returned external metadata in PostgreSQL.

Return the saved image record, including secure_url.

Validation:

Missing activity returns 404.

Missing/invalid token returns 401.

Wrong role returns 403.

Unsupported file type returns 422 or 400.

Cloudinary/Gateway failure returns a controlled error, not a raw stack trace.

GET /activities/{activity_id}/images

Return images for an activity.

Authorization:

manager can read images for active and inactive activities.

instructor and customer can read images for active activities only.

Behavior:

Missing activity returns 404.

If a customer or instructor requests images for an inactive activity, return403 or follow the same visibility rule used in Task 06 activity detail.

DELETE /activities/{activity_id}/images/{image_id}

Delete or detach an activity image.

Authorization:

manager only.

Behavior:

Validate that the activity and image exist.

Delete the external Cloudinary asset through the Gateway when possible.

Remove the image record or soft-delete it according to the existing projectstyle.

Return a clear success response or the removed image record.

If external deletion fails, handle the error explicitly. Do not silently leavethe system in a confusing state.

Activity Response Updates

Update activity response models so catalog consumers can see image data.

Suggested approach:

Include images: list[ActivityImageResponse] in detail responses.

For list responses, either include the primary image only or include a compactimage list.

Keep the implementation simple and consistent with the current API style.

Authorization Rules

Use the existing authentication/RBAC helpers from Task 05.

Required behavior:

Missing or invalid token on protected routes returns 401.

Authenticated user with wrong role returns 403.

Missing activity or image record returns 404.

Role behavior:

manager can upload, view, and delete activity images.

instructor can view images for active activities only.

customer can view images for active activities only.

instructor and customer cannot upload or delete images.

Architecture Rules

Keep implementation aligned with the existing backend structure:

Routers stay thin and contain HTTP-level logic only.

Pydantic request/response schemas belong in backend/app/schemas.

Business/use-case logic belongs in backend/app/application.

Gateway abstractions belong in backend/app/application/gateways or anequivalent application-layer module.

Cloudinary SDK code belongs only in backend/app/infrastructure/gateways.

Database access belongs in backend/app/infrastructure/repositories.

Shared config belongs in the existing config/settings module.

Use parameterized SQL only.

Do not let the desktop client access PostgreSQL directly.

Suggested files:

backend/app/application/gateways/image_gateway.py
backend/app/application/services/activity_image_service.py
backend/app/infrastructure/gateways/cloudinary_image_gateway.py
backend/app/infrastructure/repositories/activity_image_repository.py
backend/app/schemas/activity_image.py
backend/app/routers/activity_images.py
backend/app/db/schema.py
backend/app/db/init_db.py
backend/app/core/config.py
backend/app/main.py
backend/.env.example

Use different names if the codebase already has a clearer local pattern.

Dependencies

Add the Cloudinary Python package to the backend requirements file if it is notalready present.

Use the package only inside the infrastructure Gateway implementation.

Out Of Scope

Do not implement in this task:

PySide6 activity image UI.

Desktop navigation changes.

Creating bookings.

Booking Event Sourcing or CQRS.

Instructor assignment.

Dashboard.

RAG or AI.

Public marketing catalog.

Advanced image editing or transformations.

Actual WhatsApp/email sending.

Keep this task focused on backend activity images and the image Gateway.

Documentation

After implementation, create or update:

docs/piv/07-cloudinary-gateway-activity-images.md
docs/piv/requirements-traceability.md

The PIV document should explain:

What was created.

Which PRD requirements were advanced.

Which files changed.

How to configure Cloudinary.

How to run it.

How it was validated.

What remains out of scope.

What the next task should be.

Update requirements traceability so:

FR-ACT-03 is marked implemented at backend/Gateway/API level.

FR-ACT-02 mentions that image URLs are now exposed in the catalog API.

FR-ACT-04 mentions read-only image visibility for customer/instructor roles.

Activity image UI remains not started until the desktop activity screen task.

Validation

Run:

.\.venv\Scripts\python.exe -m compileall backend desktop_client

When possible, validate database-backed behavior against the configuredPostgreSQL/Supabase connection and real Cloudinary credentials.

Manual HTTP checks:

Manager login succeeds.

Instructor login succeeds.

Customer login succeeds.

Manager can upload an image to an existing activity.

Upload returns saved metadata including public_id and secure_url.

The uploaded file appears in Cloudinary underhavaya-im-neshama/activities.

Manager can list images for an activity.

Instructor can list images for an active activity.

Customer can list images for an active activity.

Instructor cannot upload or delete images and receives 403.

Customer cannot upload or delete images and receives 403.

Missing activity returns 404.

Unsupported file type is rejected.

Deleting an image removes or deactivates the DB record and calls the Gateway.

Activity detail/list responses expose image URLs according to the chosen APIshape.

Also validate the Gateway boundary:

Search the codebase for direct Cloudinary imports.

Confirm only the infrastructure Gateway imports Cloudinary.

Confirm routers/services depend on the application Gateway abstraction.

Suggested search:

rg "cloudinary" backend

Acceptance Criteria

This task is complete when:

Cloudinary credentials are documented through .env.example placeholders.

Activity images have PostgreSQL/Supabase-compatible persistence.

Image upload goes through an application-owned Gateway abstraction.

Cloudinary SDK usage is isolated to the infrastructure Gateway.

Manager can upload and delete activity images through API routes.

Customers and instructors can view images for active activities only.

Activity catalog API exposes image URLs for display.

Errors are handled cleanly.

PIV documentation and traceability are updated.

Compile validation passes.