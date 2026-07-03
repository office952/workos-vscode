# BUILD_INTAKE_V4_PBL_INNER_HOLES_VISUAL_TRUTH_FIX

## Purpose

Correct Intake V4 fresh SVG analysis for PBL-style letter interiors so `inner_hole_count` matches operator visual truth for `pbl-layere.svg` (PUBLIMEDIA), without quote policy, order creation, or production side effects.

## Context

Operator visual audit of **PUBLIMEDIA** (`pbl-layere.svg`) established:

| Letter | Inner holes (visual) |
|--------|---------------------|
| P | 1 |
| B | 2 |
| D | 1 |
| A | 1 |
| **Total** | **5** |

Previous analysis reported `inner_hole_count = 2`, under-counting letter interiors. That skewed CNC/return perimeter, material truth, and pricing preview inputs.

**Branch:** `local/integration-pr4-plus-svg-path`  
**Base HEAD:** `c0bc43c fix(intake-v4): complete PBL pricing preview signals`

## Why `inner_hole_count = 2` was wrong

The frontend subpath grouper (`groupSubPathsByShape`) classified only two closed contours as `inner` holes. Three additional visual interiors were missed because:

1. **Cross-layer geometry** — Corel export splits PUBLIMEDIA across `Layer_x0020_2` and `Layer_x0020_3`; some hole contours sit on a different layer than their parent outer letter contour.
2. **Bbox-only containment** — Holes whose bounds extend slightly outside the parent letter bbox were rejected.
3. **Fragment subpaths** — Subpaths 3 and 6 (and similar) were not promoted from global fragment pools into parent letter groups.
4. **Compound-path fill** — Single-path even-odd void detection alone did not cover all multi-subpath letter shapes; pairwise containment between closed subpaths was required.

## Root cause

Hole detection relied too heavily on same-layer bbox containment and under-counted `innerContourCount` on grouped letter parts. Backend `inner_holes_count` mirrors the sum of `innerContourCount` on face production parts via `classify_letter_parts_from_analysis`.

## Fix (analyzer — no hardcoding)

**Frontend** (`frontend/src/lib/svgAnalyzer/part-extractor/`):

- **`shapeBounds.ts`** — `isInnerContourHoleOfOuter()` using even-odd compound fill sampling; improved multi-`M` compound path handling; `minHollowRatio` guard.
- **`shapeGrouping.ts`** — `isSubPathHoleOfOuter()` with bbox tolerance (28 mm), cross-layer `promoteGlobalFragmentHoles()`, fallback parent pick when compound match fails.
- **`extractParts.ts`** — passes `mmPerVbu` for consistent mm-space containment.

Holes remain **non-nestable** metadata on parent letter parts (`canNest=true` on the 10 letter shells; hole contours are not separate nestable parts).

## Visual truth after fix

Fresh analyze of `pbl-layere.svg`:

| Metric | Before | After |
|--------|--------|-------|
| `parts.count` | 11 | 11 |
| `real_letters_count` | 10 | 10 |
| `artwork_piece_count` | 1 | 1 |
| `inner_hole_count` | 2 | **5** |
| Parts with holes | 2 | **4** (1×2 holes + 3×1 hole) |

**Nominal letter mapping:** Analyzer assigns holes by geometry/containment to layer part IDs (`Layer_x0020_2_*`, `Layer_x0020_3_*`), not by glyph labels P/B/D/A. Total count and parent-hole grouping are regression-tested; per-glyph naming is not exported by the SVG.

## Impact on derived metrics (after finish-setup sync)

| Field | Before (2 holes) | After (5 holes) |
|-------|------------------|-----------------|
| `return_material_perimeter_ml` | 14.5711 | **15.444** |
| `letter_return_perimeter_ml` | 12.725 | **13.5979** |
| `hole_perimeter_ml` | lower | **~1.984** (included in return when cant policy applies) |
| `plexiglas_face` (m²) | ~0.5834 | ~0.5834 (unchanged — face area from outers/nesting) |
| Nesting | 10 nestable + 1 artwork | unchanged |
| LED perimeter | unchanged | unchanged (outer letter perimeter) |

### Policy answers

1. **Interiors in CNC?** Yes — hole contours contribute to `cutting_perimeter_mm` / face CNC when face is cut (`hole_perimeter_mm` aggregated in classification).
2. **Interiors in cant/return?** Yes — when return finish is active, inner hole perimeters add to `return_material_perimeter_ml` (standard aluminum return on PBL smoke setup).
3. **Plexiglas area?** No change — nesting uses outer letter footprints; holes do not add separate face sheets.
4. **Nesting footprint?** No change — 10 nestable letter parts + 1 artwork; holes are not independent nestable parts.
5. **LED perimeter?** No change — driven by outer letter perimeter, not hole count.

## Tests

### Frontend (Vitest)

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/svgAnalyzer/pblLayereChildParts.regression.test.ts src/lib/svgAnalyzer/part-extractor/shapeBounds.test.ts
```

- 11 child parts, 10 real letters, 5 inner holes, 4 hole-bearing parts, no 6.0 m² fallback in nesting path.

### Backend (pytest)

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_pbl_pricing_completeness.py tests/test_intake_v4_pbl_child_parts_analyze_regression.py -q
```

- Golden fixture updated; return perimeter expectations updated to 15.444 ml.

## Runtime smoke

**Workspace:** `SMOKE-PBL-INNER-HOLES-20260622-2247` (`IV4-4B172FD4`)  
**SVG:** `C:\Users\offic\Desktop\pbl-layere.svg`

After **finish-setup** persist (required for full `quote_geometry` sync):

| Check | Value |
|-------|-------|
| `parts.count` | 11 |
| `real_letters_count` | 10 |
| `artwork_piece_count` | 1 |
| `inner_holes_count` | 5 |
| `return_material_perimeter_ml` | 15.444 |
| `plexiglas_face` | 0.5834 m² (no 6.0 fallback) |
| Nesting | active, 10 nestable + 1 artwork |

No quote, order, ExecutionPlan, `tasks_json`, or stock consumption.

## Boundary

- No quote policy change.
- No Pricing Registry / CostEngine changes.
- No V2/V3/Auth changes.
- No hardcoded PBL hole count.
- No push (local commit only).

## Remaining blockers

- Quote policy (`needs_decision` artwork execution) — **out of scope** for this build.
- Production dry-run / real task generation — unchanged; still dry-run only.
- Optional follow-up: assert nominal P/B/D/A hole assignment if SVG exports letter labels in metadata.

## Files changed

- `frontend/src/lib/svgAnalyzer/part-extractor/shapeBounds.ts`
- `frontend/src/lib/svgAnalyzer/part-extractor/shapeGrouping.ts`
- `frontend/src/lib/svgAnalyzer/part-extractor/extractParts.ts`
- `frontend/src/lib/svgAnalyzer/part-extractor/shapeBounds.test.ts`
- `frontend/src/lib/svgAnalyzer/pblLayereChildParts.regression.test.ts`
- `backend/tests/fixtures/intake_v4/pbl_layere_golden_analysis.json`
- `backend/tests/test_intake_v4_pbl_pricing_completeness.py`
