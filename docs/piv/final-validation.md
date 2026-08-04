# PIV — Final Regression and Submission-Readiness Validation

## Plan

The final validation pass had four goals:

1. verify that the implemented backend and Desktop behavior still matches the
   approved PRD after the performance and visual-design work;
2. update stale tests that encoded superseded UI geometry without weakening
   behavioral coverage;
3. run the full backend regression and every Desktop test module;
4. document the remaining submission checks separately from implemented
   product behavior.

No production behavior was changed merely to satisfy an obsolete visual test.
Where a test expected an earlier table shape, dialog layout, hero size, action
position, or message text, the test was updated only after the current View
contract was inspected.

## Implement

### Regression-test maintenance

The final maintenance pass aligned Desktop tests with the current UI while
preserving functional assertions for:

- Customer, Instructor and Manager list-to-details workflows;
- row actions at the end of the current semantic tables;
- current RTL dialog labels exposed through shared dialog properties;
- current shared dialog geometry and validation behavior;
- current branded Customer hero and eight-column Customer table contract;
- current Hebrew AI-unavailable presentation;
- current Login copy and feedback lifecycle;
- role/lifecycle controls, status badges, keyboard navigation and pagination.

### Current architecture verified during the pass

The regression review confirmed that the final code still preserves the major
architectural boundaries:

```text
PySide6 View
    -> Qt-free Presenter
        -> Desktop Service
            -> ApiClient
                -> FastAPI router
                    -> application service / command / query
                        -> domain / repository / Gateway
                            -> PostgreSQL / Cloudinary / Ollama
```

Booking writes remain event-sourced. Desktop Views do not access PostgreSQL.
Server-side RBAC remains authoritative. AI consultation remains read-only and
grounded in approved role-filtered knowledge.

## Validate

### Automated test inventory

Static discovery of the final repository contains:

| Test area | Test methods | Files |
|---|---:|---:|
| Backend | 229 | 18 |
| Desktop | 251 | 26 |
| **Total** | **480** | **44** |

### Backend result

The final backend unittest discovery completed successfully:

```powershell
python -m unittest discover -s backend/tests -p "test_*.py" -v
```

Result: **229/229 passed**.

Coverage includes authentication/RBAC, Customer and Instructor lifecycle,
Booking commands/queries/Event Sourcing/replay, demo data, user administration,
RAG ingestion/retrieval, grounded AI consultation, runtime configuration and
knowledge management.

### Desktop result

All Desktop test modules were validated successfully. The updated final modules
include, among others:

- Customers: 16/16;
- Instructors: 8/8;
- Managers/Users: 9/9;
- Presenters: 27/27;
- Background operations: 10/10;
- Booking workspace: 11/11;
- general Views: 11/11;
- UI foundations: all assertions validated, with the tail of the module also
  executed individually after a native Qt process termination.

The full Desktop inventory is **251 tests**.

### PySide6/Qt test-runner limitation

On Windows, long mixed GUI runs can terminate the Python process with a native
Qt access violation without producing a unittest assertion failure. The exact
termination point moved between unrelated widget constructors, while the same
modules passed in fresh processes. The final regression therefore validates GUI
test files in process isolation rather than treating one unstable shared Qt
process as product behavior.

This limitation is a **test-runner/native-lifecycle issue**, not a known
functional failure in the validated workflows. For final verification, run GUI
modules separately if a combined discovery process terminates without an
assertion traceback.

### Compilation

The supplied final source tree passes:

```powershell
python -m compileall backend desktop_client rag
```

The compile pass reports two existing Python `SyntaxWarning` messages in demo
seed SQL string literals containing `\s`; they do not prevent compilation.

### Final local checks still required before submission

The source ZIP does not contain trustworthy Git repository state or live cloud
credentials. Therefore the following remain **environment/release checks**, not
implementation gaps:

```powershell
git diff --check
git status --short
```

Also verify on the actual demonstration machine:

- Docker Desktop starts the Ollama container;
- `llama3.1` and `nomic-embed-text-v2-moe` are installed;
- the configured cloud PostgreSQL/Supabase database is reachable;
- Cloudinary credentials are configured only in local environment settings;
- a native Windows run displays Hebrew fonts correctly;
- the complete manager → instructor → customer → AI demo scenario is rehearsed.

## Result

**Code-level regression status: PASS.**

No failing backend or Desktop assertion remains in the validated modules. The
remaining work is submission/release evidence: clean Git state, clean-machine
startup, live external-service readiness, final screenshots/demo rehearsal, and
any course-specific packaging requested by the lecturer.
