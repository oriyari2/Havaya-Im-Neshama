# Task 25.5 — Branded Desktop Visual System and Approved-Screen Styling

## Status

Planned.

This is a presentation-layer milestone under the Desktop visual-design/UI/UX work.
It must be implemented incrementally and must not change existing product behavior.

---

## Goal

Complete the final branded visual-design layer of the PySide6 desktop client for
**Havaya Im Neshama / חוויה עם נשמה**.

The existing system already contains the required operational workflows. This task
does **not** redesign the product architecture or invent new features. It applies
one coherent, professional visual language to the existing Desktop surfaces while
preserving the current MVP, Microfrontend-style module boundaries, CQRS/Event
Sourcing behavior, RBAC, API contracts, and RAG behavior.

The final result should look like a real, professionally designed operational
desktop product for the business, not like a generic AI-generated dashboard.

---

## Course/Project Motivation

The course requires a PySide6 Desktop application, MVP/Microfrontend-style UI
boundaries, and a professional and aesthetic presentation supported by UX/UI
principles.

This task is the final visual implementation pass that turns the already-functional
Desktop client into a cohesive branded product while keeping the project
architecture visible and intact.

---

## Sources of Truth

Functional and architectural behavior remains governed by:

- `AGENTS.md`
- `docs/PRD.md`
- `docs/piv/requirements-traceability.md`
- the current Desktop implementation
- completed PIV documents for prior Desktop tasks
- existing automated tests

The current application is the source of truth for:

- what screens exist;
- what information is shown;
- what actions exist;
- which roles may see or execute each action;
- how Presenters, services, API clients, CQRS commands/queries, Event Sourcing,
  authentication, and RAG behave.

The approved images under `design_reference/` are the source of truth only for
**visual direction**.

They are not functional specifications.

---

## Approved Design References

The repository must contain:

```text
design_reference/
├── logo.png
├── approved-login.png
├── approved-dashboard.png
├── approved-customers.png
├── approved-orders.png
├── approved-ai.png
├── activity-dashboard-hero.png
└── activity-customers-hero.png
```

Reference meaning:

- `logo.png`
  - the only approved brand logo;
  - do not redraw, regenerate, replace, or reinterpret it.

- `approved-login.png`
  - approved visual direction for the Login screen.

- `approved-dashboard.png`
  - approved visual direction for the Dashboard.

- `approved-customers.png`
  - approved visual direction for Customers.

- `approved-orders.png`
  - approved visual direction for the existing Booking/Orders management workspace.

- `approved-ai.png`
  - approved visual direction for the AI Advisor conversation screen.

- `activity-dashboard-hero.png`
  - approved hero image for Dashboard only.

- `activity-customers-hero.png`
  - approved hero image for Customers only.

Do not generate additional fake business photography during implementation.

---

## Required Project Skill

This task must use the reusable project skill:

```text
skills/havaya-desktop-ui/SKILL.md
```

Skill name:

```text
havaya-desktop-ui
```

The skill defines the reusable inspect → preserve behavior → style → visually
validate → regress → report workflow for all screen phases in this task.

### Skill usage rule

For every Task 25.5 implementation phase:

1. load/use the `havaya-desktop-ui` skill before making UI changes;
2. follow its hard boundaries and workflow;
3. state in the final phase report that the skill was used;
4. if the Codex runtime does not expose the skill through explicit skill
   invocation, read `skills/havaya-desktop-ui/SKILL.md` directly and follow it
   as the implementation playbook.

The skill is reusable guidance. This task file remains authoritative for product
scope and acceptance criteria.

---

## Non-Negotiable Functional Boundaries

Task 25.5 MUST NOT:

- add new product functionality;
- remove existing functionality;
- add new navigation destinations;
- invent new actions, filters, statuses, queues, metrics, or workflows;
- change backend behavior;
- change API contracts;
- change authentication or authorization;
- change RBAC;
- change CQRS behavior;
- change Event Sourcing behavior;
- change booking domain semantics;
- change database/repository behavior;
- change Cloudinary/Gateway behavior;
- change RAG retrieval, grounding, role filtering, citations, or abstention;
- allow the Desktop client to connect directly to PostgreSQL/Supabase;
- move business logic into PySide6 Views;
- weaken existing MVP boundaries;
- refactor unrelated code.

Presenter behavior may be touched only when an extremely small presentation
integration adjustment is strictly required, and only if business behavior
remains unchanged.

Existing signals, service calls, API calls, role visibility, and workflow
semantics must remain stable.

---

## Design Objective

The product should feel:

- professional;
- warm;
- modern;
- trustworthy;
- calm;
- clearly branded as "חוויה עם נשמה";
- operational rather than promotional;
- distinctive without being childish;
- suitable for a real Windows Desktop management product.

The interface must **not** feel like:

- a generic AI dashboard;
- a template marketplace admin panel;
- a marketing landing page;
- a children's game;
- a glassmorphism showcase;
- a collection of unrelated rounded rectangles;
- an image collage;
- a neon interface.

---

## Visual Language

### Brand palette

Derive the restrained palette from the approved logo.

Use approximately:

- warm off-white / near-white for application surfaces;
- deep navy-charcoal for primary text;
- teal/turquoise as the principal interactive brand color;
- sky blue as a secondary accent;
- leaf green for positive/approved states;
- warm orange for secondary attention states;
- muted coral/red only for destructive/cancelled/error states.

Avoid highly saturated neon colors.

Status must always remain understandable from readable text, not color alone.

### Typography

Use a Windows-safe font stack already compatible with the project, preferably
Segoe UI unless the current project defines another suitable local font.

Do not introduce external font downloads or font dependencies.

Create a clear visual hierarchy for:

- screen titles;
- subtitles;
- section headings;
- statistic values;
- table headers;
- body text;
- form labels;
- metadata;
- status labels.

### Spacing

Use a consistent spacing rhythm, preferably based on an 8 px scale where
practical.

Increase breathing room compared with the current neutral UI, while preserving
useful Desktop data density.

Do not waste vertical space needed by operational tables.

### Geometry

Use:

- restrained corner radii;
- thin, subtle borders;
- minimal visual elevation;
- shadow only where it clearly improves hierarchy.

Avoid putting every small control inside another bordered card.

---

## Shared Application Shell

The existing right-side application navigation remains the common shell.

Preserve:

- the current navigation destinations;
- their current order unless the existing implementation already defines role
  ordering differently;
- role-based visibility;
- current navigation signals;
- logged-in user email;
- existing logout behavior.

Apply:

- the real `logo.png` at the top;
- consistent line-style icons;
- subtle hover states;
- visible keyboard focus;
- clear but restrained active state;
- consistent spacing and typography.

Do NOT add:

- a clock;
- compass;
- promotional panel;
- arbitrary sidebar photography;
- extra menu items.

---

## Shared Component System

Prefer extending the existing shared Desktop design infrastructure rather than
creating a second independent styling system.

Inspect and reuse, where present:

- `design_tokens.py`;
- shared QSS/style generation;
- management/common View helpers;
- shared buttons;
- shared form controls;
- shared tables;
- shared dialogs;
- shared pagination;
- shared status rendering.

Centralize reusable presentation rules for:

- brand colors;
- semantic colors;
- typography;
- spacing;
- borders/radii;
- primary buttons;
- secondary buttons;
- destructive buttons;
- text inputs;
- combo boxes;
- search controls;
- table headers;
- table rows/selection;
- status badges;
- pagination;
- navigation items;
- page headers;
- statistic cards;
- dialogs;
- AI user message bubbles;
- AI assistant message bubbles;
- AI source/reference blocks.

Avoid duplicated page-local QSS when a shared solution fits the current
architecture.

Do not perform a large refactor solely to achieve style reuse.

---

## Image Rules

Photography is optional and must be restrained.

Use only the two approved UI hero assets:

```text
design_reference/activity-dashboard-hero.png
design_reference/activity-customers-hero.png
```

Rules:

- use them only on their approved screens;
- use them as narrow header/hero material;
- crop without stretching;
- use a fade/overlay/neutral transition so text remains readable;
- preserve aspect ratio;
- never place them in table rows;
- never place them in arbitrary statistic cards;
- never use them as sidebar decoration;
- do not repeat one image across multiple unrelated screens;
- do not generate replacement business photos.

---

# Screen Targets

## Dashboard

Visual reference:

```text
design_reference/approved-dashboard.png
```

Hero:

```text
design_reference/activity-dashboard-hero.png
```

Preserve all current Dashboard functionality, including the existing:

- six summary metrics;
- meanings of those metrics;
- drill-down/open actions;
- quick action/navigation controls;
- upcoming-bookings operational section;
- instructor/open-work section;
- role visibility;
- Presenter/service behavior.

Visual goals:

- narrow activity hero at the top;
- smooth fade into the neutral content surface;
- strong RTL title/subtitle hierarchy;
- six balanced statistic cards;
- restrained category color accents;
- clean quick-action row;
- crisp, practical tables;
- shared branded sidebar.

Do not add:

- clock;
- compass;
- charts;
- trends;
- percentages;
- notifications;
- fake data;
- extra actions.

---

## Customers

Visual reference:

```text
design_reference/approved-customers.png
```

Hero:

```text
design_reference/activity-customers-hero.png
```

Preserve the already-implemented Customer workflow, including current:

- New Customer action;
- search;
- supported filters/sort;
- pagination;
- Customer list;
- open/details flow;
- create/edit/deactivate/reactivate/delete behavior where currently supported;
- Presenter/service/API behavior;
- role restrictions.

Visual goals:

- restrained activity hero in the approved header area;
- strong Customers title/subtitle;
- clear primary action;
- unified search/filter bar;
- readable high-density table;
- polished status labels and row actions;
- consistent pagination;
- shared branded sidebar.

Do not invent a new logo or Customer functionality.

---

## Bookings / Orders Management

Visual reference:

```text
design_reference/approved-orders.png
```

The reference filename uses "orders", but it maps to the existing Booking
management workspace.

Preserve all current Booking behavior, including current:

- queue/summary information;
- search/filter/sort behavior;
- Booking table;
- statuses;
- pagination;
- details/history;
- assignment workflows;
- role restrictions;
- CQRS commands/queries;
- Event Sourcing semantics.

Visual goals:

- strong operational title hierarchy;
- restrained summary cards;
- clean search/filter row;
- highly readable Booking table;
- refined status badges;
- consistent sidebar;
- no unnecessary decorative photography.

Do not add the previously rejected lower-right decorative image.

---

## AI Advisor

Visual reference:

```text
design_reference/approved-ai.png
```

Preserve all existing AI/RAG behavior exactly:

- same consult action;
- same role-aware retrieval;
- same grounded answer semantics;
- same abstention behavior;
- same sources;
- same read-only behavior;
- same input/send workflow.

Recompose only the conversation presentation.

Visual goals:

- real chat-like conversation layout;
- clear distinction between user and assistant messages;
- user messages use one subtle tint;
- assistant messages use a different branded tint;
- use the real logo mark as the assistant avatar/identity marker;
- preserve RTL;
- preserve long-answer readability;
- keep sources visually attached to the assistant answer they support;
- polished bottom composer/input area;
- scrollable conversation.

Do not add:

- file upload;
- conversation history;
- regenerate;
- reactions;
- model selection;
- typing controls;
- unsupported AI actions.

---

## Login

Visual reference:

```text
design_reference/approved-login.png
```

Preserve the authentication workflow exactly.

Use only current:

- email field;
- password field;
- login action;
- current feedback/error behavior.

Visual goals:

- centered branded composition;
- real logo;
- clean hierarchy;
- soft organic background shapes;
- restrained warm/light visual language;
- clear focus states.

Do not add authentication providers.

Do not add a functional Forgot Password workflow if one does not already exist.

---

# Accessibility and RTL

Preserve or improve:

- Hebrew RTL layout;
- readable contrast;
- accessible names;
- keyboard focus;
- logical tab order;
- semantic status text;
- disabled-state readability;
- error readability.

Do not rely on color alone.

Do not solve visual polish by reducing accessibility.

---

# Desktop/Responsive Constraints

The result must remain usable at the Desktop sizes already supported by the
project and tested by the existing UI foundation.

Requirements:

- no essential controls overlap;
- no essential text becomes inaccessible;
- tables retain useful working area;
- hero images crop predictably;
- images never stretch;
- RTL stays correct at supported sizes;
- the shell remains stable for all roles.

---

# Implementation Plan

Task 25.5 MUST be implemented in bounded phases.

## Phase 0 — Skill

Create/verify:

```text
skills/havaya-desktop-ui/SKILL.md
```

Use it for every later phase.

Do not begin screen implementation until the skill and design references are
available.

## Phase 1 — Inspect + Shared Visual Foundation

Inspect the current Desktop visual architecture.

Establish/extend the shared branded design system.

Screen-specific redesign is not part of this phase.

The common shell/sidebar may be styled here because it is shared.

Stop and report.

## Phase 2 — Dashboard

Implement only Dashboard.

Validate and stop.

## Phase 3 — Customers

Implement only Customers.

Validate and stop.

## Phase 4 — Bookings

Implement only Booking/Orders management.

Validate and stop.

## Phase 5 — AI Advisor

Implement only AI Advisor conversation presentation.

Validate and stop.

## Phase 6 — Login

Implement only Login.

Validate and stop.

## Phase 7 — Cross-Screen Consistency Pass

Inspect the five approved surfaces together.

Fix only visual inconsistencies or regressions.

Do not add features.

Run final Desktop regression validation.

---

# Validation

After each implementation phase, run focused tests relevant to that phase.

Use the project's Qt offscreen convention where applicable:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
```

At minimum run:

```powershell
.\.venv\Scripts\python.exe -m compileall backend desktop_client
git diff --check
```

Also run the relevant Desktop unit/UI tests.

Before Task 25.5 completion, run the full Desktop regression suite.

Preserve existing architecture-boundary verification, including:

- Presenters remain Qt-free where the project currently requires it;
- Desktop contains no direct PostgreSQL/Supabase access;
- server-side authorization remains authoritative.

Do not make tests brittle by asserting exact pixels unless the existing test
architecture already does so.

Prefer behavioral and structural UI assertions.

---

# Visual Validation

For every screen phase:

1. run/instantiate the actual PySide6 screen;
2. compare it with the corresponding approved reference;
3. treat the reference as design intent, not pixel-perfect HTML/CSS;
4. adapt only where PySide6/QSS limitations require it;
5. document meaningful deviations.

If project screenshot capture already exists, save evidence under:

```text
docs/screenshots/
```

Suggested names:

```text
task-25-5-dashboard.png
task-25-5-customers.png
task-25-5-bookings.png
task-25-5-ai.png
task-25-5-login.png
```

Do not generate replacement mockups during implementation.

---

# Documentation

Create/update:

```text
docs/piv/25-5-branded-desktop-visual-system.md
```

The PIV must document:

- the reusable skill used;
- visual system implemented;
- approved references used;
- files changed;
- functional boundaries preserved;
- tests run;
- visual validation performed;
- justified deviations/limitations;
- current phase status.

Update:

```text
docs/piv/requirements-traceability.md
```

only where the visual/UX requirement status meaningfully changes.

Do not claim pixel-perfect similarity if it was not achieved.

---

# Completion Criteria

Task 25.5 is complete only when:

- all five approved surfaces share one coherent design language;
- the real logo is used consistently;
- only approved hero imagery is used;
- the UI is professional and aesthetically coherent;
- RTL is correct;
- keyboard/focus/accessibility behavior is preserved or improved;
- no unsupported functionality was introduced;
- all existing workflows still work;
- architecture boundaries remain intact;
- focused tests pass;
- full Desktop regression passes;
- compile validation passes;
- PIV documentation is complete.

---

# Scope Discipline

Do not begin unrelated functional work.

Do not refactor unrelated code.

Do not commit or push unless explicitly instructed by the product owner.

After each bounded phase, report and stop when the current Codex prompt says to
stop.
