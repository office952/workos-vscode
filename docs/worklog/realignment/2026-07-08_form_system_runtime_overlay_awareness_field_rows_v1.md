# Form System Runtime Overlay Awareness Field Rows V1

## Why policy was added before this slice

The runtime overlay was intentionally left unwired until a read-only readiness policy existed.

Reason:

- runtime overlay can confirm existing SVG backbone projection rows from Intake V6 runtime state
- awareness panel still renders readiness/blocker rows from the backbone
- wiring overlay without policy could make field rows appear confirmed while broad/global backbone blockers were still active, without explaining the distinction

The previous slice added that policy first. This slice wires overlay plus policy only into awareness field rows.

## Owner rule preserved

Do not bypass the Form System Backbone.

Actual wiring path now is:

Product System / Component contracts
-> Form System Backbone
-> Field Projection
-> Runtime State Overlay
-> Runtime Readiness Policy
-> Awareness field rows only
-> Broad/global blockers remain backbone-derived

## Exact wiring path

### Backbone source

- `FormSystemBackboneAwarenessPanel` still starts from `contract.form_system_backbone`

### Projection

- `formSystemBackboneAwareness.ts` still starts by building projection from backbone fields only

### Overlay

- runtime overlay is applied only to the existing projection rows
- runtime input is narrow:
  - `layerRoleSetup`

### Policy

- readiness policy evaluates:
  - original projection
  - overlaid projection
  - `backbone.readiness`

### Awareness field rows

- field rows now summarize from overlaid projection plus policy decisions
- field-row blocker badge is relaxed only when policy allows field-level relaxation

### Broad/global blockers

- blocker list remains raw backbone-derived
- no broad/global blocker suppression is performed in this slice

## Proof backbone remains source

- projection still starts from backbone fields
- runtime state does not create rows
- blocker list still comes from `backbone.blockers ?? backbone.readiness?.blockers`
- Product Truth boundary message still comes from awareness logic, not runtime payload

## Proof runtime overlay only enriches existing fields

Runtime input is passed as:

- `runtimeState.layerRoleSetup`

It is derived from existing `state.layerRoleConfirmation` through the existing bridge:

- `layerRoleConfirmationToV6Setup(...)`

No full workspace state object is passed to awareness.
No full payload is passed to awareness.
No new field rows are created.

## What field-level warnings can relax

Current wired scope:

- `svg.layer_group_role`
- `svg.selected_layer_group`

If runtime state confirms them:

- field row may change to `operator_confirmed / confirmed`
- field-row blocker badge may relax
- suggested/missing field-row semantics may relax

## What broad/global blockers remain untouched

Unchanged in this slice:

- broad/global backbone blocker rows
- readiness summary source of truth
- Product Truth boundary message
- hydrated/fallback warnings such as `return.depth_mm`

This means the UI can now show:

- field row confirmed
- broad/global blocker rows still visible

That is intentional and policy-backed.

## Files changed

- `frontend/src/lib/intakeV6/formSystemBackboneAwareness.ts`
- `frontend/src/components/workos/intake-v6/FormSystemBackboneAwarenessPanel.tsx`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `frontend/src/lib/intakeV6/formSystemBackboneAwareness.test.ts`
- `docs/worklog/realignment/2026-07-08_form_system_runtime_overlay_awareness_field_rows_v1.md`

## Tests run

Focused Vitest:

`cd frontend`

`cmd /c npx.cmd --yes pnpm@8.10.0 exec vitest run src/lib/intakeV6/formSystemBackboneFieldProjection.test.ts src/lib/intakeV6/formSystemBackboneRuntimeStateOverlay.test.ts src/lib/intakeV6/formSystemBackboneRuntimeReadinessPolicy.test.ts src/lib/intakeV6/formSystemBackboneAwareness.test.ts`

Result:

- `4` files passed
- `31` tests passed

## Runtime smoke

### `/intake-v6/IR-MRBMAK7Z/operator`

- Review loads
- Form System Backbone panel appears
- expanded panel still shows Product Truth boundary message
- blocker rows still remain visible
- current route data shows SVG field rows as `operator_confirmed / confirmed`
- composition still shows `Litere volumetrice + logo volumetric`
- current route state still shows `Confirmat in Pasul 1`
- PSU parent row still visible as `Sursa LED 12V / 2 buc / 67,20 EUR`

### `/intake`

- `Cerere Nouă` modal opens

### `/product-system`

- Letters/Logo status unchanged on visible surface

## Forbidden scope confirmation

This slice does not add or modify:

- backend endpoint behavior
- backend writes
- Product Truth write
- ProductDefinition write
- Pricing
- Quote / Order
- Execution
- ProductAggregate
- TaskGraph
- ExecutionPlan
- DB / seed / migration
- Logo root behavior
- component root behavior
- component quote behavior
- PSU formula
- LED formula
- material calculation behavior
- promotion of PSU/material rows into Form System truth
- broad/global blocker deletion

## Remaining risks

- field rows can now appear confirmed while matching field-addressed blocker rows still appear in the raw backbone blocker list; this is acceptable in this slice because blocker rows intentionally remain backbone-derived
- the live panel truncates blocker display to the first few entries, so broad/global blocker preservation is best proven by tests rather than current visible route ordering alone
- if future caller logic needs resolved vs unresolved blocker presentation, the blocker list will need a policy-aware rendering layer rather than direct raw display

## Recommended next slice

Add a narrow blocker-row presentation layer that consumes the readiness policy and marks matching field-addressed blockers as resolved visually, while still preserving broad/global backbone blockers unchanged.