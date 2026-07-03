# BUILD_INTAKE_V4_CONSUMABLES_ADHESIVE_AND_WIRING_FOUNDATION

## Purpose

Add informative Intake V4 material-breakdown consumable lines for volumetric illuminated letters: return-to-face adhesive, per-letter MYYUP 2×0.75 wiring, and job-level MYYUP 2×1.5 supply wiring. Quote-estimate only — no stock, tasks, or orders.

## Owner inputs

| Item | Consumption | Price (RON, excl. TVA) | EUR display (5.1 RON/EUR, 1 decimal) |
|------|-------------|------------------------|----------------------------------------|
| Adeziv lipire cant | 2 ml / ml cant | 30 lei / flacon 50 ml → 0.6 lei/ml | 5.9 EUR/flacon, 0.1 EUR/ml |
| Cablu MYYUP 2×0.75 | 1 ml / literă/segment | 1.9 lei/ml | 0.4 EUR/ml |
| Cablu MYYUP 2×1.5 alimentare 220V | 5 ml / set reclamă | 3.9 lei/ml | 0.8 EUR/ml → ~3.8 EUR/set |

EUR conversion: `eur = ron / 5.1`, user-facing unit prices rounded to **one decimal**.

## Formulas

### Adhesive (`adhesive_return_to_face`)

- Basis: `letter_return_perimeter_ml` (letter cant only — excludes artwork return). Fallback: `return_material_perimeter_ml − artwork_return_perimeter_ml`.
- `quantity_ml = applicable_return_perimeter_ml × 2`
- `bottles_required = ceil(quantity_ml / 50)` — procurement hint on row warning
- `estimated_cost_eur = quantity_ml × (30/50/5.1)` prorated by ml (not full-bottle billing)

### Wire letters (`wire_letters_myyup_2x075`)

- `quantity_ml = real_letters_count × 1` (never artwork)
- `estimated_cost_eur = quantity_ml × (1.9/5.1)`

### Wire supply (`wire_supply_myyup_2x15`)

- `quantity_ml = 5` fixed per job/set
- `estimated_cost_eur = 5 × (3.9/5.1) ≈ 3.82 EUR`

## Applicability

| Consumable | When |
|------------|------|
| Adhesive | `TPL-VOLUMETRIC-LETTERS`, `real_letters_count > 0`, letter return perimeter > 0 |
| MYYUP 2×0.75 | Above + `illuminated = true` |
| MYYUP 2×1.5 | Above + `illuminated = true` |

No duplication of LED modules, PSU, cant aluminium registry rows, or Oracal face vinyl.

## Files changed

| Area | File |
|------|------|
| Consumables service | `backend/services/intake_v4_consumables_adhesive_wiring_service.py` |
| Breakdown integration | `backend/services/intake_v4_material_breakdown_service.py` |
| UI | `frontend/src/components/workos/intake-v4/IntakeV4MaterialBreakdownPanel.tsx` |
| Backend tests | `backend/tests/test_intake_v4_consumables_adhesive_and_wiring.py` |
| Frontend tests | `frontend/src/components/workos/intake-v4/IntakeV4MaterialBreakdownPanel.test.tsx` |

## Tests

```powershell
cd backend
$env:DATABASE_URL='sqlite+aiosqlite:///./test_consumables.db'
$env:JWT_SECRET_KEY='local-dev-secret'
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_consumables_adhesive_and_wiring.py -q
```

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v4/IntakeV4MaterialBreakdownPanel.test.tsx
```

**Results (2026-06-23):** 17 backend passed, 3 frontend passed.

## Runtime smoke (PBL IV4-4B172FD4)

Workspace `0f300dcf-0b77-4fc1-affd-6e2a20329804` — validated via `build_intake_v4_material_breakdown` on live payload:

- Adhesive: ~27.24 ml, 0.1 EUR/ml, 1 flacon hint
- MYYUP 2×0.75: 10 ml, 0.4 EUR/ml
- MYYUP 2×1.5: 5 ml, 0.8 EUR/ml, ~3.82 EUR

Restart `scripts/start-dev.ps1` backend to expose rows on `:8000` API after deploy.

## Boundary

- No quote policy changes
- No Pricing Registry / global CostEngine changes
- No quote/order/task/ExecutionPlan/stock side effects
- No push in this build

## Remaining / owner notes

- Adhesive billing: breakdown uses **prorated ml** cost; `bottles_required` is procurement hint only — owner may later choose full-bottle billing.
- MYYUP 2×1.5 price supplied by owner at 3.9 lei/ml (0.8 EUR/ml display).
