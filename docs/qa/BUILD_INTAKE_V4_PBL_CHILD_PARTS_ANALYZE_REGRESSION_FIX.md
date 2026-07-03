# BUILD_INTAKE_V4_PBL_CHILD_PARTS_ANALYZE_REGRESSION_FIX

## Purpose

Fix fresh Intake V4 analyze/persist path for `pbl-layere.svg` (hash `c674e8a3…`) so child-part truth matches golden workspace `IV4-46499080` instead of collapsing to 3 layer-level parts.

## Blocker (before fix)

**NO PASS — analyzer blocker** on full operator flow:

| Metric | Golden `IV4-46499080` | Fresh `IV4-6206EFED` (broken) |
|--------|----------------------|-------------------------------|
| `parts.items` | 11 | 3 |
| `groupsCreated` | 10 | 2 |
| Face split `canNest` | true (valid bounds) | false (0×0 bounds) |
| Plexiglas face | ≈ 0.5834 m² | 6.0 m² full-sheet fallback |
| Nesting active sheet | useful placements | empty / degraded |

Same SVG bytes, same hash — mismatch was **not** persistence truncation.

## Root cause

1. **Canonical analyzer** = frontend `analyzeSvgString` → `extractSubPaths` → `groupSubPathsByShape` (nest2 port).
2. Fresh path persists client bundle via `PUT /analysis-bundle` (no server-side child-part re-analyze).
3. `measurePathShape` preferred detached DOM `getBBox()` for CorelDRAW relative paths (`l0`, comma decimals).
4. In happy-dom and some browser contexts, `getBBox()` returns **0×0** while token-based `estimateBBoxAndLength` is correct.
5. All subpaths shared degenerate bounds → shape grouping collapsed each face layer to **one mega-group** (2 groups + 1 artwork = 3 parts).

Golden workspace was analyzed when bounds were valid (earlier session / non-degenerate measurement).

## Fix

### Frontend (`shapeBounds.ts`)

- Detect degenerate DOM bbox (width/height ≤ ε).
- Fall back to `estimateBBoxAndLength` when DOM measurement is missing or zero-sized.
- Treat degenerate bbox as unavailable in `subPathExtractor` / `extractParts`.

### Backend guard (`intake_v4_analysis_bundle_guard_service.py`)

- Reject degraded bundles on `PUT /analysis-bundle` with `422 degraded_child_parts_analysis`.
- Prevents client from persisting collapsed layer-level parts when `subPathCount ≥ 10` but `groupsCreated ≤ 3` or split parts have zero bounds.

## Analyzer source truth

| Path | Analyzer | Child parts |
|------|----------|-------------|
| Operator UI | Client `analyzeSvgString` (nest2) | Yes — after fix |
| `POST /svg` | Backend V3 `analyze_svg_content` | Layer-level only (unchanged) |
| Persist truth | `PUT /analysis-bundle` | Client bundle + guard |

Official Intake V4 production truth = **client nest2 analysis bundle**, guarded on persist.

## After fix (fixture + desktop verification)

Vitest on `fixtures/pbl-layere.svg` (same bytes as desktop file):

- `parts.count` = **11**
- `groupsCreated` = **10**
- `nestableCount` = **11** (10 face splits + 1 artwork)
- Face splits: valid bounds, `canNest: true`
- Nesting: active sheet layouts with placements
- Classification with L1/L2/L3 roles: `real_letters_count` = **10**

Material breakdown on golden-shaped analysis: plexiglas face **≈ 0.5834 m²**, not 6.0 m².

## Tests

### Frontend

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/svgAnalyzer/pblLayereChildParts.regression.test.ts src/lib/svgAnalyzer/part-extractor/shapeBounds.test.ts
```

### Backend

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_pbl_child_parts_analyze_regression.py -q
```

Also ran (pass):

- `tests/test_intake_v4_material_breakdown.py`
- `tests/test_intake_v4_nesting_preview.py`
- `tests/test_intake_v4_nesting_material_precision.py`
- `tests/test_intake_v4_pricing_input.py`
- `tests/test_intake_v4_task_generation_dry_run.py`

## Quote policy blocker (unchanged)

`create-draft-quote` still returns **422** `artwork_execution_undecided:Layer_x0020_1` when L1 = `needs_decision`.

Policy options (owner decision — **not implemented**):

- **A.** Keep fail-closed until artwork execution decided.
- **B.** Allow draft quote with warnings + `requires_pricing_review`.

## Production / tasks (unchanged)

- Production handoff = preview only
- Task generation = dry-run only
- No ExecutionPlan, no `tasks_json`, no stock consumption

## Full E2E status

**PARTIAL E2E PASS** after analyzer fix — stops at quote policy (`needs_decision`) and production dry-run boundary.

Runtime operator retest: upload `pbl-layere.svg` on a fresh workspace with fixed frontend build; expect same canonical counts as golden.

## Files changed

- `frontend/src/lib/svgAnalyzer/part-extractor/shapeBounds.ts`
- `frontend/src/lib/svgAnalyzer/part-extractor/subPathExtractor.ts`
- `frontend/src/lib/svgAnalyzer/part-extractor/extractParts.ts`
- `frontend/src/lib/svgAnalyzer/fixtures/pbl-layere.svg`
- `frontend/src/lib/svgAnalyzer/pblLayereChildParts.regression.test.ts`
- `frontend/src/lib/svgAnalyzer/part-extractor/shapeBounds.test.ts`
- `backend/services/intake_v4_analysis_bundle_guard_service.py`
- `backend/services/intake_v4_workspace_service.py`
- `backend/tests/test_intake_v4_pbl_child_parts_analyze_regression.py`
- `backend/tests/fixtures/intake_v4/pbl_layere_golden_analysis.json`
- `backend/tests/fixtures/intake_v4/pbl_layere_degraded_analysis.json`

## Boundary

- No Pricing Registry / CostEngine changes
- No quote policy change
- No real tasks / ExecutionPlan / stock
- No push (per owner request)
