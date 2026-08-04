# Task 22 PIV — Desktop Background Execution and Non-Blocking UI

## Status

Design, bounded implementation, automated validation, and documentation are
complete. The requested commit and push close the task.

## What was created

- A plain `OperationExecutor` port and lifecycle identity model for Qt-free
  Presenters.
- A deterministic immediate adapter for Presenter unit tests.
- A production `QtOperationExecutor` using a private `QThreadPool`, four-worker
  concurrency, 32-operation capacity, queued UI-thread delivery, cancellation
  by result suppression, session invalidation, and bounded shutdown waiting.
- Composition-level session-expiry dispatch safe for callbacks originating on a
  worker thread.
- Page, logout, session-expiry, and shutdown invalidation.
- Background migration of Login, Dashboard, Customers, Customer profile,
  Instructors, Instructor profile, and User Administration operations.
- Deterministic responsiveness/lifecycle tests.

## Requirements advanced

- `NFR-03`: ordinary pilot HTTP work no longer occupies the Qt event loop.
- `NFR-06`: operation failures cross the worker boundary through controlled,
  friendly error paths.
- `NFR-07`: Views remain passive and Presenters remain Qt-independent.
- `NFR-08`: bounded operation capacity and deterministic lifecycle cleanup.

No PRD requirement, backend API contract, schema, CQRS/Event Sourcing behavior,
Gateway behavior, authorization rule, or AI/RAG behavior changed.

## Files changed

Production desktop:

- `desktop_client/app/models/operation.py`
- `desktop_client/app/infrastructure/__init__.py`
- `desktop_client/app/infrastructure/qt_operations.py`
- `desktop_client/app/main.py`
- `desktop_client/app/features/auth/presenter.py`
- `desktop_client/app/features/dashboard/presenter.py`
- `desktop_client/app/features/customers/presenter.py`
- `desktop_client/app/features/instructors/presenter.py`
- `desktop_client/app/features/users/presenter.py`

Tests and documentation:

- `desktop_client/tests/test_background_operations.py`
- `tasks/22-desktop-background-execution-non-blocking-ui.md`
- `docs/piv/22-desktop-background-execution-non-blocking-ui.md`
- `docs/piv/requirements-traceability.md`
- `docs/PROJECT-ROADMAP.md`
- `ARCHITECTURE.md`

Backend production code, API contracts, database schema, PRD, and AI/RAG code
remain unchanged.

## Measurement

The repeatable probe uses a simulated 200 ms service call:

- before: the direct synchronous call occupies the UI thread for approximately
  200 ms and delays a 20 ms heartbeat;
- after: background submission returns in under 50 ms in the automated test,
  the 20 ms heartbeat runs before service completion, and the completion
  callback is observed on the UI thread.

This demonstrates removal of UI-thread waiting, not faster server execution.

## How to validate

```powershell
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\Scripts\python.exe -m unittest desktop_client.tests.test_background_operations desktop_client.tests.test_presenters desktop_client.tests.test_customers_presenter desktop_client.tests.test_instructors_presenter desktop_client.tests.test_users_presenter -v
.\.venv\Scripts\python.exe -m unittest discover -s desktop_client/tests -v
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
.\.venv\Scripts\python.exe -m compileall backend desktop_client rag
git diff --check
```

Architecture scans must confirm no PySide6/Qt graphics imports in Presenters,
no backend/cloud provider imports in the desktop, and no database access from
the desktop.

## Validation results

- Focused desktop/lifecycle suite: 50 passed.
- Full desktop suite: 159 passed.
- Full backend suite: 185 passed.
- Native Windows Qt application smoke: 2 passed. The real Login and Shell
  opened, delayed authentication and Dashboard/Customer/Instructor/User loads
  ran at 1024×640 and 1200×760, navigation and resizing completed immediately,
  and a 20 ms UI heartbeat fired while background work remained active.
- Compileall, architecture/security scans, and whitespace validation: passed
  before the closing commit.

## Known bounded limitations

- Task 22 deliberately migrates the approved representative pilot rather than
  every synchronous desktop operation.
- Cancellation suppresses obsolete callbacks; it cannot roll back a mutation
  already committed by FastAPI.
- Search is explicit-submit in the pilot, so keystroke debounce is not used.
- API/query optimization, refresh reduction, and safe caching remain Task 23.
- Visual redesign remains Phase 3.

## Next task

Task 23 — API Performance, Refresh Reduction, and Safe Local Caching.
