# Form System Runtime Overlay Readiness Policy V1

## Why the previous overlay stayed unwired

The runtime overlay can safely enrich existing SVG backbone projection rows from Intake V6 runtime confirmation state.

It was not wired because the current Awareness Panel still derives readiness/blocker display directly from backbone readiness/blocker data. Without an explicit rule, the UI could show:

- field row confirmed by runtime overlay
- readiness/blocker copy still present from backbone

That can be correct, but only with explicit policy. This slice adds that policy and keeps the UI unwired.

## Owner clarification

Do not bypass the Form System Backbone.

Required chain remains:

Product System / Component contracts
-> Form System Backbone
-> Field Projection
-> Runtime State Overlay
-> Readiness / Blocker Policy
-> Awareness Panel later

## Readiness / blocker audit

Audited files:

- `frontend/src/lib/intakeV6/formSystemBackboneFieldProjection.ts`
- `frontend/src/lib/intakeV6/formSystemBackboneRuntimeStateOverlay.ts`
- `frontend/src/lib/intakeV6/formSystemBackboneAwareness.ts`
- `frontend/src/components/workos/intake-v6/FormSystemBackboneAwarenessPanel.tsx`
- `frontend/src/lib/intakeV6/intakeV6ModularFormContractTypes.ts`
- `backend/services/form_system_contract_backbone_service.py`

Findings:

- backbone blockers are field-addressable enough for a policy helper
- each readiness blocker currently carries:
  - `field_key`
  - `owning_component`
  - `blocker_code`
  - `state`
  - `blocks`
  - `message`
- `_build_readiness(...)` in backend derives blockers from fields whose `blocker_code` exists and whose state is not `confirmed` / `ready`
- awareness currently renders two separate concepts:
  - field-state warnings from projection states
  - readiness/blocker list from backbone blockers

### What is field-addressed

Examples:

- `svg.layer_group_role`
- `svg.selected_layer_group`
- `return.depth_mm`
- `face.material`

These can support a policy decision about field-row relaxation.

### What is broad / global

Broad readiness markers include:

- `readiness.product_truth_blockers`
- blockers without a specific field key
- overall readiness status / root-level readiness interpretation

These must remain active by default when uncertain.

## Policy rules

Helper added:

- `frontend/src/lib/intakeV6/formSystemBackboneRuntimeReadinessPolicy.ts`

Policy rules:

1. Backbone remains source.
2. Overlay may only enrich existing backbone fields.
3. If a field changes from `missing` or `suggested` to `confirmed`, policy may relax that field-level warning.
4. Overlay must not remove broad/global backbone blockers.
5. Overlay may allow relaxation of a matching field-addressed blocker only when blocker `field_key` matches the same confirmed field.
6. Hydrated/fallback fields remain not confirmed.
7. PSU/material/pricing/read-model fields are ignored.
8. Policy is read-only and does not mutate inputs.
9. Policy does not create Product Truth.
10. Policy does not decide Quote/Order/Execution readiness.

Default:

When uncertain, keep blocker/warning active.

## Policy contract

Input:

- original projection
- runtime-overlaid projection
- backbone readiness

Output per field:

- original state
- overlay state
- whether state changed
- whether field warning can relax
- whether global blocker can relax
- reason
- trace metadata with matching and broad blocker codes

## Whether blockers are field-addressable enough

Yes, for policy-only purposes.

Current blocker semantics are addressable enough to distinguish:

- field-addressed blocker tied to the same `field_key`
- broad/global readiness marker that must remain visible

That is enough for a pure policy helper.

It is not enough yet to safely wire the UI without deciding how mixed field-confirmed plus global-blocked states should be rendered to operators.

## Wiring decision

Status: policy-only, not wired.

Reason:

- current awareness model still shows backbone blockers directly
- broad/global blocker behavior is preserved by the new policy, but the UI does not yet consume policy decisions
- wiring now would require visible-state rules and likely additional tests for mixed field-confirmed/global-blocked scenarios

Result token:

- `POLICY_ADDED_NOT_WIRED_YET`

## Files changed

- `frontend/src/lib/intakeV6/formSystemBackboneRuntimeReadinessPolicy.ts`
- `frontend/src/lib/intakeV6/formSystemBackboneRuntimeReadinessPolicy.test.ts`
- `docs/worklog/realignment/2026-07-08_form_system_runtime_overlay_readiness_policy_v1.md`

## Tests run

Focused Vitest:

`cd frontend`

`cmd /c npx.cmd --yes pnpm@8.10.0 exec vitest run src/lib/intakeV6/formSystemBackboneFieldProjection.test.ts src/lib/intakeV6/formSystemBackboneRuntimeStateOverlay.test.ts src/lib/intakeV6/formSystemBackboneAwareness.test.ts src/lib/intakeV6/formSystemBackboneRuntimeReadinessPolicy.test.ts`

Result:

- `4` files passed
- `26` tests passed

## Runtime smoke

### `/intake-v6/IR-MRBMAK7Z/operator`

- Review loads
- Form System Backbone panel appears
- backbone warnings still visible after expand
- composition still shows `Litere volumetrice + logo volumetric`
- PSU parent row still visible as `Sursa LED 12V / 2 buc / 67,20 EUR`

### `/intake`

- `Cerere Nouă` modal opens

### `/product-system`

- Letters/Logo status unchanged on visible surface

## Forbidden scope confirmation

This slice does not add or modify:

- UI wiring for the overlay/policy
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
- PSU/material read-model promotion

## Remaining risks

- current policy distinguishes field-addressed from broad/global blockers, but the panel does not yet consume that distinction
- `readiness.product_truth_blockers` is treated as broad/global by policy and kept active by default; future caller wiring must preserve that default
- if backend later introduces non-field-addressed blocker variants beyond current patterns, policy may need one more classifier rule

## Recommended next slice

Add a narrow awareness integration slice that consumes both runtime overlay and readiness policy together, with tests proving that field-row confirmation may relax local warning while broad/global backbone blockers remain visible and unchanged.