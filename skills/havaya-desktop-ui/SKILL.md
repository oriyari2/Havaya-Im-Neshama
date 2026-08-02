---
name: havaya-desktop-ui
description: Apply the approved Havaya Im Neshama brand and UI/UX system to one existing PySide6 desktop screen at a time while preserving all functionality, RTL, MVP boundaries, accessibility, and regression safety.
---

# Havaya Desktop UI Skill

## Purpose

Use this skill whenever implementing or reviewing branded UI/UX changes for the
PySide6 Desktop client of **Havaya Im Neshama / חוויה עם נשמה**.

This skill is intentionally reusable across:

- shared shell/design-system work;
- Dashboard;
- Customers;
- Bookings;
- AI Advisor;
- Login;
- final cross-screen consistency review.

The skill governs **how** to perform the UI work safely and consistently.

The current task file and PRD govern **what** the product is allowed to do.

---

## Required Inputs

Before editing code, read:

1. `AGENTS.md`
2. the current task file
3. relevant PIV documents
4. relevant existing View/Presenter/service code
5. the matching `design_reference/approved-*.png`
6. `design_reference/logo.png`
7. any explicitly approved screen-specific hero asset

Do not infer functionality from a mockup.

The existing implementation is the functional source of truth.

---

## Hard Guardrails

Never use a visual redesign as justification to:

- add functionality;
- remove functionality;
- add navigation;
- invent metrics, filters, statuses, controls, or workflows;
- change backend/API behavior;
- change CQRS/Event Sourcing semantics;
- change RAG behavior;
- change RBAC;
- move business logic into the View;
- connect the Desktop directly to the database;
- refactor unrelated architecture.

Do not generate or substitute a new logo.

Do not generate additional fake business photography.

---

# Workflow

Follow this sequence for every phase.

## 1. Inspect

Inspect the existing implementation before changing it.

Identify:

- View class(es);
- Presenter contract;
- service/API interactions;
- signals and slots;
- role-dependent visibility;
- shared widgets/helpers;
- current object names/properties used by QSS;
- shared design tokens;
- table model/delegate behavior;
- focus/tab behavior;
- existing tests.

Write down the functional contract mentally before styling.

Do not redesign from the screenshot alone.

---

## 2. Map the Reference to Existing Functionality

Open the approved reference for the current screen.

Classify every visible reference element as one of:

- existing functional element → style/reposition it;
- decorative approved element → may implement if explicitly allowed by the task;
- unsupported functional-looking element → do not implement;
- visual approximation → adapt to PySide6 without changing behavior.

If the mockup conflicts with the real application, preserve application
functionality and use the mockup only for design intent.

---

## 3. Reuse the Shared Design System

Prefer existing shared tokens/helpers.

Before adding page-local styling, check whether the requirement belongs in:

- shared brand colors;
- shared typography;
- button roles;
- input roles;
- table style;
- status badges;
- navigation;
- page header;
- statistic cards;
- chat messages;
- image helper.

Do not create a new QSS system when the project already has one.

Do not over-abstract a single visual edge case.

---

## 4. Implement with PySide6 Constraints in Mind

Keep layout responsive to the project's supported Desktop sizes.

Prefer Qt layouts over manual absolute positioning.

Preserve RTL deliberately.

For imagery:

- preserve aspect ratio;
- crop rather than stretch;
- use only approved assets;
- keep text readable over/near images;
- avoid making images the main content on operational screens.

For cards:

- use modest radii;
- thin borders;
- minimal shadow/elevation;
- do not nest boxes without a hierarchy reason.

For tables:

- prioritize scanning and density;
- preserve header clarity;
- preserve sort/selection behavior;
- preserve enough vertical working area;
- keep statuses text-readable.

For forms:

- align labels and fields consistently;
- provide visible focus;
- preserve error states;
- preserve keyboard usability.

Do not add external UI libraries unless the task explicitly approves them.

---

## 5. Check Visual Hierarchy

Before testing, inspect the screen for:

- one clear primary page title;
- restrained subtitle;
- obvious primary action;
- consistent spacing;
- aligned controls;
- coherent colors;
- no unnecessary icons;
- no excessive rectangles;
- no random imagery;
- table readability;
- clear active navigation;
- consistent status treatment.

The result should feel like one product, not a set of independently styled
widgets.

---

## 6. Accessibility and RTL Check

Verify:

- Hebrew RTL is correct;
- tab/focus order is logical;
- visible focus is retained;
- contrast is readable;
- disabled controls are understandable;
- status does not rely only on color;
- icons do not replace necessary text;
- long Hebrew text does not become inaccessible.

---

## 7. Behavioral Regression Check

Confirm that styling did not change:

- emitted signals;
- Presenter calls;
- service/API calls;
- role visibility;
- data loading;
- pagination;
- filtering;
- table selection;
- dialogs;
- mutations;
- navigation.

Run focused tests.

---

## 8. Visual Comparison

Compare the real PySide6 result with the approved reference.

Do not chase pixel perfection.

Evaluate:

- hierarchy;
- spacing;
- proportions;
- brand feel;
- image placement;
- control grouping;
- table density;
- sidebar consistency.

If PySide6/QSS cannot reproduce an effect safely, choose the simplest
professional approximation and document it.

---

## 9. Validate

Use:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
```

Run relevant tests plus:

```powershell
.\.venv\Scripts\python.exe -m compileall backend desktop_client
git diff --check
```

Run broader Desktop regression when the task/prompt requires it.

---

## 10. Report and Stop

For every bounded screen phase, report:

1. skill used;
2. files changed;
3. visual changes;
4. design references/assets used;
5. functional behavior explicitly preserved;
6. tests/results;
7. visual validation result;
8. PySide6/QSS limitations or deviations.

If the prompt says to stop after one screen, stop.

Do not continue to the next screen automatically.

---

# Brand Rules

## Logo

Use only:

```text
design_reference/logo.png
```

Do not redraw it.

For AI assistant identity, use the approved real logo/mark rather than a generic
AI robot or sparkle identity where the task/reference requests a brand avatar.

## Colors

Use restrained variants of:

- teal/turquoise;
- sky blue;
- leaf green;
- warm orange;
- muted coral/red;
- warm off-white;
- navy-charcoal text.

Avoid neon.

## Images

Approved screen-specific hero images only.

Do not use marketing flyers as UI backgrounds.

Do not use stock-photo-style collages.

---

# Anti-Patterns

Reject these patterns unless the existing product specifically needs them:

- every section inside a thick rounded card;
- multiple nested borders;
- large gradients;
- glassmorphism;
- glowing buttons;
- giant decorative icons;
- AI sparkle icons everywhere;
- huge empty whitespace that reduces table usability;
- random illustration in the sidebar;
- visual status represented only by color;
- image stretching;
- page-specific color systems that do not match other screens.

---

# Final Quality Checklist

Before considering a screen complete, answer YES to all:

- Is existing functionality unchanged?
- Is the approved reference clearly reflected?
- Is the real logo used correctly?
- Is the screen consistent with the shared brand system?
- Is RTL correct?
- Is keyboard/focus behavior preserved?
- Are tables/forms still practical?
- Are unsupported mockup features excluded?
- Are approved images used only where allowed?
- Did focused tests pass?
- Did compile validation pass?
- Did `git diff --check` pass?
- Was the PIV updated when required?
