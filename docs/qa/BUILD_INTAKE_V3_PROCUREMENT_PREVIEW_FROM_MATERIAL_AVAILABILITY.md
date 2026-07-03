# BUILD — INTAKE_V3_PROCUREMENT_PREVIEW_FROM_MATERIAL_AVAILABILITY

**Verdict:** PASS  
**Branch:** `local/integration-pr4-plus-svg-path`  
**HEAD before:** `707030a`  
**Date:** 2026-06-18

## Purpose

Add a **read-only procurement preview** that translates Material Availability rows into operational recommendations (purchase, owner decision, manual check, preventive restock). No Purchase Order, Supplier Order, inventory mutation, StockMovement, CostEngine, or execution side effects.

## Audit — supplier / source / procurement metadata

| Item | Finding |
|------|---------|
| Primary registry | `inventory_materials` |
| On-hand | `stock_current`, optional `stock_min` / `stock_max` |
| Source hints | `source_name`, `source_url`, `source_notes`, `source_review_status` |
| Cost hints | `unit_cost`, `currency` — informative only, not commercial pricing |
| Purchase Order model | **Not found** — boundary flags only |
| Supplier Order model | **Not found** |
| StockMovement | Execution consumption only — not used |
| Reservations | No dedicated table |
| Reorder automation | **Not implemented** — preview may suggest preventive restock only |

## Material Availability as source

Procurement Preview **does not** recalculate geometry, breakdown, or availability. It consumes `build_material_availability_response()` rows and maps:

`availability_status` → `procurement_status` → `recommended_action` / `decision_owner` / warnings.

## Procurement statuses

`purchase_recommended` · `manual_check` · `owner_decision_required` · `advance_recommended` · `preventive_restock` · `indirect_consumable` · `no_action` · `not_applicable` · `unknown`

| Availability | Procurement (typical) |
|--------------|----------------------|
| `available` | `no_action` |
| `shortage` + major material | `owner_decision_required` + `advance_recommended` |
| `shortage` + normal tracked material | `purchase_recommended` |
| `manual_check` / `no_match` / `ambiguous_match` / `not_tracked` | `manual_check` |
| `indirect_consumable` | `indirect_consumable` / preventive restock hint |

## Owner decision policy

Major material intents (shortage → owner + advance):

- `plexiglas_face`, `forex_backing`, `aluminum_return`, `face_vinyl`, `led_power_supply`, `acm_panel`

`decision_required=true`, `decision_owner=owner`, `recommended_action=purchase_after_owner_approval`.

## Advance recommended policy

Set when major material has shortage and material is flagged expensive (`is_expensive_material`) or in major-intent list. Informative only — no commercial recalculation.

## Indirect consumables policy

`mounting_cables`, `electrical_connectors`, `mounting_screws`, `silicone_sealant` → `indirect_consumable` / `preventive_restock_or_manual_check`. Not treated as strict stock shortage.

## Source hints

Read-only from matched `inventory_materials` row when available. Warnings: `supplier_source_missing`, `supplier_source_needs_review` (when `source_review_status` is stale/needs_review). No registry mutation.

## Warnings

Preview + downstream: `material_availability_missing`, `purchase_recommended`, `owner_decision_required`, `advance_recommended`, `manual_stock_check_required`, `procurement_owner_decision_required`, `procurement_manual_check_required`, `procurement_purchase_recommended`, `procurement_preview_read_only`, etc.

## Integrations

| Consumer | Behavior |
|----------|----------|
| Production Readiness | `procurement_preview_*` counts in `available_data`; string warnings `procurement_owner_decision_required`, … |
| Task Dry-Run | Summary fields; candidate task inputs include `procurement_status`; task-level procurement warnings |
| Flow stepper | `procurement_preview` between Material Availability and Task Dry-Run |

## Endpoints

```
GET /api/v1/intake-v3/workspaces/{workspace_id}/procurement-preview
GET /api/v1/intake-v3/quotes/{quote_id}/procurement-preview
GET /api/v1/intake-v3/orders/{order_id}/procurement-preview
```

## Boundary (confirmed)

- `read_only = true`, `creates_purchase_order = false`, `creates_supplier_order = false`
- No Inventory mutation, StockMovement, reservation
- No ExecutionPlan / ExecutionTask / WorkSession
- No CostEngine, Order/Quote status or pricing mutation
- UI: no Buy / Order / Reserve / Generate Tasks / Start Production buttons

## Files changed

### Backend
- `backend/services/intake_v3_procurement_preview_service.py` (new)
- `backend/schemas/intake_v3.py`
- `backend/services/intake_v3_order_production_readiness_service.py`
- `backend/services/intake_v3_production_task_dry_run_service.py`
- `backend/services/intake_v3_workspace_service.py`
- `backend/routers/intake_v3_workspaces.py`
- `backend/tests/test_intake_v3_procurement_preview.py` (new)

### Frontend
- `frontend/src/lib/intakeV3/procurementPreviewContracts.ts` (new)
- `frontend/src/lib/intakeV3/api.ts`
- `frontend/src/lib/intakeV3/flowState.ts` + `flowState.test.ts`
- `frontend/src/lib/intakeV3/orderProductionReadinessContracts.ts`
- `frontend/src/lib/intakeV3/productionTaskDryRunContracts.ts`
- `frontend/src/components/workos/intake-v3/IntakeV3ProcurementPreviewPanel.tsx` (new)
- `frontend/src/components/workos/intake-v3/IntakeV3ProcurementPreviewPanel.test.tsx` (new)
- `frontend/src/components/workos/intake-v3/IntakeV3OrderProductionReadinessPanel.tsx`
- `frontend/src/components/workos/intake-v3/IntakeV3ProductionTaskDryRunPanel.tsx`
- `frontend/src/pages/IntakeV3App.tsx` + `IntakeV3App.test.tsx`

### Docs
- This file + intake-v3 status/roadmap/readiness/decisions/handoff adapter updates

## Tests run

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_procurement_preview.py tests/test_intake_v3_material_availability.py tests/test_intake_v3_material_quantity_breakdown.py tests/test_intake_v3_order_production_readiness.py tests/test_intake_v3_production_task_dry_run.py -q
# 70 passed

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v3/IntakeV3ProcurementPreviewPanel.test.tsx src/components/workos/intake-v3/IntakeV3MaterialAvailabilityPanel.test.tsx src/pages/IntakeV3App.test.tsx src/lib/intakeV3/flowState.test.ts
# 179 passed
```

## Open questions

- Formal Purchase Order / Supplier Order models when procurement moves from preview to execution
- Owner-approved purchase workflow UI (separate build; no PO in this preview)
- Threshold-based “expensive material” from registry `unit_cost` vs fixed major-intent list
- Preventive restock suggestions vs actual reorder points (`stock_min`) when policy is defined

## Recommended next build

`INTAKE_V3_PRODUCTION_HANDOFF_EXECUTION_GUARD` or dedicated **Purchase Order preview contract** (still read-only) once PO schema exists — not auto-procurement.
