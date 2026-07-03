# BUILD_INTAKE_V4_PERIMETER_LABELS_INTEGER_UNITS_AND_LED_ADHESIVE

## Purpose

Clarify Intake V4 operator UI for CNC vs cant/volum perimeters and pricing waste, format discrete LED/PSU quantities without decimals, and add supplemental LED module adhesive consumable.

## Problem (PBL `IV4-4B172FD4`)

| Metric | Value | Meaning |
|--------|-------|---------|
| Perimetru CNC față | 13.62 ml | Face cutting perimeter (letters + inner contours) |
| Cant / volum calculat | 15.47 ml | Return/profile material perimeter (letters + interioare + artwork) |
| Pentru preț (+20%) | 18.56 ml | `15.47 × 1.2` — quote waste buffer applied once in `_with_waste` |

**Conclusion:** Not double-counting waste on geometry — **labeling issue**. CNC and cant measure different contours; +20% applies only to priced quantity for material rows.

## Labels changed

- Geometry panel: **Perimetru CNC față**, **Cant / volum calculat**
- Confirm summary: **Cant / volum calculat**
- Material breakdown table: **Cantitate calculată** | **Pentru preț** with `(+20% pierdere)` when applicable
- Production handoff job: **Cant / volum calculat** (was Cant / profil lateral)
- Basis hint: cant/volum profil — baza geometrică; pentru preț +20% pierdere

## Integer quantity formatting

- Shared helper `intakeV4QuantityDisplay.ts` — `buc`, `pcs`, etc. without decimals
- Applied in material breakdown panel and production handoff preview
- ml, m², EUR precision unchanged

## LED module adhesive

| Field | Value |
|-------|-------|
| Key | `adhesive_led_modules` |
| Formula | `led_module_count × 0.2 ml` (production assumption) |
| Pricing | Same bottle as cant adhesive: 50 ml / 30 lei, `intake_v4_owner_consumable_adhesive` |
| PBL (47 modules) | 9.4 ml, 1 bottle hint, ~1.1 EUR estimated |

Separate from `adhesive_return_to_face` (cant ml × 2 ml).

## Files changed

- `backend/services/intake_v4_consumables_adhesive_wiring_service.py`
- `backend/services/intake_v4_material_breakdown_service.py`
- `backend/services/intake_v4_production_handoff_preview_service.py`
- `backend/schemas/intake_v4.py` (optional `priced_quantity` / `waste_percent` on handoff jobs)
- `frontend/src/lib/intakeV4/intakeV4QuantityDisplay.ts`
- `frontend/src/components/workos/intake-v4/IntakeV4MaterialBreakdownPanel.tsx`
- `frontend/src/components/workos/intake-v4/IntakeV4ProductionHandoffPreviewPanel.tsx`
- `frontend/src/components/workos/intake-v4/IntakeV4GeometryPanel.tsx`
- `frontend/src/components/workos/intake-v4/IntakeV4ConfirmOperationalSummary.tsx`
- Tests + this QA doc

## Commands + results

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_consumables_adhesive_and_wiring.py -q
# 22 passed

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV4/intakeV4QuantityDisplay.test.ts src/components/workos/intake-v4/IntakeV4MaterialBreakdownPanel.test.tsx
```

## Runtime smoke (PBL)

Stack :8000/:3000 — verify material breakdown API and UI labels.

## Boundary

No quote/order/tasks, ExecutionPlan, tasks_json, stock consumption, Pricing Registry global, CostEngine global, quote policy, V2/V3/Auth. No push.
