---
name: havaya-desktop-ui
description: Apply the approved Havaya Im Neshama brand and UI/UX system to one existing PySide6 desktop screen at a time while preserving all functionality, content reachability, RTL/right alignment, MVP boundaries, accessibility, and regression safety.
---

# Havaya Desktop UI Skill

## Purpose

Use this skill whenever implementing or reviewing branded UI/UX changes for the
PySide6 Desktop client of **Havaya Im Neshama / חוויה עם נשמה**.

This skill is reusable across:

- shared shell/design-system work;
- Dashboard;
- Customers;
- Bookings;
- AI Advisor;
- Login;
- final cross-screen consistency review.

The skill governs **how** to perform UI work safely and consistently.

The current task file and PRD govern **what** the product is allowed to do.

---

# Core Principle

A visual improvement is successful only if the application remains fully usable.

Never trade functionality, visibility, reachability, readability, RTL correctness,
role behavior, keyboard access, or data density for decoration.

The real running PySide6 application is the final source of truth for whether a
layout works.

A mockup is a visual target, not permission to hide, remove, compress, or invent
functionality.

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

# Hard Guardrails

Never use a visual redesign as justification to:

- add functionality;
- remove functionality;
- hide functionality;
- add navigation;
- invent metrics, filters, statuses, controls, or workflows;
- change backend/API behavior;
- change CQRS/Event Sourcing semantics;
- change RAG behavior;
- change RBAC;
- move business logic into the View;
- connect the Desktop directly to the database;
- refactor unrelated architecture;
- overwrite approved design-reference assets;
- replace working shared UI infrastructure without auditing all consumers.

Do not generate or substitute a new logo.

Do not generate additional fake business photography.

---

# Safe-Editing / Do-Not-Overwrite Rules

Before changing a shared View, helper, design token, stylesheet, or asset:

1. inspect all current consumers;
2. preserve existing public names/properties where practical;
3. prefer extending shared infrastructure over replacing it;
4. keep backward-compatible aliases when renaming shared APIs would create
   unnecessary churn;
5. do not overwrite `design_reference/*`;
6. if a runtime-transformed/cropped asset is required, create a new Desktop-owned
   asset under `desktop_client/app/assets/...`;
7. keep changes presentation-focused and minimal.

If a shared stylesheet change affects multiple screens, visually/regression-check
the affected shared surfaces before declaring the phase complete.

Never "fix" one screen by breaking another.

---

# Global RTL and Alignment Rules

The entire application is a Hebrew-first RTL Desktop application.

RTL/right alignment is the **default visual behavior across the product**.

## Global rule

All screen-level Views should use:

- `Qt.RightToLeft` layout direction;
- right-aligned Hebrew text;
- right-aligned section titles;
- right-aligned page titles and subtitles;
- right-aligned field labels;
- right-aligned card titles and values;
- right-aligned Hebrew button labels where appropriate;
- right-aligned Hebrew table headers and textual cells where semantically appropriate.

Do not rely only on inherited RTL behavior.

Where PySide6 widgets do not visually align correctly through layout direction
alone, set explicit alignment, for example:

```python
Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
```

Use explicit alignment for important labels when needed.

## Visual consistency

The application should have a consistent visual right edge.

Within a screen, related elements should align to the same right-side grid where
practical:

- page title;
- subtitle;
- section headings;
- cards;
- form labels;
- search/filter labels;
- table headings;
- informational text.

Avoid situations where one Hebrew label is centered, another is left-aligned,
and another is right-aligned without a functional reason.

## Mixed-direction exceptions

Do **not** force RTL/right alignment blindly onto data that is naturally LTR.

Examples that may keep LTR or specialized alignment:

- email addresses;
- URLs;
- technical identifiers;
- UUIDs;
- file names;
- phone numbers where LTR improves readability;
- numeric-only values;
- dates and times;
- code snippets;
- English-only content.

Use existing mixed-direction helpers where available.

The surrounding Hebrew label/container should still participate in the RTL
layout.

Example:

```text
דוא"ל: manager@example.com
```

The Hebrew label belongs to the RTL layout, while the email value may render LTR.

## Tables

For Hebrew tables:

- Hebrew column headers should normally be right-aligned;
- Hebrew textual cells should normally be right-aligned;
- numeric columns may use centered/right numeric alignment consistently;
- date/time columns may use a consistent numeric alignment;
- technical IDs may use LTR alignment if needed.

Do not use one blanket alignment for every data type if it reduces readability.

## Forms

Forms should follow Hebrew RTL structure:

- labels on the right;
- fields aligned consistently;
- Hebrew input starts from the right;
- LTR inputs such as email/technical values may use LTR text direction;
- validation/error messages should be right-aligned Hebrew.

## Cards

Statistic/information cards should follow a consistent RTL hierarchy.

Example:

```text
                        כותרת
                           22
                        פתיחה
```

Card title, value, and related textual actions should align consistently to the
right unless the approved design reference explicitly requires another layout.

## Buttons

Hebrew button labels should be RTL-aware and visually consistent with the rest of
the screen.

Do not center or left-align Hebrew button text merely because the default Qt
appearance looks acceptable.

Balanced internal padding should still be preserved.

## Validation

Every screen-specific phase must visually verify RTL/right alignment in the
**real running application**.

Check at minimum:

- page title;
- subtitle;
- card labels;
- card values;
- section headings;
- buttons;
- forms;
- table headers;
- table textual cells;
- validation/error text.

If Hebrew text is unexpectedly centered or left-aligned without a clear reason,
the phase is not complete.

---

# Layout Safety Rules

These rules are mandatory for every screen.

## Nothing important may be clipped

No essential content may be:

- cut off;
- hidden behind another widget;
- rendered outside the visible layout;
- inaccessible because of a fixed height;
- inaccessible because a parent container refuses to grow;
- obscured by an image or decorative layer.

Avoid fixed heights for content containers unless the content size is truly fixed.

Prefer:

- minimum heights;
- layout-managed geometry;
- expanding/Preferred size policies;
- `QScrollArea` when content may exceed the available viewport.

## Everything must remain reachable

If the full screen content can exceed the supported window height:

- make the page content vertically scrollable;
- use `QScrollArea.setWidgetResizable(True)`;
- prefer vertical scrollbar `AsNeeded`;
- avoid horizontal scrolling unless the product genuinely requires it;
- keep global navigation/sidebar fixed where appropriate.

Tables may keep their own internal scrolling while the outer page remains
scrollable.

The user must always be able to reach:

- the last control;
- the last table/section;
- pagination;
- primary actions;
- save/cancel/close actions;
- page bottom.

## No accidental horizontal overflow

At supported Desktop widths:

- labels must not push controls off-screen;
- quick-action rows must wrap/reflow or size safely;
- tables should use practical column sizing;
- horizontal scrollbars should not appear because of decorative padding.

## Role-specific layouts must stay valid

Manager, Instructor, Customer, or other roles may have different content.

Never force one role's mockup structure onto another role.

Apply the same design language while preserving each role's existing functional
layout and visibility rules.

---

# Readability and Contrast Rules

Readability is mandatory.

## Text contrast

Normal body/control text should target WCAG-style contrast of at least **4.5:1**
against its background where practical.

Large display text should target at least **3:1**.

Do not place important text directly on a busy image without a reliable
readability treatment.

Acceptable treatments include:

- separate clean text panel;
- solid/light surface beside the image;
- sufficiently opaque overlay;
- controlled fade from image into neutral surface.

Do not rely on a subtle gradient if real text remains hard to read.

## Status communication

Color must never be the only status indicator.

Keep readable Hebrew status text.

## Font sizing

Do not reduce font size merely to force content to fit.

Fix the layout first.

## Truncation

Use ellipsis/tooltips only for secondary or naturally truncatable fields.

Do not truncate:

- page titles;
- primary actions;
- essential labels;
- critical status text.

---

# Image Safety Rules

Use only approved assets.

For every image:

- preserve aspect ratio;
- crop rather than stretch;
- never distort;
- never cover essential text;
- never consume excessive operational space;
- keep the image subordinate to the screen's job.

Before using an image, inspect whether the file itself contains large
transparent/white margins.

If a runtime crop is needed:

- keep the approved reference untouched;
- create a separate runtime asset;
- do not alter the logo artwork itself.

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
- scroll behavior;
- size policies;
- fixed/min/max sizes;
- existing tests.

Before layout changes, explicitly identify any existing:

- `setFixedHeight`;
- `setMaximumHeight`;
- `setFixedWidth`;
- restrictive `QSizePolicy`;
- nested `QScrollArea`;
- layout stretch factors.

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
- image helper;
- scroll/page scaffold.

Do not create a new QSS system when the project already has one.

Do not over-abstract a single visual edge case.

---

## 4. Implement with PySide6 Constraints in Mind

Prefer Qt layouts over manual absolute positioning.

Preserve RTL deliberately.

Use:

- `QVBoxLayout`, `QHBoxLayout`, `QGridLayout` for structure;
- sensible stretch factors;
- minimum sizes rather than rigid fixed heights;
- `QScrollArea` for page-level overflow where necessary;
- expanding/Preferred size policies for flexible content.

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
- do not nest boxes without a hierarchy reason;
- ensure all labels/values/actions fit at supported sizes.

For tables:

- prioritize scanning and density;
- preserve header clarity;
- preserve sort/selection behavior;
- preserve enough vertical working area;
- keep statuses text-readable;
- do not collapse tables to header-only height.

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

## 6. Check Content Reachability

This check is mandatory before visual approval.

At the real supported window size(s), verify:

- all major sections are reachable;
- page bottom is reachable;
- no second row of cards is clipped;
- no table is unintentionally collapsed;
- no action disappears below the viewport;
- vertical scrolling appears when needed;
- horizontal scrolling does not appear unnecessarily;
- resizing the window does not cause overlap.

If anything is unreachable, the phase is not complete.

---

## 7. Accessibility and RTL Check

Verify:

- Hebrew RTL is correct;
- mixed Hebrew/English/email text renders correctly;
- tab/focus order is logical;
- visible focus is retained;
- contrast is readable;
- disabled controls are understandable;
- status does not rely only on color;
- icons do not replace necessary text;
- long Hebrew text does not become inaccessible.

---

## 8. Behavioral Regression Check

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

## 9. Visual Comparison

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
- sidebar consistency;
- readability;
- reachability;
- RTL/right alignment.

If PySide6/QSS cannot reproduce an effect safely, choose the simplest
professional approximation and document it.

---

## 10. Real-App Visual Validation

Unit tests are not sufficient for layout work.

For every screen-specific phase:

1. run the real PySide6 application;
2. open the changed screen;
3. test the primary role shown in the reference;
4. test at least one other role if the screen is role-sensitive;
5. resize to the project's supported/default and minimum practical window sizes;
6. scroll to the bottom;
7. inspect text contrast;
8. inspect RTL/right alignment;
9. inspect clipping and overlap;
10. inspect disabled/focus states where relevant.

Do not approve the phase from an offscreen test run alone.

---

## 11. Validate

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

## 12. Report and Stop

For every bounded screen phase, report:

1. skill used;
2. files changed;
3. visual changes;
4. design references/assets used;
5. functional behavior explicitly preserved;
6. layout/reachability validation;
7. RTL/right-alignment validation;
8. contrast/readability validation;
9. tests/results;
10. visual validation result;
11. PySide6/QSS limitations or deviations.

If the prompt says to stop after one screen, stop.

Do not continue to the next screen automatically.

---

# Brand Rules

## Logo

Use only the approved logo artwork.

Reference:

```text
design_reference/logo.png
```

Runtime copies/crops may live under:

```text
desktop_client/app/assets/branding/
```

Do not redraw or regenerate it.

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
- page-specific color systems that do not match other screens;
- fixed-height content containers that clip children;
- layouts that only look correct at one exact window size;
- hidden page bottoms with no scroll access;
- text on images without reliable contrast;
- shrinking typography to solve layout problems;
- overlapping widgets;
- accidental empty action placeholders;
- inconsistent Hebrew alignment across one screen;
- centered/left-aligned Hebrew labels without a clear design reason.

---

# Final Quality Checklist

Before considering a screen complete, answer YES to all:

- Is existing functionality unchanged?
- Is all existing content still present?
- Is every essential control reachable?
- Is the page scrollable when content exceeds the viewport?
- Is there no unintended horizontal overflow?
- Is the approved reference clearly reflected?
- Is the real logo used correctly?
- Is the screen consistent with the shared brand system?
- Is RTL correct?
- Is Hebrew content right-aligned consistently across the screen?
- Are LTR exceptions limited only to data that genuinely benefits from LTR?
- Is keyboard/focus behavior preserved?
- Is text contrast readable?
- Is important text fully visible?
- Are tables/forms still practical?
- Are unsupported mockup features excluded?
- Are approved images used only where allowed?
- Did the real running app receive visual inspection?
- Did relevant role variants receive inspection?
- Did focused tests pass?
- Did compile validation pass?
- Did `git diff --check` pass?
- Was the PIV updated when required?

If any answer is NO, the screen phase is not complete.
