# BUILD_INTAKE_V4_REAL_FILE_MATERIAL_NESTING_TRUTH_AUDIT_AND_FIX

## Branch / HEAD

| Field | Value |
|-------|-------|
| Branch | `local/integration-pr4-plus-svg-path` |
| HEAD before | `fe9b39d9206796a1dfe286b6e9db3d74267edd0f` |
| Build date | 2026-06-22 |

## Real file context (manual upload only — not hardcoded)

| Field | Value |
|-------|-------|
| Workspace | `a6cb9f56-2d16-4a53-b569-d5fd51cabfe2` / **IV4-46499080** |
| File | `pbl-layere.svg` (operator upload) |
| Document bbox | **2700 × 350 mm** → **0.945 m²** bounding area |
| Layers | L1 `printed_artwork`, L2/L3 `face` (no backing) |
| Child parts | 11 (contour split) |

## QA-BUG-2 — Suspicious material quantity / nesting truth audit

### Screenshot / UI observation (before fix)

| Material line | Reported | Suspicion |
|---------------|----------|-----------|
| Plexiglas / față litere | **4.482 m²** | >> bbox 0.945 m² |
| Vinil față | **2.784 m²** | >> face geometry ~0.69 m² |
| Cant / return 60mm | 13.62 ml (+20% → 16.35) | plausible |
| Print + laminare L1 | 0.198 m² each | plausible |
| LED modules | 55 (+20% → 66) | formula check OK |
| PSU | 2 buc, ~267 W | config-driven |

### Expected sanity bounds

| Metric | Expected order of magnitude |
|--------|----------------------------|
| Total bbox | ~0.945 m² |
| Face layers L2+L3 geometry | ~0.69 m² (`quote_geometry.face_area_m2`) |
| Face placement footprint (sheet) | ~0.58 m² (sum L2/L3 split part bboxes) |
| Artwork L1 | ~0.198 m² |
| Face vinyl (2 colors, best roll each) | ~0.98 m² |
| Return perimeter | ~13.62 ml |

### Root cause (confirmed bug)

Two aggregation bugs in `intake_v4_nesting_material_precision.py`:

1. **Sheet plexiglas/Forex:** When placements existed, material qty used  
   `usedSheetAreaSqm × (face_placements / total_placements)`  
   where `usedSheetAreaSqm` = **full stock sheet area** (6.0 m² for `sheet_3000x2000`), not placed-part footprint (~0.78 m²).  
   For IV4-46499080: `6.0 × 0.5834 / 0.7810 = **4.482 m²**`.

2. **Roll vinyl:** `compute_roll_nesting_vinyl_estimate` **summed all roll width alternatives** (1000 mm + 1260 mm) and included **printed_artwork** roll jobs.  
   For IV4-46499080: double-count across widths + L1 artwork → **2.784 m²**.

3. **Sheet picker:** `_pick_best_sheet_layout` previously chose layout with **maximum** `usedSheetAreaSqm` (not best efficiency). Fixed to prefer highest efficiency.

**Not** unit conversion bug (mm/cm scale correct: viewBox cm × ~10 → 2700 mm).  
**Not** duplicate child parts in sheet placements (11 unique placements).

### Fix (scoped)

| File | Change |
|------|--------|
| `backend/services/intake_v4_nesting_material_precision.py` | Use **placement footprint sums** for face/backing when placements exist; pick best sheet by efficiency; roll vinyl picks **min area per layer/color** across roll widths; exclude `printed_artwork` from face vinyl roll sum |
| `backend/services/intake_v4_material_breakdown_service.py` | Pass `layer_role_setup` into roll estimate |
| `backend/tests/test_intake_v4_nesting_material_precision.py` | Regression tests for PBL-like scenario |
| `backend/tests/test_intake_v4_material_breakdown.py` | Updated role-split expectations |

### After fix (IV4-46499080 backend recompute)

| Material line | Before | After | Source |
|---------------|--------|-------|--------|
| Plexiglas față | 4.482 m² | **0.5834 m²** | Sum face-role sheet placements (L2+L3 splits) |
| Vinil față | 2.784 m² | **0.9821 m²** | Best roll per face layer/color; excludes L1 |
| Cant / return | 13.62 ml | 13.62 ml | `quote_geometry.return_material_perimeter_ml` |
| Print L1 | 0.198 m² | 0.198 m² | Layer L1 `filledAreaSqm` via artwork finishes |
| Laminare L1 | 0.198 m² | 0.198 m² | Same |
| LED modules | 55 buc | 55 buc | `ceil(perimeter_mm / 250)` → 55 |
| PSU | 2 buc | 2 buc | `finish_setup.psu_configuration` [200, 60] |

### Trace — Plexiglas față

```
11 sheet placements on sheet_3000x2000 (usedSheetAreaSqm=6.0 metadata only)
  → 10 classified face (L2/L3 split parts): Σ bbox = 0.5834 m²
  → 1 unclassified (L1 printed_artwork): 0.1976 m² → excluded from plexiglas face
material breakdown plexiglas_face = 0.5834 m² (NOT 4.482)
```

### Trace — Vinil față

```
Roll jobs L2 #009846: min(0.538 @1000mm, 0.506 @1260mm) = 0.506
Roll jobs L3 #66c3d0: min(0.501 @1000mm, 0.476 @1260mm) = 0.476
L1 printed_artwork roll job excluded
Total face_vinyl = 0.9821 m²
```

### Trace — Print / laminare

```
L1 printed_artwork → artwork_finishes print_laminate execution
Area = layer filledAreaSqm = 0.1976 m²
+20% waste on priced_quantity only (quote policy)
Not included in plexiglas_face (role ≠ face)
```

### Trace — Cant / return

```
return_material_perimeter_ml = 13.6211 ml (nest2 face layers perimeter)
Registry: MAT-PROFIL-LATERAL-LITERE-60MM (aluminum return profile)
finish: oracal_wrapped → operation flag return_vinyl_application_required
```

### Trace — LED / PSU

```
letter_perimeter_m = 13.6211 m → 13621 mm
LED count = ceil(13621 / 250) = 55 modules
required_psu_watts ≈ 227–267 W (module wattage × count + policy)
psu_configuration = [200, 60] → 2 PSU units
+20% on priced_quantity for consumables (quote waste policy)
```

## Task activation matrix (IV4-46499080)

| Finish / material | Tasks expected | Status |
|-------------------|----------------|--------|
| Față Oracal (L2/L3) | `vinyl_cutting`, `face_finish_application` | Active via finish adapter |
| Față printată (L1) | `printed_artwork_production`, `print_lamination` | Active via artwork execution |
| Cant colantat Oracal | `return_vinyl_application_workbench` before `return_side_forming` | **Active (operation flag)** |
| Cant material cost | Profile `MAT-PROFIL-LATERAL-LITERE-60MM` priced | **GAP:** no separate Oracal roll line for cant wrap — labor via task, not vinyl ml |
| Backing lipsă | `cnc_backing_cutting` | **Inactive** (no backing layer) — **WARNING**, not auto Forex |
| LED | `led_module_install`, `psu_electrical` | Active (illuminated) |
| Assembly | `letter_assembly` | Provisional / blocks real generation |

### Gaps / blockers

| ID | Severity | Description |
|----|----------|-------------|
| QA-GAP-1 | **warning** | `oracal_wrapped` cant shows profile material (EUR/ml) but not Oracal vinyl consumption for cant — task exists, material line does not |
| QA-WARN-1 | warning | No backing layer — Forex omitted correctly; production may need backing decision |
| QA-WARN-2 | warning | Multi-color face (L2/L3) — two face layers, roll split by color OK after fix |

**Missing backing verdict:** **WARNING** for volumetric letters — quote can proceed with warnings; production handoff flags partial alignment.

## Tests run

```
test_intake_v4_nesting_material_precision.py  → PASS (incl. new PBL-like tests)
test_intake_v4_material_breakdown.py          → PASS
test_intake_v4_task_generation_dry_run.py     → PASS
test_tpl_volumetric_operation_keys_alignment.py → 58 passed, 1 unrelated fixture ERROR (event loop)
```

## Quote continuation

After fix: material breakdown **truthful for quote estimate** on placement/roll footprint.  
Draft quote may proceed **with documented GAP-1** (cant Oracal material vs profile pricing).  
**No ExecutionPlan / tasks_json created.**

## No hardcode confirmation

- No filename/hash literals in fix
- Generic placement-footprint + roll-dedup logic

## Verdict

| Scope | Verdict |
|-------|---------|
| Root cause identified | **PASS** |
| 4.482 m² was bug | **YES — sheet stock proration bug (fixed)** |
| Fix scoped | **PASS** |
| Nesting preview diagnostic | **PASS MVP** |
| Quote continuation | **ALLOWED with warnings** (not BLOCKED) |
| **Build overall** | **PASS scoped** |

---

## Nesting preview / diagnostic view

### Implemented

Read-only `nesting_preview` block attached to `GET .../material-breakdown` response + collapsible UI panel in Review step.

| Layer | Location |
|-------|----------|
| API | `IntakeV4MaterialBreakdownResponse.nesting_preview` |
| Backend builder | `backend/services/intake_v4_nesting_preview_service.py` |
| UI | `IntakeV4NestingPreviewPanel` inside `IntakeV4MaterialBreakdownPanel` (Review step) |

### What it shows (IV4-46499080 / manual upload file)

**Sheet layouts (4 variants in nesting output):**

| configId | placed | usedSheetAreaSqm | eff | Status |
|----------|--------|------------------|-----|--------|
| sheet_3000x2000 | 11 | 6.0 m² | 13% | **ACTIVE for breakdown** |
| sheet_3000x1500 | 0 | 4.5 m² | 0% | alternative — not summed |
| sheet_4000x1500 | 0 | 6.0 m² | 0% | alternative — not summed |
| sheet_1300x900 | 0 | 1.17 m² | 0% | alternative — not summed |

**Before fix:** breakdown used 6.0 m² sheet stock proration → **4.482 m²** plexiglas (bug).  
**After fix:** breakdown uses **10 face part bboxes Σ = 0.5834 m²**; preview confirms partIds and excludes L1 artwork.

**Roll jobs:** marks 1000mm vs 1260mm alternatives; active = min area per face layer (L2, L3); L1 artwork excluded from face_vinyl trace.

**Part table (active sheet):** 11 rows with partId, sourceLayer, role, area m², material lines (`plexiglas_face` / excluded for L1).

**Visual canvas:** bounding-box MVP on active sheet only — not exact toolpath shapes.

### Preview answers for 4.482 m² bug

| # | Question | Preview answer |
|---|----------|----------------|
| 1 | Câte piese în plexiglas? | **10** (L2+L3 splits) |
| 2 | partIds? | `split_layer_x0020_2_*`, `split_layer_x0020_3_*` |
| 3 | Layere? | L2, L3 |
| 4 | Arie fiecare? | ~0.03–0.09 m² per split part |
| 5 | Sheet? | `sheet_3000x2000` (active) |
| 6 | Adună alternative? | **Nu** — alternative marcate explicit |
| 7 | Piese vs sheet stock? | **Before fix:** sheet stock; **after fix:** placement footprint |
| 8 | L1 în plexi? | **Nu** — role printed_artwork, excluded in trace |
| 9 | L2/L3 dublate? | **Nu** — 10 distinct partIds |
| 10 | Forex greșit? | **Nu** — no backing placements |

**Preview confirms root cause:** 4.482 m² came from multiplying full sheet area (6 m²) by face/total placement ratio — not from part geometry alone.

### Limitations

- Bounding boxes only (MVP), not path geometry
- Roll canvas not rendered (table only)
- Does not re-run nest2; reads persisted `svg_analysis_json.nesting`
- Read-only — does not change material totals

### Tests

```
test_intake_v4_nesting_preview.py → 3 passed
(+ material/nesting precision regression 29 total)
```

Recommend separate commit after owner review — backend nesting precision only, no CostEngine/Pricing Registry.
