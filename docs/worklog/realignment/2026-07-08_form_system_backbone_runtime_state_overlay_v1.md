# Form System Backbone Runtime State Overlay V1

## Owner clarification

This slice preserves the required authority chain:

Product System / Component contracts
-> Form System Backbone
-> Field Projection
-> Runtime State Overlay, read-only
-> Awareness Panel / Review UI

The overlay does not bypass the Form System Backbone. It starts from existing backbone projection rows and only enriches fields already present there.

## Why the overlay exists

The strict backbone projection correctly kept `svg.selected_layer_group` as `missing` because the template-level backbone does not itself carry runtime operator confirmation state.

The Intake V6 runtime workspace already persists SVG layer-role confirmation in `layer_role_setup`, so a controlled read-only overlay is the right place to enrich existing SVG backbone projection rows without introducing a parallel truth source.

## Runtime state audited

Audited frontend runtime state confirmed:

- persisted payload path: `workspace.payload.layer_role_setup`
- hydrated frontend runtime path: `state.layerRoleConfirmation`
- persisted entry fields:
  - `auto_role`
  - `confirmed_role`
  - `confirmation_state`
- confirmation status:
  - `missing`
  - `partial`
  - `complete`

Relevant files inspected:

- `frontend/src/lib/intakeV6/formSystemBackboneFieldProjection.ts`
- `frontend/src/lib/intakeV6/formSystemBackboneAwareness.ts`
- `frontend/src/lib/intakeV6/useModularFormContract.ts`
- `frontend/src/lib/intakeV6/useModularFormAwareness.ts`
- `frontend/src/lib/intakeV6/intakeV4Api.ts`
- `frontend/src/lib/intakeV6/intakeV6Api.ts`
- `frontend/src/lib/intakeV6/intakeV4LayerRoleDisplay.ts`
- `frontend/src/lib/intakeV6/intakeV4LayerRoleOptions.ts`
- `frontend/src/components/workos/intake-v6/IntakeV6LayersOperatorPanel.tsx`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `frontend/src/components/workos/intake-v6/FormSystemBackboneAwarenessPanel.tsx`
- `frontend/src/lib/intakeV6/intakeV6LayerRoleBridge.ts`
- `frontend/src/lib/intakeV6/intakeV6PayloadHydrate.ts`
- `frontend/src/lib/svgAnalyzer/analyzer/layerRoleTypes.ts`

## Chosen fields

V1 overlay scope is limited to existing SVG backbone projection rows:

1. `svg.layer_group_role`
2. `svg.selected_layer_group`

## Overlay contract

Helper added:

- `frontend/src/lib/intakeV6/formSystemBackboneRuntimeStateOverlay.ts`

Input:

- existing `FormSystemBackboneFieldProjection[]`
- narrow runtime input `{ layerRoleSetup?: IntakeV6LayerRoleSetup | null }`

Output:

- new `FormSystemBackboneFieldProjection[]`

Mutation policy:

- input projection array is not mutated
- projection entries are cloned before any overlay is applied
- no new field rows are created

Inclusion rules:

- only existing `svg.layer_group_role`
- only existing `svg.selected_layer_group`

Overlay behavior:

- if `layer_role_setup.confirmation_status === complete`
- and confirmed layers exist with `confirmed_role`
- then existing SVG projection rows may become:
  - `state = confirmed`
  - `sourceKind = operator_manual`
  - `isConfirmedTruth = true`
- trace preserves original state/source and adds runtime confirmation details

Exclusion rules:

- no new fields added
- no `return.depth_mm` runtime promotion in this slice
- no PSU/material rows
- no pricing/read-model rows

## Why PSU/material rows remain excluded

This slice is about SVG runtime confirmation only. PSU/material rows are not Form System truth for this task and are explicitly excluded from overlay behavior:

- `lighting.psu_configuration`
- `material.led_psu`
- `materials.led_psu`

## Wiring decision

Status: utility-only, not wired into awareness yet.

Reason:

- the awareness panel still renders blocker/readiness sections directly from the backbone
- applying overlay only to projection field rows would produce mixed semantics unless a parallel read-only blocker/readiness overlay policy is defined
- the runtime layer-role source is clear enough for a safe utility, but not enough to alter current panel semantics without owner-reviewed display rules

Result token:

- `OVERLAY_ADDED_NOT_WIRED_YET`

## Files changed

- `frontend/src/lib/intakeV6/formSystemBackboneRuntimeStateOverlay.ts`
- `frontend/src/lib/intakeV6/formSystemBackboneRuntimeStateOverlay.test.ts`
- `docs/worklog/realignment/2026-07-08_form_system_backbone_runtime_state_overlay_v1.md`

## Tests run

Focused Vitest:

`cd frontend`

`cmd /c npx.cmd --yes pnpm@8.10.0 exec vitest run src/lib/intakeV6/formSystemBackboneFieldProjection.test.ts src/lib/intakeV6/formSystemBackboneRuntimeStateOverlay.test.ts src/lib/intakeV6/formSystemBackboneAwareness.test.ts`

Result:

- `3` files passed
- `19` tests passed

## Runtime smoke

### `/intake-v6/IR-MRBMAK7Z/operator`

- Straturi / Review / Confirmare shell still loads
- Form System Backbone panel still appears
- Review still loads
- composition still shows `Litere volumetrice + logo volumetric`
- current route state still shows `Confirmat in Pasul 1`
- PSU parent row still visible as `Sursa LED 12V / 2 buc / 67,20 EUR`

### `/intake`

- `Cerere Nouă` modal still opens

### `/product-system`

- Letters/Logo status remains unchanged on visible surface

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

## Remaining risks

- `svg.selected_layer_group` is overlaid from confirmed runtime layer refs, not from a distinct dedicated runtime `selected_group` object; this is acceptable for utility-only enrichment but still an interpretation choice.
- Awareness/readiness rows remain split between projection-derived field semantics and raw backbone blockers until a dedicated read-only overlay policy is defined for blocker semantics.
- If future templates introduce explicit group-level runtime selection separate from per-layer confirmation, this helper will need a narrower mapping rule.

## Recommended next slice

Add an owner-reviewed read-only awareness integration slice only if the repo defines how runtime-confirmed SVG field rows should interact with backbone blocker/readiness copy, so the panel does not present mixed semantics.