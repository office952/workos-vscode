# BUILD — Intake V4 Phase B1 Cant Breakdown Alignment

**Date:** 2026-06-24  
**Branch:** `local/integration-pr4-plus-svg-path`  
**Base HEAD:** `5b9c3b2` feat(intake-v4): persist sheet footprint source for material preview  
**Scope:** Backend-only — align `return_material` base quantity with operator vector cant perimeter.

---

## Purpose

Material breakdown `return_material` row previously used `quote_geometry.return_material_perimeter_ml` / LED outer perimeter (~20.97 m on Ana Maria) instead of the operator vector cant sum (~31.64 m) already shown in Review UI and Materiale folosite. Phase B1 aligns breakdown base quantity to the same policy as `resolveIntakeV4OperatorCantPerimeterDisplay` / `sumActiveLetterGroupCantPerimeterM`.

---

## Audit chain (before fix)

```text
svg_analyzer (nest2 layers.perimeterMl)
  → intake_v4_quote_geometry_service.build_quote_geometry_from_analysis
      (outer classification → return_material_perimeter_ml ≈ LED outer)
  → intake_v4_volumetric_return_metrics_service.enrich_quote_geometry_with_volumetric_return
      (letter_return = outer + inner holes; led_perimeter_ml = outer only)
  → path_geometry_summary / quote_geometry persisted on workspace
  → intake_v4_material_breakdown_service.build_intake_v4_material_breakdown
      _float_metric(..., "return_material_perimeter_ml") → _append_return_material_rows
      _with_waste → base_quantity / priced_quantity (+20%)
```

**Field producing cant base qty (before):** `return_material_perimeter_ml` from geometry sources (often `outer_letter_perimeter_ml` / LED scope ~20.97 m).

**+20% waste:** `_with_waste()` in `_quote_cost_row` / `_cost_row` with `WASTE_PERCENT = 20` → `priced_quantity = base × 1.20`, `quantity_basis = perimeter_with_waste`.

**Frontend expectation (unchanged):** `intakeV4EdgeCantDisplay.ts` reads `returnRow.base_quantity` for calculated cant; Materiale folosite uses operator perimeter from letter groups.

---

## Root cause

Breakdown trusted persisted geometry `return_material_perimeter_ml` and classification outer perimeter instead of summing **cant-active letter group `perimeter_m`** (+ eligible emblem vector when cant active). LED outer (~20.97 m) leaked into cant material row on multi-group jobs like Ana Maria.

---

## Fix

Added `_compute_operator_cant_perimeter_m()` and `_artwork_row_counts_for_operator_cant()` in `intake_v4_material_breakdown_service.py`:

```text
operator_cant =
  Σ letter_group.perimeter_m (or layer vector) where cant active
  + Σ artwork layer vector where cant active AND not raster print-only
```

When letter groups or artwork finishes exist:

- Use operator cant for `_append_return_material_rows` inputs.
- If cant active but vector missing → warning `missing_operator_cant_perimeter`, **no** bbox / LED / quote_geometry fallback.
- LED module count still uses `letter_perimeter_ml` / `led_perimeter_ml` (unchanged).

---

## Files changed

| File | Change |
|------|--------|
| `backend/services/intake_v4_material_breakdown_service.py` | Operator cant helpers + breakdown injection |
| `backend/tests/test_intake_v4_cant_breakdown_alignment.py` | Phase B1 contract tests (new) |
| `backend/tests/test_intake_v4_material_breakdown.py` | Ana Maria fixture: `perimeter_m` on letter groups |

---

## Expected Ana Maria (after fix)

| Metric | Value |
|--------|-------|
| UI cant (operator vector) | ~31.64 m |
| Materiale folosite cant | ~31.64 m |
| Breakdown `return_material.base_quantity` | ~31.64 m |
| Breakdown `return_material.priced_quantity` | ~37.97 m (+20%) |
| LED exterior | ~20.97 m (separate, unchanged) |

---

## Tests

### Backend

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_material_breakdown.py tests/test_intake_v4_sheet_footprint_override.py tests/test_intake_v4_cant_breakdown_alignment.py tests/test_intake_v4_edge_cant_ui_hardening.py -q
```

**Result:** 59 passed (2026-06-24).

Phase B1 cases covered:

1. `return_material` base uses vector letters, not LED outer  
2. Emblem perimeter on separate row when `separate_emblem` + cant active  
3. Raster/print artwork without cant excluded  
4. `priced_quantity` = base × 1.20, waste separate  
5. LED geometry unchanged  
6. Missing vector → warning, no row, no bbox fallback  

### Frontend regression (no changes)

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/components/workos/intake-v4/IntakeV4EdgeCantReviewCard.test.tsx `
  src/lib/intakeV4/intakeV4EdgeCantDisplay.test.ts `
  src/lib/intakeV4/intakeV4LiveMaterialsUsedDisplay.test.ts `
  src/components/workos/intake-v4/IntakeV4LiveCalculationSummary.test.tsx
```

**Result:** 26/26 passed (2026-06-24).

---

## Boundary

**In scope:** Material breakdown `return_material` quantity alignment only.

**Out of scope:** ProductSystem, CostEngine final, task generation, ExecutionPlan, pricing registry, frontend, quote_geometry persistence shape, edge cant operation quantities (still use geometry letter_return for adhesive/bond scope).

---

## Next steps

1. Optional: persist `operator_cant_perimeter_m` on quote_geometry for cross-service reuse.  
2. Runtime verify Ana Maria workspace after save/reanalyze with live `perimeter_m` hydration.  
3. Phase B2+ — ProductSystem cant task derivation when registry integration starts.

---

## Phase B1.1 — Cant-active print_laminate emblem in return_material (2026-06-24)

### Problem

Ana Maria workspace (`IV4-8D89E354`): UI cant ~31.64 m (letters ~26.75 m + emblem ~4.89 m), but `return_material.base_quantity` stayed ~26.75 m. Root cause: `_artwork_row_counts_for_operator_cant` excluded `print_laminate` execution type and `printed_artwork` layer role even when cant was active.

### Fix

Align backend with `intakeV4EdgeCantDisplay.buildIntakeV4EdgeCantLayerBreakdown`:

```text
operator_cant artwork rule =
  return_finish_active(artwork.return_finish_type)
  AND vector perimeter from svg_analysis_json.layers (no bbox fallback)
```

- `print_laminate` with cant active → included in operator cant sum and combined `return_material` row.
- `print_laminate` without cant → excluded (letters-only base).
- Raster-only / missing vector → warning `missing_artwork_perimeter`, letters-only base.
- LED ~20.97 m unchanged.

Also simplified `_artwork_included_in_aggregated_volumetric_cant` so combined row label/quantity does not strip emblem when cant active.

### Files changed (B1.1)

| File | Change |
|------|--------|
| `backend/services/intake_v4_material_breakdown_service.py` | Artwork cant inclusion matches UI |
| `backend/tests/test_intake_v4_cant_breakdown_alignment.py` | print_laminate cant sum + raster warning cases |
| `docs/qa/BUILD_INTAKE_V4_PHASE_B1_CANT_BREAKDOWN_ALIGNMENT.md` | B1.1 subsection |

### Expected Ana Maria (after B1.1)

| Metric | Value |
|--------|-------|
| `return_material.base_quantity` | ~31.64 m |
| `return_material.priced_quantity` | ~37.97 m (+20%) |
| LED exterior | ~20.97 m (unchanged) |
| Emblem print-only no cant | ~26.75 m (letters only) |
