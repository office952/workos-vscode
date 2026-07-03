# Intake V4 Operator Redesign Schema

## Intent

Build a desktop-only operator cockpit for `TPL-VOLUMETRIC-LETTERS`.

The UI should feel like WorkOS, not a standalone mockup. The left navigation belongs to the site shell. The Intake V4 workflow lives inside the Operator page.

## Product Shape

1. **WorkOS Shell**
   - Persistent left sidebar with the real site navigation groups.
   - Topbar with global search, live DB status, template identity, autosave state, and user chip.

2. **Job Command Header**
   - One dense row with the file, dimensions, canonical vector perimeter, template area, and draft status.
   - No marketing copy, no tutorial text.

3. **Operator Cockpit**
   - A smart status band shows current step, active production zone, auto-confirmation, and calculation impact.
   - Step navigation remains inside the workspace: `Layere`, `Finisaje`, `Confirmare`.
   - The main decision surface changes by step.

4. **Decision Surface**
   - Step 1: vector/layer classification with preview, layer chips, and selected-layer inspector.
   - Step 2: finish decisions by production zone: `Litere`, `Embleme`, `Template + spate`, `LED`.
   - Step 3: draft handoff gates, production file attachments, and internal note.

5. **Right Inspector**
   - Live calculation ledger stays visible.
   - Ledger filters: all, materials, operations.
   - Clicking a ledger row updates a detail inspector and the cockpit impact card.
   - Oracal remains visibly split by use: `Oracal 651 / față litere`, `Oracal 8500 / față litere`, and `Oracal 651 / cant volum`.

## Protected Product Rules

- The Product System dictates fields and defaults.
- The canonical vector perimeter remains the source for cant/CNC.
- Face vinyl is separated by series: Oracal 651 and Oracal 8500.
- Cant vinyl remains separate from face vinyl.
- Letter lighting and emblem lighting are different calculations.
- Backing is mandatory for this template.
- UI must not show hole details as operator-facing content.
- UI must not show an invalid no-backing option.

## Interaction Rules

- Step buttons update visible stage and smart guidance.
- Scope buttons in Step 2 update the finish form without leaving the step.
- Ledger row clicks update selected cost detail.
- Form changes trigger a visible autosave pulse and return to confirmed state.
- Draft creation remains visually gated by operator confirmation.

## Implementation Target

Static HTML + CSS + JS only, but structured as it should later become React components:

- `AppShellSidebar`
- `OperatorTopbar`
- `JobCommandHeader`
- `OperatorCockpit`
- `StepNavigator`
- `LayerDecisionBoard`
- `FinishScopePanel`
- `HandoffGatePanel`
- `LiveCostInspector`
