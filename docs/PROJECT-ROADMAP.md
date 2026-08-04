# Experience-with-Soul: Current Project Roadmap

## 1. Authority

`docs/PRD.md` remains the product source of truth. Historical task and PIV files
remain evidence of the development process. This roadmap describes the current
state of the supplied final source tree and supersedes older future-task
numbering preserved in historical notes.

## 2. Current state

| Workstream | Current state | Evidence |
|---|---|---|
| Core backend / persistence / seed | Complete | Tasks/PIV 01–03 |
| Auth, RBAC, Customers, Activities, Gateway | Complete | Tasks/PIV 04–07 |
| Booking CQRS / Event Sourcing / Dashboard | Complete | Tasks/PIV 08–12 |
| Ollama / RAG / grounded AI / knowledge management | Complete for MVP | Tasks/PIV 13–18 + current runtime code |
| Activity image Desktop workflow | Complete | Task/PIV 19 |
| Shared Desktop UX/accessibility foundation | Complete | Task/PIV 20 |
| Manager account administration | Complete | Task/PIV 21 |
| Non-blocking Desktop execution | Complete | Task/PIV 22 |
| Performance/cache/refresh reduction | Complete | Task/PIV 23 |
| Booking request/assignment closure | Complete | Task/PIV 24–24.3 |
| Professional branded Desktop UX | Complete for current MVP | Task/PIV 25.x + final consolidation |
| Code-level final regression | Complete | `docs/piv/final-validation.md` |
| Packaging / clean-machine demo / final submission audit | Remaining | local/release environment |

## 3. Final implementation gate

The product-feature gate is closed unless a real acceptance defect is found.
Do not add a new feature only to satisfy historical roadmap numbering.

The current final-regression inventory is 480 tests: 229 backend and 251
Desktop. Backend discovery passed 229/229. Desktop modules pass in fresh
processes; long mixed PySide6 GUI runs may terminate natively on Windows, so GUI
regression is validated in process isolation.

## 4. Remaining submission sequence

### Step A — Repository cleanliness

```powershell
git diff --check
git status --short
```

Commit the final documentation/test updates and push the submission branch.
Confirm that no `.env`, token, password, Cloudinary secret or database secret is
tracked.

### Step B — Native Windows/demo-machine readiness

- install documented Python dependencies;
- start Docker/Ollama;
- pull `llama3.1` and `nomic-embed-text-v2-moe`;
- verify the configured PostgreSQL/Supabase connection;
- verify Cloudinary upload/display;
- call manager-only `/api/ai/readiness`;
- start the Desktop application and verify Hebrew/RTL rendering.

### Step C — Acceptance rehearsal

Demonstrate:

1. Manager login and role navigation.
2. Customer and Activity management.
3. Activity image through the Gateway.
4. Booking creation, event-sourced update, assignment and history.
5. Instructor role visibility.
6. Customer ownership isolation and own bookings/catalog.
7. RAG consultation with source citations and insufficient-context abstention.
8. Manager knowledge-source management.

### Step D — Final grading interpretation checks

Resolve two wording-sensitive items with the lecturer if necessary:

- the repository pins `PySide6==6.9.1`; confirm this satisfies the assignment's
  `6/6.5 PySide` wording;
- the repository now includes both the Cloudinary image Gateway and a
  domain-specific OpenRouteService `RouteGateway` for Booking distance/duration;
  perform one live calculation on the demonstration machine.

### Step E — Submission materials

Capture current native Windows screenshots, include the architecture and
traceability documents, preserve all PIV artifacts, and prepare a concise demo
script.

## 5. Definition of final ready

The project is submission-ready when:

- the final Git state is clean and pushed;
- setup works on the demonstration machine;
- live PostgreSQL, Cloudinary and Ollama checks pass;
- the acceptance scenario is rehearsed;
- current screenshots match the final UI;
- no known critical/high defect remains;
- the lecturer-specific PySide interpretation is resolved if required, and a
  live OpenRouteService travel calculation has been demonstrated.
