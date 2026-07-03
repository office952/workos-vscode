# FIX_INTAKE_V4_ORPHAN_SPLIT_ROLE_PROPAGATION_AND_SHEET_QUOTE_CANDIDATES

## 1. Problem statement

Ana Maria (`fara_layere` / PowerClip SVG) showed six `split_layer_1_*` nesting placements (~2.32 m²) with no layer/role metadata. Material Breakdown used eligible-face floor (1.2638 m²) for quote quantity while auto shelf layout reported 5.36 m² occupied — far from owner manual Corel layout (~2.76 m²). Operators could not compare candidate sheet areas in one place.

## 2. Ana Maria before

| Metric | Value (m²) |
|--------|------------|
| eligible_face_area_sum | 1.2638 |
| placement_footprint_face (pre-floor) | 1.1469 |
| unknown / orphan placements | ~2.321 (6× `split_layer_1_*`) |
| owner manual Corel footprint | 2.7627 |
| layout_occupied (usedWidth × consumedLength) | 5.36 |
| selected quote (plexiglas face, floored) | 1.2638 |

## 3. Root cause

Paths inside `<defs>/<clipPath>` in `ana-maria-gradinita-fara-layere.svg` were parsed as production geometry. Subpath extraction created unassigned `split_layer_N_M` parts with **no** `source.layerId` / `source.layerName` and **no** confirmed role. These are clip/mask reference geometry, not face pseudo-layer children. PBL (`split_layer_x0020_2_*`) is unrelated — those retain Corel layer metadata.

Metadata loss points:

1. `parseSvg.ts` — walked into `defs`/`clipPath` without exclusion flag  
2. `subPathExtractor.ts` — included all paths  
3. Nesting — placed orphan parts on shelf  
4. Backend role classifier — no layer → unclassified / unknown bucket  

## 4. Fix (scoped)

**Frontend (fresh analyze)**

- Mark paths inside `defs` / `clipPath` / `mask` / `symbol` with `excludeFromPartExtraction`  
- Filter excluded paths in `subPathExtractor.ts`  

**Backend (stale snapshots + reporting)**

- Detect orphan pattern `^split_layer_\d+_\d+$` without layer metadata  
- Exclude from face/backing material split footprint  
- Track as `orphan_defs_split_placement_sqm` in quote candidates (not as face)  

**Quote candidates (additive, no pricing change)**

- `eligible_face_area_sqm`, `placement_footprint_face_sqm`, `face_union_bbox_sqm`, `layout_occupied_area_sqm`, `full_sheet_allocation_sqm`, `selected_quote_sheet_area_sqm`, `selected_quote_sheet_area_source` on material breakdown response  
- UI: **Detalii tehnice / debug** → “Candidați material placă”  

**Policy preserved**

- `selected_quote_sheet_area_sqm` = current floored quantity  
- `selected_quote_sheet_area_source` = `eligible_area_floor` when floor applied  

PBL guard: Corel `Layer_x0020_1/2/3` unchanged; `split_layer_x0020_*` parts keep layer metadata.

## 5. Ana Maria after (stale workspace `2aeda68b-…`, backend filter on persisted nesting)

| Metric | Before | After |
|--------|--------|-------|
| eligible | 1.2638 | 1.2638 |
| placement_footprint_face | 1.1469 | 1.1469 |
| unknown_placement | ~2.321 | **null** (reclassified) |
| orphan_defs_split | — | **2.3211** (tracked, excluded) |
| face_union_bbox | — | **1.4069** |
| layout_occupied | 5.36 | 5.36 |
| selected quote | 1.2638 | **1.2638** (unchanged) |

**Fresh re-analyze** (frontend defs exclusion): `split_layer_1_*` parts/placements should not be created; orphan_defs → null.

**Owner manual (2.7627 m²):** not matched by any single auto field. Closest auto signals: orphan footprint was ~2.32 m² (now labeled/excluded); face union bbox ~1.41 m²; layout occupied still overstates.

## 6. PBL control (`a6cb9f56-…`, `pbl-layere.svg`)

| Metric | Value |
|--------|-------|
| Corel layers | 3 (`Layer_x0020_1` artwork, `2`+`3` face) |
| eligible_face_area_sqm | 0.6907 |
| placement_footprint_face | 0.5834 |
| face_union_bbox | 1.1577 |
| layout_occupied | 1.1577 |
| unknown / orphan_defs | null |
| selected quote | 0.6907 (`eligible_area_floor`) |

Regression gate + Playwright smoke: PASS.

## 7. Why we do not switch directly to layout_occupied (5.36 m²)

Shelf MVP nesting packs bounding boxes with spacing on a 3000×2000 mm sheet. `usedWidthMm × consumedLengthMm` reflects **algorithm shelf footprint**, not owner Corel manual layout (2.76 m²) nor geometric face area (1.26 m²). Switching quote quantity to 5.36 m² would over-quote Ana Maria ~2× vs manual layout and ~4× vs eligible geometry without operator review.

## 8. Candidate material metric table

| Field | Meaning | Ana Maria (stale) |
|-------|---------|-------------------|
| `eligible_face_area_sqm` | Sum confirmed face layer filled areas | 1.2638 |
| `placement_footprint_face_sqm` | Σ face-classified placement bboxes (pre-floor) | 1.1469 |
| `face_union_bbox_sqm` | Union bbox of face placements on sheet | 1.4069 |
| `layout_occupied_area_sqm` | Auto nesting shelf rectangle | 5.36 |
| `full_sheet_allocation_sqm` | Physical sheet stock (1× 3000×2000) | 6.0 |
| `orphan_defs_split_placement_sqm` | Excluded defs/clipPath splits | 2.3211 |
| `selected_quote_sheet_area_sqm` | **Current** material line qty | 1.2638 |
| `selected_quote_sheet_area_source` | `eligible_area_floor` | floor policy |

## 9. Remaining decision — commercial sheet quote policy

Options for next build (needs owner sign-off):

1. **face_union_bbox** — tighter than sum of bboxes, still below manual 2.76 m² for Ana Maria  
2. **layout_occupied** — risks over-quote on sparse shelf layouts  
3. **Operator override** — manual Corel footprint entry with audit trail  
4. **Full sheet / fraction policy** — stock-oriented, separate from geometry estimate  

Recommended path: keep floor as default; use candidate table + optional operator override toward manual layout where auto layout is unreliable.

## Files changed

- `frontend/src/lib/svgAnalyzer/analyzer/parseSvg.ts`
- `frontend/src/lib/svgAnalyzer/analyzer/types.ts`
- `frontend/src/lib/svgAnalyzer/part-extractor/subPathExtractor.ts`
- `frontend/src/lib/svgAnalyzer/analyzer/svgAnalyzerRegressionGate.test.ts`
- `backend/services/intake_v4_nesting_material_precision.py`
- `backend/services/intake_v4_material_breakdown_service.py`
- `backend/schemas/intake_v4.py`
- `backend/tests/test_intake_v4_nesting_material_precision.py`
- `frontend/src/lib/intakeV4/intakeV4Api.ts`
- `frontend/src/components/workos/intake-v4/IntakeV4MaterialBreakdownPanel.tsx`
- `frontend/src/components/workos/intake-v4/IntakeV4MaterialBreakdownPanel.test.tsx`

## Commands + results

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_nesting_material_precision.py tests/test_intake_v4_material_breakdown.py -q
# 40 passed

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/svgAnalyzer/analyzer/svgAnalyzerRegressionGate.test.ts
npx --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v4/IntakeV4MaterialBreakdownPanel.test.tsx
# 12 passed

$env:PW_SKIP_WEB_SERVER='1'
npx --yes pnpm@8.10.0 exec playwright test e2e/intake-v4-analyzer-regression-gate-smoke.spec.ts
npx --yes pnpm@8.10.0 exec playwright test e2e/intake-v4-corel-reference-perimeter-smoke.spec.ts
# PASS
```

## Boundary

No Pricing Registry, Color Registry, CostEngine, QuoteWizard, quote/order/task creation, ExecutionPlan, `tasks_json`, stock consumption, or full-sheet commercial policy changes.
