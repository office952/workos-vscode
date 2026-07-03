# AUDIT_AND_FIX_INTAKE_V4_SHEET_NESTING_QUANTITY_FLOOR_AND_BACKING_AREA_TRUTH

**Build:** `AUDIT_AND_FIX_INTAKE_V4_SHEET_NESTING_QUANTITY_FLOOR_AND_BACKING_AREA_TRUTH`  
**Branch:** `local/integration-pr4-plus-svg-path`  
**Boundary:** Material breakdown / sheet nesting quantity floor + cant label clarity only.

## Problem statement

On Ana Maria Grădiniță (workspace `2aeda68b-09e0-46af-ba1e-31b0a47482d7`), operator geometry showed **Suprafață față ≈ 1.264 m²** (sum of four pseudo volumetric groups), but Material Breakdown listed **Plexiglas 3 mm / față litere = 1.147 m²** and **Forex 10 mm / spate litere = 1.147 m²** with backing fallback warning.

That undercounted sheet material versus eligible face area and contradicted operator trust.

## Observed values (before)

| Metric | Value | Source |
|--------|-------|--------|
| Display / group face area sum | **1.2638 m²** | `letter_group_finishes.face_area_m2` |
| Sheet nesting placement footprint (face) | **1.1469 m²** | Σ `placedWidthMm × placedHeightMm` on face-classified placements |
| Material Plexiglas | **1.1469 m²** | `compute_sheet_nesting_material_split` → breakdown |
| Material Forex (backing fallback) | **1.1469 m²** | `resolve_backing_material_area_m2` from floored face quoteable |
| Cant label | `…+ interioare + artwork…` | Incorrect for raster/print logos |
| Cant quantity | 29.9098 m | Included artwork return despite raster exclusion policy |

Gap: **1.2638 − 1.1469 ≈ 0.117 m²** (~9.3% undercount).

## Root cause

1. **Sheet nesting split** correctly summed **placement bounding-box footprints** (`placedWidthMm × placedHeightMm`), not filled vector areas. For Ana Maria, 19 classified face placements + 6 unclassified yielded footprint **below** the sum of pseudo-layer filled areas shown in geometry UI.
2. **Material breakdown** used nesting footprint directly as Plexiglas quantity with **no floor** against eligible part area.
3. **Forex backing** copied the undercounted face quoteable area via existing fallback (`backing_area_m2` dedicated geometry absent).
4. **Cant row** used `artwork_return_perimeter_ml` in label/quantity even when artwork layers are `printed_artwork` / `needs_decision` raster (excluded from volumetric cant in operator UI).

No analyzer geometry formula bug — display face area from layers/groups was consistent; **quote material quantity** was the defect.

## Corrected rule

```
sheet_face_material_quantity_sqm = max(
    eligible_face_area_sum_sqm,
    sheet_nesting_face_footprint_sqm,
)
```

- `eligible_face_area_sum_sqm` = Σ `letter_group_finishes.face_area_m2` excluding artwork layers (and `printed_artwork` roles).
- Floor **not** applied for `prorated_fallback` mode (full-sheet proration — different semantics).
- Backing fallback uses **corrected** face quoteable quantity via existing `resolve_backing_material_area_m2`.
- Cant aggregated row: exclude raster/print `needs_decision` artwork from `+ artwork` label; use letter-only perimeter when artwork is not volumetric cant.

## Corrected values (after) — IV4-8D89E354 live recompute

| Metric | Before | After |
|--------|--------|-------|
| Plexiglas față | 1.1469 m² | **1.2638 m²** |
| Forex spate (fallback) | 1.1469 m² | **1.2638 m²** |
| Cant label | `+ artwork` | **`interioare eligibile`** (no artwork) |
| Cant quantity | 29.9098 m | **25.0188 m** (letters + interioare) |

PBL workspace IV4-46499080: Plexiglas **0.5834 → 0.6907 m²** (aligned to geometry face area; E2E dimension/part smoke unchanged).

## Audit trace (Ana Maria)

```
eligible_face_area_sum_sqm     = 1.2638  (4 pseudo groups)
sheet_nesting_placed_footprint = 1.1469  (19 face placements bbox sum)
material_breakdown_face_before = 1.1469
material_breakdown_face_after  = 1.2638  (floor applied)
```

## Files changed

| File | Change |
|------|--------|
| `backend/services/intake_v4_nesting_material_precision.py` | `compute_eligible_sheet_face_area_sum_sqm`, `apply_sheet_material_quantity_floor` |
| `backend/services/intake_v4_material_breakdown_service.py` | Wire floor; cant label/quantity for raster artwork; warning `sheet_nesting_quantity_floor_applied` |
| `backend/tests/test_intake_v4_nesting_material_precision.py` | Floor unit tests |
| `backend/tests/test_intake_v4_material_breakdown.py` | Ana Maria–like + PBL floor + cant label tests |

## Test evidence

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_nesting_material_precision.py tests/test_intake_v4_material_breakdown.py -q
# 38 passed

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v4/IntakeV4MaterialBreakdownPanel.test.tsx src/components/workos/intake-v4/IntakeV4OperatorUiPolish.test.tsx
# 8 passed
```

## Remaining limitations

- **Backing area** still uses face-area fallback when dedicated `backing_area_m2` geometry is absent (warning retained).
- **Logo print area ~1.5608 m²** per side: `estimated_area_m2` / covered-vector fallback when external raster asset missing — informational; not changed in this build.
- Material Breakdown remains **informative estimate**, not final quote price.
- Nesting placement footprint can still be **below** filled area; floor raises quote quantity but does not change nest2 layout.

## Logo print area note (Task I)

`logo stanga` / `logo dreapta` show **~1.5608 m²** when raster external asset is missing: this is **covered vector geometry / outbox fallback** from artwork complexity assessment (`covered_vector_area_estimate`), not duplicate physical area. Both logos can show the same value when they share symmetric clip/bbox fallback. **Intentional diagnostic fallback** — risky for final print quote if left undecided; operator should confirm execution method and real asset.

## Explicit non-changes

- No analyzer geometry formula / SVG parser / pseudo-layer classifier changes
- No Pricing Registry / Color Registry / CostEngine changes
- No API payload contract changes
- No quote/order/task creation, ExecutionPlan, tasks_json, or stock consumption
