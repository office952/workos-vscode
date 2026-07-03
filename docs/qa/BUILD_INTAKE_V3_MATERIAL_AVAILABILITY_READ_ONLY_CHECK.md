# BUILD — INTAKE_V3_MATERIAL_AVAILABILITY_READ_ONLY_CHECK

**Verdict:** PASS  
**Branch:** `local/integration-pr4-plus-svg-path`  
**HEAD before:** `222ef9d`  
**Date:** 2026-06-18

## Purpose

Add a **read-only** material availability preview for Intake V3: Material Breakdown required quantities → matched `inventory_materials` rows → estimated available/shortage/manual-check status. No reservation, stock movement, procurement, CostEngine, or execution side effects.

## Inventory / Material Registry audit

| Item | Finding |
|------|---------|
| Primary table | `inventory_materials` (`backend/models/inventory_materials.py`) |
| On-hand field | `stock_current` |
| Units | `unit` column (`m2`, `mp`, `ml`, `buc`, `placa`, …) |
| Sheet conversion | `format_verified` + `usable_width/height` + `sheet_unit` only |
| Stock movements | `stock_movements` — execution consumption only; not used here |
| Reservations | No dedicated reservation table |
| Read-only access pattern | `select(Inventory_materials).where(code==...)` (same as pricing lookup) |

## Matching strategy

1. **Code match** (`OWNER_CONFIRMED_FALLBACKS` / `resolve_registry_code_for_row`) → confidence **high**
2. **Single name match** → confidence **medium**
3. **Multiple candidates** → `ambiguous_match` / manual check
4. **No match** → `no_match` / manual check
5. **Indirect consumables** → policy rows (`cables`, `connectors`, `screws`, `silicone`) → `indirect_consumable`

Registry mapping (TPL-VOLUMETRIC-LETTERS):

| Breakdown key | Registry code |
|---------------|---------------|
| plexiglas_face | MAT-ACP-FATA-LITERE |
| forex_backing | MAT-SPATE-PVC-LITERE |
| face_vinyl | MAT-ORACAL-651 |
| aluminum_return | MAT-PROFIL-LATERAL-LITERE-{depth}MM |
| led_modules | MAT-LED-MODULE |
| led_power_supply | MAT-LED-PSU-12V |

## Unit handling

- Compare normalized compatible units: `m2`/`mp`, `ml`/`m`, `buc`/`pcs`
- `placa` → `m2` only when sheet format verified with usable dimensions
- Incompatible units → `manual_check` (no invented shortage)

## Availability statuses

`available` · `shortage` · `manual_check` · `not_tracked` · `indirect_consumable` · `no_match` · `ambiguous_match` · `unknown`

## Boundary (confirmed)

- `read_only = true`
- No Inventory mutation
- No StockMovement
- No reservation / Purchase Order
- No ExecutionPlan / ExecutionTask / WorkSession
- No CostEngine
- No Order/Quote status or pricing mutation

## Files changed

### Backend
- `backend/services/intake_v3_material_availability_service.py` (new)
- `backend/schemas/intake_v3.py`
- `backend/services/intake_v3_material_quantity_breakdown_service.py`
- `backend/services/intake_v3_order_production_readiness_service.py`
- `backend/services/intake_v3_production_task_dry_run_service.py`
- `backend/services/intake_v3_workspace_service.py`
- `backend/routers/intake_v3_workspaces.py`
- `backend/tests/test_intake_v3_material_availability.py` (new)

### Frontend
- `frontend/src/lib/intakeV3/materialAvailabilityContracts.ts` (new)
- `frontend/src/lib/intakeV3/api.ts`
- `frontend/src/lib/intakeV3/flowState.ts`
- `frontend/src/lib/intakeV3/flowState.test.ts`
- `frontend/src/lib/intakeV3/orderProductionReadinessContracts.ts`
- `frontend/src/lib/intakeV3/productionTaskDryRunContracts.ts`
- `frontend/src/components/workos/intake-v3/IntakeV3MaterialAvailabilityPanel.tsx` (new)
- `frontend/src/components/workos/intake-v3/IntakeV3MaterialAvailabilityPanel.test.tsx` (new)
- `frontend/src/components/workos/intake-v3/IntakeV3OrderProductionReadinessPanel.tsx`
- `frontend/src/components/workos/intake-v3/IntakeV3ProductionTaskDryRunPanel.tsx`
- `frontend/src/pages/IntakeV3App.tsx`

### Docs
- `docs/qa/BUILD_INTAKE_V3_MATERIAL_AVAILABILITY_READ_ONLY_CHECK.md` (this file)
- `docs/intake-v3/00_STATUS.md`
- `docs/intake-v3/04_READINESS_AND_BLOCKERS_MODEL.md`
- `docs/intake-v3/06_BUILD_ROADMAP.md`
- `docs/intake-v3/07_DECISIONS_LOG.md`
- `docs/intake-v3/templates/TPL-VOLUMETRIC-LETTERS/10_PRODUCTION_HANDOFF_ADAPTER.md`

## Endpoints

```
GET /api/v1/intake-v3/workspaces/{workspace_id}/material-availability
GET /api/v1/intake-v3/quotes/{quote_id}/material-availability
GET /api/v1/intake-v3/orders/{order_id}/material-availability
```

## Integrations

| Consumer | Fields / behavior |
|----------|-------------------|
| Material Breakdown | `registry_code`, `material_intent`, `stock_tracking_class` on quantity rows |
| Production Readiness | `material_availability_*` in `available_data`; warnings `material_shortage_detected`, `material_manual_check_required`, `material_availability_missing` |
| Task Dry-Run | `material_availability_*` summary; task inputs include `availability_status`; task warnings for shortages |

## Tests run

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_material_availability.py tests/test_intake_v3_material_quantity_breakdown.py tests/test_intake_v3_order_production_readiness.py tests/test_intake_v3_production_task_dry_run.py tests/test_intake_v3_layer_role_confirmation_propagation.py tests/test_intake_v3_geometry_path_perimeter_classification.py tests/test_intake_v3_geometry_metrics_snapshot.py -q
# 95 passed, 1 skipped

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v3/IntakeV3MaterialAvailabilityPanel.test.tsx src/pages/IntakeV3App.test.tsx src/lib/intakeV3/flowState.test.ts
# 175 passed
```

## Open questions

1. Should indirect consumables eventually map to `MaterialIntent.accessories` rows instead of static policy rows?
2. LED PSU watt-specific registry variants — match from finish/quote_input beyond `MAT-LED-PSU-12V` fallback?
3. IV3 audit log for availability checks (no pattern yet)?

## Recommended next build

`INTAKE_V3_INVENTORY_RESERVATION_GUARDED` or `INTAKE_V3_PROCUREMENT_PREVIEW` — only after explicit operator policy; keep separate from this read-only preview.

## Autoevaluare

| Criterion | Score |
|-----------|-------|
| Corectitudine | 8/10 |
| Boundary | 10/10 |
| Risc deviere | 2/10 |
