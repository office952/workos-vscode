# BUILD — INTAKE_V3_MATERIAL_QUANTITY_GEOMETRY_AND_MATERIAL_COST_BREAKDOWN_INFORMATIVE

## Purpose

Add a **read-only, materials-only informative** breakdown for Intake V3 / TPL-VOLUMETRIC-LETTERS covering geometry summary, material quantities, material unit prices, and material cost totals — without labor, operations, markup, profit, VAT, Inventory mutation, Execution, or CostEngine.

## Context

- Base commit: `26d4296` — order production readiness audit
- Scope: `breakdown_scope = materials_only_informative`
- IV3 chain through guarded convert + production readiness audit remains unchanged

## Data source audit

| Question | Answer |
|----------|--------|
| Confirmed production model location | `quote.notes.intake_v3_linkage_v1.snapshot.sections.confirmed_production_model_snapshot` (or live workspace payload) |
| Letter/contour/hole fields | `letter_count`, `cut_contour_count`, `inner_hole_count`, `cut_contour_model.outer_contour_count` |
| Perimeters in IV3 snapshot today | **Not stored by default** — optional `geometry_metrics_snapshot` section or volumetric-style keys when injected |
| Areas in IV3 snapshot today | **Not stored by default** — bounding box `pricing_input_candidate_snapshot.dimensions.area_m2` used as **estimated** fallback |
| Return / LED quantities | From `geometry_metrics_snapshot` when present; PSU count may fall back to `derive_material_intent` power supplies |
| Material intent | `derive_material_intent()` — conceptual only, `requires_geometry` for sheets/rolls |
| Material prices | Read-only lookup on `inventory_materials` by registry code; owner-confirmed fallback documented in service when registry row missing |

## Geometry extraction strategy

1. Counts from `ConfirmedProductionModel` (never infer holes as letters).
2. Perimeters/areas from merged sources: `geometry_metrics_snapshot`, nested `geometry_metrics`, pricing adapter dimensions, optional quote_input keys (`letter_perimeter_m`, `letter_face_area_m2`, etc.).
3. Missing perimeters → `missing_geometry_perimeters` warning; quantities marked `missing`/`partial`.
4. Bounding-box area only → `estimated` + explicit warnings.

## Material quantity strategy

- Sheet rows: plexiglas face, forex backing, face vinyl (only if finish requires vinyl).
- Linear row: aluminum return from return perimeter + 20% waste.
- Component rows: LED modules, LED PSU.
- Optional/future: ACM, șablon, ambalare — not included unless snapshot rules added later.

## Material price source strategy

1. Prefer `inventory_materials.unit_cost` when `status=active` (pricing registry path).
2. Fallback `owner_confirmed_fallback` for documented TPL-VOLUMETRIC owner values (plexi/forex/vinyl/LED/profile tiers).
3. Aluminum return tier from `return_depth_mm` → `PROFILE_DEPTH_MM_TO_VARIANT_CODE`.
4. Missing price → cost row `missing`, warning `missing_unit_price` — response does not crash.
5. Mixed currencies → totals grouped per currency; no FX conversion.

## Explicit exclusions

- No labor, operations, markup, profit, VAT in breakdown
- No CostEngine calls
- No ExecutionPlan / ExecutionTask creation
- No Inventory / StockMovement mutation
- Perimeters displayed as technical geometry, not operation costs

## Files changed

### Backend

- `backend/services/intake_v3_material_quantity_breakdown_service.py` (new)
- `backend/schemas/intake_v3.py` — breakdown response models
- `backend/routers/intake_v3_workspaces.py` — GET material-breakdown endpoints
- `backend/services/intake_v3_workspace_service.py` — workspace wrappers
- `backend/tests/test_intake_v3_material_quantity_breakdown.py` (new)

### Frontend

- `frontend/src/lib/intakeV3/materialBreakdownContracts.ts` (new)
- `frontend/src/lib/intakeV3/api.ts`
- `frontend/src/lib/intakeV3/contracts.ts`
- `frontend/src/components/workos/intake-v3/IntakeV3MaterialBreakdownPanel.tsx` (new)
- `frontend/src/pages/IntakeV3App.tsx`
- `frontend/src/lib/intakeV3/flowState.ts`
- `frontend/src/components/workos/intake-v3/IntakeV3OrderProductionReadinessPanel.tsx`
- `frontend/src/components/workos/intake-v3/IntakeV3AcceptConvertReadinessPanel.tsx`
- `frontend/src/lib/intakeV3QuoteCommercialGuard.ts`
- Tests: `IntakeV3App.test.tsx`, `flowState.test.ts`, `quoteCommercialGuidance.test.ts`

### Docs

- This file + intake-v3 status/roadmap/decisions updates

## Endpoints

```http
GET /api/v1/intake-v3/orders/{order_id}/material-breakdown
GET /api/v1/intake-v3/quotes/{quote_id}/material-breakdown
GET /api/v1/intake-v3/workspaces/{workspace_id}/material-breakdown
```

## Commands + results

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_material_quantity_breakdown.py tests/test_intake_v3_order_production_readiness.py tests/test_intake_v3_guarded_convert_to_order.py tests/test_intake_v3_guarded_accept_flow.py -q
# 54 passed

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/IntakeV3App.test.tsx src/lib/intakeV3/flowState.test.ts src/lib/intakeV3QuoteCommercialGuard.test.ts src/lib/quoteCommercialGuidance.test.ts
# 174 passed
```

## Boundary

- Does not create ExecutionPlan/ExecutionTask
- Does not mutate Inventory
- Does not call CostEngine
- Does not change non-IV3 orders/quotes behavior (returns `is_intake_v3=false` safely)
- Does not invent SVG path geometry — requires snapshot metrics or marks missing/estimated

## Next build options

1. Production task generation dry-run contract
2. Material registry refinement (dedicated IV3 material price resolver)
3. Inventory availability read-only check

## Open questions

- When will IV3 persist path-derived `geometry_metrics_snapshot` from SVG analysis (letter_perimeter_m, letter_face_area_m2)?
- Should LED module count be derived from face area policy like volumetric CostEngine (future, not in this build)?
