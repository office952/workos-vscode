# Form System Backbone Field Projection V1

## Why this slice exists

The previous task stopped at audit-only because the first decision had to be whether a new backend endpoint or write path was needed. The audit confirmed that a read-only endpoint already exists at `GET /api/v1/intake-v6/form-contract/{templateCode}` and already returns a `form_system_backbone` block.

This slice therefore stays narrow: add a frontend projection adapter over the existing backbone contract instead of creating new backend behavior.

## Why PSU and material rows are excluded

`psu_configuration` and `material.led_psu` exist elsewhere in runtime payload and downstream read models, but they are not the same thing as Form System input truth.

This v1 explicitly excludes:

- `lighting.psu_configuration`
- `materials.led_psu`
- `material.led_psu`

The goal is to avoid false Product Truth claims around calculated material rows or downstream pricing/read-model data.

## Chosen strict field set

The v1 projection includes only fields that already exist in the backend backbone contract:

1. `svg.layer_group_role`
2. `svg.selected_layer_group`
3. `return.depth_mm`

These cover:

- SVG suggestion state
- operator-selected / not-yet-confirmed selection state
- hydrated runtime state

All three remain read-only.

## Adapter output shape

Added `frontend/src/lib/intakeV6/formSystemBackboneFieldProjection.ts`.

The adapter exposes a normalized `FormSystemBackboneFieldProjection` list with:

- field identity and label
- owner kind / owner id
- normalized source kind
- normalized state
- product truth path candidate
- confirmed-truth flag
- derived flag
- blocking flag
- warnings / blockers
- raw trace payload for debugging

The adapter:

- accepts the existing modular contract response or the backbone object directly
- does not fetch
- does not mutate input
- does not write anything
- does not include PSU or material rows by default

## Files changed

- `frontend/src/lib/intakeV6/formSystemBackboneFieldProjection.ts`
- `frontend/src/lib/intakeV6/formSystemBackboneFieldProjection.test.ts`
- `docs/worklog/realignment/2026-07-08_form_system_backbone_field_projection_v1.md`

## Tests run

Planned focused validation:

`cd frontend`

`cmd /c npx.cmd --yes pnpm@8.10.0 exec vitest run src/lib/intakeV6/formSystemBackboneFieldProjection.test.ts`

## Runtime smoke

Runtime smoke for this slice is regression-only because no UI contract was changed.

Targets:

- `/intake-v6/IR-MRBMAK7Z/operator`
- `/intake`
- `/product-system`

Checks:

- review shell still loads
- existing backbone awareness panel still renders if present
- composition remains litere + logo volumetric
- PSU regression proof remains unchanged
- intake modal still opens
- product-system letters/logo statuses stay unchanged

## Forbidden scope confirmation

This slice does not add or modify:

- backend endpoint surface
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
- PSU formula or LED formula
- material calculation logic

## Remaining risks

- `svg.selected_layer_group` is still represented as `missing` in the current backbone until operator confirmation data is reflected as confirmed truth in that contract.
- The adapter is strict by design and does not attempt to merge workspace payload truth with backbone truth.
- A later slice may need a separate projection for runtime-confirmed values if owner-approved.

## Recommended next slice

Next recommended slice: add an owner-approved read-only projection for explicit confirmed runtime truth once the backbone or adjacent contract distinguishes confirmed operator-selected SVG group state from missing state in a stable way.