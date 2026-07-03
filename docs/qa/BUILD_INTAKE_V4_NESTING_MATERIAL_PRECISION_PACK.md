# BUILD_INTAKE_V4_NESTING_MATERIAL_PRECISION_PACK

**Date:** 2026-06-22  
**Status:** PASS (scoped nesting precision for quote material breakdown)  
**Branch:** `local/integration-pr4-plus-svg-path`  
**HEAD before:** `98f1c88bbaba1fd5cac88c5b14b5d4bf5000331a`  
**Commit:** none (awaiting user confirmation)

---

## Purpose

Replace interim **sheet pro-rata** plexiglas/Forex allocation with **placement-aware role/part-kind split** when nest2 metadata allows, while keeping explicit fallbacks and `stock_consumption=false`.

---

## Working tree before (off-scope dirty — do NOT include in commit)

V2/V3 operator workspace, AuthContext, `tmp/`, untracked E2E off-scope, atoms docs — unchanged from prior builds.

---

## Files audited

| Path | Role |
|------|------|
| `frontend/src/lib/svgAnalyzer/nesting/nestingTypes.ts` | Nesting report schema (placements, jobs, aggregates) |
| `frontend/src/lib/svgAnalyzer/nesting/buildNestingReport.ts` | Job construction (layer/color roll split, global sheet) |
| `frontend/src/lib/svgAnalyzer/nesting/sheetNesting.ts` | Sheet placements + `usedSheetAreaSqm` |
| `frontend/src/lib/svgAnalyzer/nesting/rollNesting.ts` | Roll jobs + `usedRollAreaSqm` |
| `frontend/src/lib/svgAnalyzer/part-extractor/partTypes.ts` | `derivedPartKind`, `materialLabel`, part ids |
| `backend/services/intake_v4_material_breakdown_service.py` | V4 material rows + pricing apply |
| `backend/services/intake_v4_quote_geometry_service.py` | Layer role helpers |
| `backend/tests/test_intake_v4_material_breakdown.py` | Existing breakdown tests |

---

## Files modified (in-scope)

| File | Change |
|------|--------|
| `backend/services/intake_v4_nesting_material_precision.py` | **New** — sheet role split + roll estimate |
| `backend/services/intake_v4_material_breakdown_service.py` | Wire precision module; warnings; basis/confidence |
| `backend/tests/test_intake_v4_nesting_material_precision.py` | **New** — unit tests for split logic |
| `backend/tests/test_intake_v4_material_breakdown.py` | Extended integration tests |
| `frontend/src/components/workos/intake-v4/IntakeV4MaterialBreakdownPanel.tsx` | Basis/confidence labels + copy |
| `docs/qa/BUILD_INTAKE_V4_NESTING_MATERIAL_PRECISION_PACK.md` | This document |

**Not touched:** CostEngine, svgAnalyzer nesting engine, V2/V3 dirty, stock consumption, pricing BLK-18 logic.

---

## Nesting metadata audit

### Verdict: **partial — sufficient for role split when placements + parts + layer roles exist**

| Field | Available in `svg_analysis_json.nesting`? | Used by V4 |
|-------|------------------------------------------|------------|
| `sheets[]` / `rolls[]` | yes | yes |
| `usedSheetAreaSqm`, `sheetsUsed`, `configId` | yes | yes (dominant sheet) |
| `placements[]` (`partId`, `sourceLayerName`, bbox mm) | yes | **yes (new)** |
| `usedRollAreaSqm`, roll jobs by layer/color | yes | yes |
| `derivedPartKind` on placement | **no** (on `parts.items`) | mapped via `partId` |
| `confirmed_role` | **no** (on `layer_role_setup`) | mapped via layer name |
| Per-material bucket id in nesting | no | derived in code |

Placements **can** be mapped to child parts → layer role / derived part kind. Without placements, only geometry pro-rata fallback remains (explicitly warned).

---

## Logic before vs after

### Before (`4700e45` / `98f1c88`)

- Sheet: `usedSheetAreaSqm` pro-rated between face/backing using **geometry area ratio** (`face/(face+backing)`).
- Warning: `sheet_nesting_prorated` always when both areas present.
- Roll: sum `usedRollAreaSqm` (unchanged conceptually).
- Basis: generic `sheet_nesting_quote_estimate`.

### After (this build)

1. Pick dominant sheet layout (largest `usedSheetAreaSqm`).
2. Classify each **placement** → `face` | `backing` via:
   - `derivedPartKind` (`back-cover-plate`, `diffuser-plate`, …)
   - `layer_role_setup.confirmed_role` (`face`, `backing`, `support_panel`)
   - `materialLabel` heuristics (Forex/Plexiglas)
3. Allocate `usedSheetAreaSqm` by **placement area share** (not geometry ratio) when classified.
4. Partial unknown placements → geometry pro-rata for unknown share + warning.
5. No placements → `sheet_nesting_prorated_fallback` (same math as before, renamed basis).

---

## Material calculation summary

| Material | Quantity source | `quantity_basis` | Waste on qty? |
|----------|-----------------|------------------|---------------|
| Plexiglas față | Sheet nesting role/part split | `sheet_nesting_role_split_quote_estimate` / `sheet_nesting_part_kind_quote_estimate` / `sheet_nesting_prorated_fallback` | **no** |
| Forex spate | Same | same | **no** |
| Oracal vinil | Roll `usedRollAreaSqm` sum | `roll_nesting_quote_estimate` | **no** |
| Oracal fallback | Letter group / geometry area | `area_with_waste_fallback` | **yes (20%)** |
| Print vinyl | Face / artwork area | `print_area_quote_estimate` | **yes** |
| Laminare | Same area as print | `laminate_area_quote_estimate` | **yes** |
| Cant | Return perimeter ml | `perimeter_with_waste` | **yes** |
| LED | Pitch formula / finish count | `led_modules_perimeter_pitch_estimate` | default waste |
| PSU | `psu_configuration` variants | `psu_configuration_quote_estimate` | default waste |

Pricing: unchanged BLK-18 via `load_material_pricing_dict` (`98f1c88`).

---

## `quantity_basis` values (V4)

| Code | When |
|------|------|
| `roll_nesting_quote_estimate` | Valid roll jobs |
| `sheet_nesting_role_split_quote_estimate` | Full/partial placement role split |
| `sheet_nesting_part_kind_quote_estimate` | Split driven by `derivedPartKind` |
| `sheet_nesting_prorated_fallback` | No placement metadata |
| `area_with_waste_fallback` | No roll nesting for Oracal |
| `perimeter_with_waste` | Cant / return |
| `print_area_quote_estimate` | Print finish / artwork |
| `laminate_area_quote_estimate` | Lamination row |
| `led_modules_perimeter_pitch_estimate` | LED count |
| `psu_configuration_quote_estimate` | PSU picks |

---

## `confidence` values (V4)

| Code | When |
|------|------|
| `estimate_from_nesting_high` | Full valid nesting split / roll |
| `estimate_from_nesting_medium` | Partial split, prorated fallback, unplaced roll items |
| `estimate_fallback_area` | Area fallback |
| `estimate_fallback_perimeter` | Perimeter cant |
| `estimate_formula` | LED / PSU |
| `estimate_missing_metadata` | Sheet split impossible |

---

## Warnings

| Code | Meaning |
|------|---------|
| `nesting_used_for_quote_not_stock` | Nesting drives quote qty, not inventory |
| `sheet_nesting_role_split_partial` | Some placements unclassified; geometry used for unknown share |
| `sheet_nesting_prorated_fallback` | No placement metadata; geometry pro-rata |
| `missing_placement_role_metadata` | Unclassified placements remain |
| `roll_nesting_color_split_missing` | Multiple vinyl colors merged in one Oracal row |
| `area_fallback_used` | Oracal without roll nesting |
| `missing_price_metadata` | (reserved — BLK-18 missing price on row) |

---

## Quote nesting estimate vs stock

| Layer | Behavior |
|-------|----------|
| V4 breakdown | `stock_consumption=false`, `consumption_mode=quote_estimate_not_stock` |
| Nesting qty | `usedSheetAreaSqm` / `usedRollAreaSqm` — includes nesting waste, **not** sheet leftovers |
| Fallback | Geometry area/perimeter + 20% waste where nesting absent |
| Inventory | **Not** decremented |

---

## Tests run

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_material_breakdown.py tests/test_intake_v4_nesting_material_precision.py tests/test_intake_v4_pricing_registry_alignment.py -q
```

**Result:** `27 passed`

Frontend Vitest: omitted — copy/label mapping only.

E2E: not run (stack not required for PASS; optional follow-up).

---

## PASS criteria

| Criterion | Status |
|-----------|--------|
| Role split when metadata sufficient | ✅ |
| Pro-rata explicit fallback + warning | ✅ |
| Oracal roll nesting preferred | ✅ |
| Print/laminare separate from Oracal | ✅ |
| Clear basis/confidence | ✅ |
| No double waste on nesting rows | ✅ |
| No stock consumption | ✅ |
| BLK-18 pricing unchanged | ✅ |
| UI explains estimate vs stock | ✅ |
| Backend tests pass | ✅ |
| V2/V3 untouched | ✅ |

---

## Risks remaining

1. **Sheet jobs are global** — face/backing parts share one sheet layout; split depends on placements + roles, not separate sheet jobs per material.
2. **Multi-color Oracal** — single row + warning (accepted for this build).
3. **Placement ↔ part id** — quantity copies use `_qN` suffix; index handles base id.
4. **Analyzer gap** — `derivedPartKind` not on placement payload; requires `parts.items` join (documented).

---

## Recommendation

**Recommend commit** (scoped files only):

```
feat(intake-v4): improve sheet nesting material split by role and placement
```

---

## Follow-ups

1. Emit `derivedPartKind` / `materialIntent` on `NestingPlacement` in svgAnalyzer (reduces join fragility).
2. Optional per-material sheet jobs for face vs backing when template supports it.
3. Split Oracal material rows by `colorKey` when pricing registry supports it.
4. E2E: Review shows `sheet_nesting_role_split_quote_estimate` after live upload.
