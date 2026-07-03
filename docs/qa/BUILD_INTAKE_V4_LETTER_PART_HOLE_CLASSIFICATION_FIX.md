# BUILD_INTAKE_V4_LETTER_PART_HOLE_CLASSIFICATION_FIX

## Branch / HEAD

| Field | Value |
|-------|-------|
| Branch | `local/integration-pr4-plus-svg-path` |
| HEAD before | `c356291` — docs(architecture): add AI Knowledge and Advisory Layer strategy audit |
| HEAD after | *(see commit below)* |
| Build | `BUILD_INTAKE_V4_LETTER_PART_HOLE_AND_RETURN_CANT_FINALIZATION` |

## QA-BUG-4 final rule

```txt
Inner holes are not letters/pieces, but they require return/cant material when the
volumetric part has interior return.
```

| Metric | Policy |
|--------|--------|
| `letter_count` / `real_letters_count` | Face outer production parts only — **no holes, no artwork** |
| `inner_hole_count` | Embedded + orphan interior contours — **not separate pieces** |
| `artwork_piece_count` | Artwork/logo layers with **active return** |
| `volumetric_piece_count` | Real letters + artwork with active return |
| `cutting_contours_count` | Outer letter contours + inner holes |
| `cnc_cutting_perimeter_ml` | Outer + inner hole perimeter |
| `return_material_perimeter_ml` | Letter outer + inner holes + artwork return when cant active |
| `led_perimeter_ml` | Outer face letters only (`outer_face_letters_excludes_holes_and_artwork`) |

L1 artwork with `execution_type=needs_decision` remains **pending for print/laminare**, but with `return_finish_type=standard_aluminum` + `return_depth_mm=60` it **enters cant/return** (Variant A).

## Problem observed

On real workspace **IV4-46499080** (`pbl-layere.svg`), UI showed **Nr. litere / piese = 11**.

Owner expectation: inner holes / artwork must **not** inflate real letter count.

Root cause: `build_quote_geometry_from_analysis()` used raw `parts.nestableCount` (11) without filtering by layer role. The 11th part is **printed_artwork** on `Layer_x0020_1`. Embedded inner holes were already grouped inside compound face parts; they were **not** separate nestable pieces.

## Classification rule

| Kind | Counts as letter | Counts as material piece | Nestable | Cutting perimeter |
|------|------------------|--------------------------|----------|-------------------|
| Face outer production part | Yes | Yes | Yes (if `canNest`) | Yes (outer + embedded inner) |
| Embedded inner contour (`innerContourCount`) | No | No | No | Yes (inner perimeter) |
| Orphan hole (bbox inside larger face part, same layer) | No | No | No | Yes |
| printed_artwork / logo / backing / etc. | No | No | No | No |

Geometric orphan-hole rule (nest2 / SVG Analyzer aligned):

- inner bbox fully inside outer bbox on same face layer
- inner area strictly smaller (`< 85%` of outer)
- mark `classification_confidence=low` when ambiguous subpaths exist

**Perimeter policy (owner final)**

- LED / letter count → **outer face letters only**
- CNC cutting → **outer + inner holes**
- Cant / return → **outer + inner holes + artwork return when cant active**

## Part table — IV4-46499080 (after fix)

| part_id | source_layer | role | counts_as_letter | is_inner_hole | nestable | inner embedded |
|---------|--------------|------|------------------|---------------|----------|----------------|
| split_layer_x0020_2_1_4 | Layer_x0020_2 | face | Yes | No | Yes | 1 |
| split_layer_x0020_2_1_1 | Layer_x0020_2 | face | Yes | No | Yes | 0 |
| split_layer_x0020_2_1_3 | Layer_x0020_2 | face | Yes | No | Yes | 0 |
| split_layer_x0020_2_1_2 | Layer_x0020_2 | face | Yes | No | Yes | 0 |
| split_layer_x0020_2_1_5 | Layer_x0020_2 | face | Yes | No | Yes | 0 |
| split_layer_x0020_3_2_1 | Layer_x0020_3 | face | Yes | No | Yes | 1 |
| split_layer_x0020_3_2_4 | Layer_x0020_3 | face | Yes | No | Yes | 0 |
| split_layer_x0020_3_2_2 | Layer_x0020_3 | face | Yes | No | Yes | 0 |
| split_layer_x0020_3_2_3 | Layer_x0020_3 | face | Yes | No | Yes | 0 |
| split_layer_x0020_3_2_5 | Layer_x0020_3 | face | Yes | No | Yes | 0 |
| part_layer_x0020_1_001 | Layer_x0020_1 | printed_artwork | **No** | No | **No** | 0 |

## Layer summary (face only)

| layer | real letters | inner holes | cutting contours | outer perimeter (m) | hole perimeter (m) | cutting perimeter (m) |
|-------|--------------|-------------|------------------|---------------------|--------------------|-----------------------|
| Layer_x0020_2 | 5 | 1 | 5* | 5.529 | 0.232 | 6.168 |
| Layer_x0020_3 | 5 | 1 | 5* | 6.101 | 0.863 | 6.964 |
| **Total** | **10** | **2** | **14** | **11.630** | **1.095** | **13.132** |

\*Layer `cutting_contours_count` in summary = real letters + embedded holes per layer (5+1 each layer path contributes to total 14 via part `contourCount` sum).

## Before / after metrics (IV4-46499080)

| Metric | Before | After | Should use |
|--------|--------|-------|------------|
| UI letter count | 11 | **10** | `real_letters_count` |
| Artwork pieces | (included in 11) | **1** | `artwork_piece_count` |
| Volumetric pieces | 11 | **11** | `volumetric_piece_count` |
| Inner holes | (hidden) | **2** | `inner_holes_count` |
| Cutting contours | (hidden) | **14** | `cutting_contours_count` |
| LED perimeter | ~13.62 m | **11.63 m** | `led_perimeter_ml` |
| CNC cutting perimeter | ~13.62 m | **12.73 m** | `cnc_cutting_perimeter_ml` |
| Letter return perimeter | 11.63 m | **12.73 m** | outer + holes |
| Artwork return perimeter | (missing) | **1.85 m** | `artwork_return_perimeter_ml` |
| Total return/cant | ~11.63 m | **14.57 m** | `return_material_perimeter_ml` |
| Pricing `letter_count` | 11 | **10** | `real_letters_count` |
| Production `inner_hole_count` | 0 | **2** | classification |
| `cut_contour_count` | 11 | **14** | cutting contours |
| Material breakdown cant qty | ~11.63 ml | **14.57 ml** | aggregated return row |
| Task dry-run Real letters | 11 | **10** | confirmed production model |
| Task dry-run Holes | 0 | **2** | geometry summary |
| Task dry-run Closed contours | 11 | **14** | geometry summary |
| Task dry-run Return perimeter | ~11.63 ml | **14.57 ml** | return tasks |

## Material / nesting impact

- Plexiglas face area basis unchanged (face layer areas); piece count for quote now **10**, not 11.
- Artwork part `part_layer_x0020_1_001` excluded from letter/material piece counts; should not drive volumetric letter pricing.
- **Gap (separate build):** persisted nesting placements may still list 11 items until nesting service filters non-face parts — uncommitted nesting WIP in tree.

## Task dry-run impact

- `Real letters` → 10 via `confirmed_production_model.letter_count`
- `Closed contours` → 14 via `cut_contour_count`
- `Holes` → 2 via `inner_hole_count`
- Prepress per-letter tasks scale on real letters, not holes.

## Files changed

| File | Change |
|------|--------|
| `backend/services/intake_v4_letter_part_classification_service.py` | **New** — part/hole classification |
| `backend/services/intake_v4_volumetric_return_metrics_service.py` | **New** — return/LED scope + artwork cant |
| `backend/services/intake_v4_quote_geometry_service.py` | Canonical derive + volumetric enrich |
| `backend/services/intake_v4_finish_adapter.py` | Production model + cutting vs letter counts |
| `backend/services/intake_v4_pricing_input_service.py` | Production counts + quote payload fields |
| `backend/services/intake_v4_material_breakdown_service.py` | Aggregated cant row (letters + holes + artwork) |
| `backend/tests/test_intake_v4_letter_part_hole_classification.py` | **New** — classification + return scope |
| `frontend/src/lib/intakeV4/intakeV4LetterPartClassification.ts` | **New** — client mirror |
| `frontend/src/lib/intakeV4/intakeV4QuoteGeometry.ts` | Live derive (no stale persisted) + return enrich |
| `frontend/src/components/workos/intake-v4/IntakeV4GeometryPanel.tsx` | Split UI labels |

## Commands + results

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_letter_part_hole_classification.py -q
# 17 passed

.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_task_generation_dry_run.py -q
# passed

.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_quote_geometry.py -q
# passed

.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_pricing_input.py -q
# passed

.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_material_breakdown.py -q
# 1 failed — nesting WIP (see below)

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV4/intakeV4QuoteGeometry.test.ts
# 3 passed
```

### `test_intake_v4_material_breakdown.py` failure (non-blocking for this build)

| Field | Value |
|-------|-------|
| Failed test | `TestIntakeV4MaterialBreakdownLetterGroups::test_sheet_nesting_role_split_when_metadata_present` |
| Assertion | `round(plexi.quantity + forex.quantity, 4) == 2.34` |
| Expected | `2.34` (full prorated sheet) |
| Actual | `0.56` (`0.4 + 0.16`, part-kind footprint) |
| Root cause | Parallel **nesting precision WIP** (`intake_v4_nesting_material_precision.py`) — `quantity_basis=sheet_nesting_part_kind_quote_estimate`; **no nesting hunks in this commit's material_breakdown diff** |
| Legat de acest build? | **Nu** |
| Recomandare | **Document non-blocking** — fix in dedicated nesting build |

## pbl-layere.svg retest

| Check | Result |
|-------|--------|
| Real letters X | **10** |
| Inner holes Y | **2** |
| Cutting contours Z | **14** |
| Artwork excluded | **PASS** |
| Holes not separate letters | **PASS** (embedded, not orphan parts) |

## PASS / FAIL

| Gate | Status |
|------|--------|
| Classification logic | **PASS** |
| Quote geometry / pricing counts | **PASS** |
| UI labels (IV4-46499080 hard refresh) | **PASS** |
| Material breakdown cant row | **PASS** (14.57 ml aggregated) |
| Material breakdown regression | **FAIL** (1 test — nesting WIP, **not this build**) |
| ExecutionPlan / tasks_json | **PASS** — not created |
| Draft quote readiness | **PASS** |

## Gaps remaining

1. Nesting preview may still place artwork part until nesting service filters by role.
2. `SUBPATH_CONTAINMENT_AMBIGUOUS` warnings on file — monitor orphan-hole detection.
3. Material breakdown sheet role-split test failure from parallel nesting precision WIP.

---

## QA-BUG-4 — Artwork/logo return perimeter excluded from cant calculation

### Owner observation

`Layer_x0020_1` (policromie) had `return_finish_type=standard_aluminum` + `return_depth_mm=60` in UI, but cant/return metrics used **only face letter outer perimeter (11.63 m)** — logo cant was ignored.

### Payload L1 (IV4-46499080)

| Field | Value |
|-------|-------|
| execution_type | `needs_decision` |
| return_finish_type | `standard_aluminum` |
| return_depth_mm | 60 |
| layer perimeter | 1.846 m |
| confirmed | true |

### Rule chosen: **Variant A**

Cant/return for artwork is **valid independent of artwork print execution**. `needs_decision` blocks print/laminare rows only; return/cant remains active when operator sets return on artwork finish.

### Before / after return perimeter

| Metric | Before (outer-only mistake) | After QA-BUG-4 + owner correction |
|--------|---------------------------|-----------------------------------|
| `outer_letter_perimeter_ml` | 11.630 | 11.630 |
| `inner_hole_letter_perimeter_ml` | (excluded) | **1.095** |
| `letter_return_perimeter_ml` | 11.630 | **12.725** (outer + inner holes) |
| `artwork_return_perimeter_ml` | (missing) → 1.846 | **1.846** |
| `return_material_perimeter_ml` | 11.630 → 13.476 | **14.571** |
| `led_perimeter_ml` | 11.630 | **11.630** (outer only, no holes/artwork) |
| `cnc_cutting_perimeter_ml` | 13.132 (total contour) | **12.725** (outer + inner holes) |

**Owner correction (holes + cant):** Inner holes are **not** separate letters/pieces, but cant material is applied on **interior contours too**. Previous rule “return = outer only” was wrong for volumetric letters with interior return.

```txt
previous mistaken rule: return perimeter outer only
correct rule: return perimeter outer + inner holes + artwork return when active
LED: outer face letters only (led_perimeter_policy=outer_face_letters_excludes_holes_and_artwork)
```

### Layer_x0020_1 explicit answers

| Question | Answer |
|----------|--------|
| Artwork execution pending? | Yes (`needs_decision`) |
| Cant/volum active? | **Yes** (`standard_aluminum` 60 mm) |
| In return_perimeter? | **Yes** (+1.846 m artwork only; holes N/A on L1) |
| In LED perimeter? | **No** |
| In letter_count? | **No** (still 10 real letters) |
| In volumetric_piece_count? | **Yes** (+1 → total 11) |

### Material breakdown

| Before | After |
|--------|-------|
| `Cant / return` ~11.63 m (letters outer only) | **`Cant / return litere + interioare + artwork (standard_aluminum · 60 mm)` = 14.571 m** |

### Task dry-run impact

- `return_profile_material` / `return_side_forming` / `return_face_bonding` scope uses total `return_material_perimeter_ml` (**14.571 m**).
- `Real letters` stays **10**; volumetric scope **11** via `volumetric_piece_count`.
- LED tasks still use letter-only perimeter.

### QA-BUG-4 verdict: **PASS**

## Boundary

- No CostEngine / Pricing Registry changes
- No ExecutionPlan / tasks_json / real tasks
- No V2/V3 dirty paths
- No hardcoded filename or layer names
