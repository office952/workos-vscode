# Form System Backbone Projection Awareness Wiring V1

## Owner clarification

This slice follows the clarified architecture:

Product System / Component contracts
-> Form System Backbone
-> read-only field projection
-> Awareness Panel / Review UI

The projection is not a parallel truth source and does not bypass the backbone.

## Before / after wiring

Before:

- `FormSystemBackboneAwarenessPanel` received the full `form_system_backbone` object.
- `formSystemBackboneAwareness.ts` directly re-summarized raw backbone fields.
- It locally recomputed `suggested` and `fallback/hydrated` grouping from raw `source_type` and `state` values.

After:

- `FormSystemBackboneAwarenessPanel` still receives the full `form_system_backbone` object.
- `formSystemBackboneAwareness.ts` now derives its field summaries and state warning categories through `buildFormSystemBackboneFieldProjection(backbone, { fieldKeys })`.
- The panel still renders the same backbone-oriented view model, but the interpretation layer now flows through the projection adapter.

## Why projection is only a view-model over backbone

- Input remains `contract.form_system_backbone` only.
- No workspace runtime payload is read for this projection path.
- No API calls are added.
- No write behavior exists.
- No Product Truth, ProductDefinition, pricing, quote, order, or execution behavior is involved.

This keeps the backbone as the coherent system-connection layer and uses projection only to normalize display semantics.

## Duplicate awareness logic reduced

Reduced / removed from direct raw-field interpretation:

- field summary mapping for displayed fields
- suggested vs unconfirmed grouping
- fallback / hydrated grouping

Still derived directly from backbone outside the projection:

- root metadata
- component coverage summaries
- readiness / blocker list
- downstream write intent flags

## Fields included

The awareness wiring consumes backbone fields through projection and preserves current panel meaning for existing backbone-backed fields, including the strict v1 slice fields:

1. `svg.layer_group_role`
2. `svg.selected_layer_group`
3. `return.depth_mm`

## Fields intentionally excluded

The awareness wiring explicitly excludes these from projection-backed awareness fields:

- `lighting.psu_configuration`
- `materials.led_psu`
- `material.led_psu`

These are not promoted to Form System truth.

## Files changed

- `frontend/src/lib/intakeV6/formSystemBackboneAwareness.ts`
- `frontend/src/lib/intakeV6/formSystemBackboneAwareness.test.ts`
- `docs/worklog/realignment/2026-07-08_form_system_backbone_projection_awareness_wiring_v1.md`

## Tests run

Focused Vitest:

`cd frontend`

`cmd /c npx.cmd --yes pnpm@8.10.0 exec vitest run src/lib/intakeV6/formSystemBackboneFieldProjection.test.ts src/lib/intakeV6/formSystemBackboneAwareness.test.ts`

Result:

- `2` files passed
- `12` tests passed

## Runtime smoke

### `/intake-v6/IR-MRBMAK7Z/operator`

- Review loads
- `Form System Backbone` panel still appears
- expanded panel still shows:
  - `Suggested values are not confirmed.`
  - `Fallback/hydrated values are not confirmed.`
  - `Operator confirmation remains the Product Truth boundary.`
- composition still shows `Litere volumetrice + logo volumetric`
- `Confirmat in Pasul 1` remains present in the current review state
- PSU parent row still visible as `Sursa LED 12V / 2 buc / 67,20 EUR`

### `/intake`

- `Cerere Nouă` modal still opens

### `/product-system`

- Letters / Logo status distinction remains unchanged on the visible surface

## Forbidden scope confirmation

This slice does not add or modify:

- backend endpoint behavior
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
- PSU / LED formulas
- material calculation logic

## Remaining risks

- The awareness model still depends on raw backbone blocker/root/component sections outside the field projection, which is acceptable for this slice but leaves some interpretation split across two layers.
- `svg.selected_layer_group` remains `missing` until the backbone itself exposes a stronger confirmed state.
- The projection adapter default remains the strict 3-field slice; awareness wiring intentionally overrides field selection from actual backbone keys to preserve panel semantics.

## Recommended next slice

Consider a small follow-up that centralizes more read-only awareness formatting around projection-backed helpers without moving any truth authority out of the backbone.