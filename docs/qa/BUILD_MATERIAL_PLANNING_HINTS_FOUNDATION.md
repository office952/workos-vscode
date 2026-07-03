# BUILD: Material Planning Hints Foundation

## Purpose

Add read-only **material planning hints** to execution read models so WorkOS can show what materials a volumetric order likely needs — without claiming exact stock levels for cheap consumables or blocking tasks automatically.

Prior audit: `docs/qa/AUDIT_MATERIAL_PLANNING_AND_PROCUREMENT_READINESS.md`

## Why no strict tracking for screws / silicone / cable

Publimedia production does not maintain piece-level inventory for small workshop consumables. False precision (e.g. “missing 17 screws”) is worse than operational guidance: **verify / checklist / preventive replenishment**.

## Material categories

| Category | Use |
|----------|-----|
| `project_critical` | Plexi, Forex, cant, LED modules, PSU, project bars |
| `standard_low_cost_stock` | Adhesive, screws, cable, connectors, packaging |
| `indirect_consumable` | QC checklist items |
| `internal_semifinished_output` | Reserved — handled via `depends_on_task_ids`, not inventory |

## Planning policies

`verify_before_start`, `keep_min_stock`, `checklist_only`, `buy_after_advance`, `operator_decision_required`

## Readiness impact (metadata only in this build)

`can_block_if_missing`, `suggest_replenishment`, `checklist_only`, `handled_by_dependency`, `no_task_block`

**This build does not activate `waiting_material` or change start guards.**

## Boundary: Pricing vs Inventory vs Planning

- **Pricing** — registry `unit_cost` for quotes; not physical availability.
- **Inventory** — `stock_current` + manual deduction from reality; no reservation.
- **Material planning** — derived hints from template rules + plan `process_id`; `quantity_estimate` is `null` when not safe.

## TPL-VOLUMETRIC-LETTERS map

See `backend/services/material_planning_service.py` — `VOLUMETRIC_PROCESS_MATERIAL_RULES` keyed by `process_id` (face_cnc_cut, side_forming, return_face_bonding, back_cut, led_install_letters, electrical_letters, mounting_template_cnc_cut, assembly_letters, qc_letters, packaging_letters).

## Operator Blueprint

- Order-level `material_planning_summary` (counts by category/impact).
- Per-task `material_planning_items` (name, category, policies, display_note — no price).

## Employee Mobile

- Per-task `material_hints` (max 2, employee-safe).
- Aggregated consumables label: “Consumabile montaj — verificare preventivă”.
- No price, supplier, margin, payroll.

## Files changed

### Backend

- `backend/services/material_planning_service.py` (new)
- `backend/services/order_production_blueprint_service.py`
- `backend/services/employee_mobile_order_blueprint_service.py`
- `backend/routers/employee_mobile_tasks.py` (Pydantic)
- `backend/tests/test_material_planning_hints.py` (new)

### Frontend

- `frontend/src/api/operatorProductionBlueprint.ts`
- `frontend/src/api/employeeMobileOrderBlueprint.ts`
- `frontend/src/components/workos/OperatorProductionBlueprintPanel.tsx`
- `frontend/src/components/workos/employee-mobile/EmployeeMobileOrderPipelineView.tsx`
- `frontend/src/pages/EmployeeMobileApp.test.tsx`

## Commands + results

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_material_planning_hints.py tests/test_task_readiness_dependencies.py tests/test_employee_mobile_tasks.py tests/test_employee_mobile_order_blueprint.py tests/test_operator_production_blueprint.py -q

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/employeeMobileAccess.test.ts src/lib/employeeMobileTaskSummary.test.ts src/lib/employeeMobileTaskViews.test.ts src/lib/employeeMobilePipelineEligibility.test.ts src/pages/EmployeeMobileApp.test.tsx
```

## Smoke (Sandu)

After backend reload on `:8000`:

- T-006: `waiting_predecessor` unchanged + `material_hints` with LED
- T-008: mounting hints visible
- No cost/preț/marjă in employee payload

## Deferred

- Manual procurement status (`awaiting_advance`, `to_order`, …)
- Real `waiting_material` readiness integration
- Stock reservation / inventory deduction at Start
- Supplier workflow / PO generation
- Automatic quantity calculation from geometry

## Boundary

- No CostEngine changes
- No task start guard changes
- No DB schema migration (derived read-only view)
