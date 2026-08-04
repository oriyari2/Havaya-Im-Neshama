# Task 25.6 — Feature-First Desktop Microfrontend Structure

## Plan

The Desktop already had explicit feature registration boundaries, but the
business implementation files still lived in parallel layer-first directories
(`views/`, `presenters/`, `services/`). For final course presentation, the goal
of this refactor is to make the Microfrontend boundary visible both logically
and physically without changing runtime behavior.

Constraints:

- no intentional UI or styling changes;
- no signal/slot behavior changes;
- no API contract changes;
- no role/authorization changes;
- no Event Sourcing, RAG or database changes;
- preserve the same View/Presenter/service implementations and public flows.

## Implement

Business source is now grouped by feature:

```text
desktop_client/app/features/
├── auth/
├── dashboard/
├── activities/
├── customers/
├── instructors/
├── users/
├── bookings/
├── knowledge/
└── ai_assistant/
```

Each package contains its own `registration.py` plus its feature-specific View,
Presenter and service adapter. Dialogs and formatting helpers remain with the
feature when they are feature-specific.

Reusable infrastructure was extracted to:

```text
desktop_client/app/shared/
├── navigation.py
├── formatting.py
├── validation/
└── ui/
```

The old parallel business `views/`, `presenters/` and `services/` packages are
removed, so there is one physical owner for each business implementation.

`MainWindow` continues to act as the Desktop shell. It composes role-appropriate
features through `features.registry`, while `features.service_factory` creates
the same service instances that were previously created directly in
`MainWindow`.

## Architecture invariant

```text
Desktop Shell
  -> Feature Registry
    -> Feature package
       -> View
       -> Presenter
       -> Service/API adapter
```

MVP remains the internal presentation pattern inside each Microfrontend. Shared
widgets and validation code do not belong to any one business feature and are
therefore kept under `shared/` rather than duplicated.

## Validate

After applying the refactor, run the existing feature/regression suites plus the
architecture test:

```powershell
python -m unittest discover -s desktop_client/tests -p "test_microfrontends.py" -v
python -m unittest discover -s desktop_client/tests -p "test_views.py" -v
python -m unittest discover -s desktop_client/tests -p "test_activity_views.py" -v
python -m unittest discover -s desktop_client/tests -p "test_customer_views.py" -v
python -m unittest discover -s desktop_client/tests -p "test_instructor_views.py" -v
python -m unittest discover -s desktop_client/tests -p "test_user_views.py" -v
python -m unittest discover -s desktop_client/tests -p "test_booking_workspace.py" -v
python -m unittest discover -s desktop_client/tests -p "test_knowledge_management.py" -v
python -m unittest discover -s desktop_client/tests -p "test_presenters.py" -v
python -m compileall backend desktop_client rag
```

Manual validation should confirm that Login, navigation, all role-specific
screens, booking creation/drill-down and the AI Advisor render and behave exactly
as before the structural refactor.

## Result

The intended result is a clearer course-facing Microfrontend implementation:
feature ownership is visible directly in the source tree, while the existing
MVP behavior and user experience remain unchanged.
