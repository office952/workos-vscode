# BUILD_INTAKE_V4_CNC_ROUTER_PASSES_AND_BEVEL_COSTING_AUDIT

## Branch / HEAD

| Field | Value |
|-------|-------|
| Branch | `local/integration-pr4-plus-svg-path` |
| HEAD before | `db458d1` — fix(intake-v4): classify real letters and return contours |
| Build | `BUILD_INTAKE_V4_CNC_ROUTER_PASSES_AND_BEVEL_COSTING_AUDIT` |
| Commit | **Not committed** — awaiting owner confirmation |

## Purpose

Audit CNC router passes, șanfren/bevel, perimeter separation (LED vs CNC vs cant), and CostEngine alignment for **TPL-VOLUMETRIC-LETTERS** on real workspace **IV4-46499080** (`pbl-layere.svg`).

---

## QA-BUG summary

| Issue | Before | After (this build) |
|-------|--------|-------------------|
| CostEngine CNC ops used `letter_perimeter_m` (LED outer only) | 11.6299 ml | **`cnc_cutting_perimeter_ml` = 12.725 ml** via template `perimeter_quote_input_key` |
| `cnc_cutting_perimeter_ml` missing from quote_input | absent | **patched** in Intake V4 pricing adapter |
| `bevel_perimeter_ml` missing (dry-run warnings) | 0 / missing | **= cnc_cutting perimeter** when holes included |
| `back_bevel_enabled` missing in V4 quote_input | absent | **default `false`** (matches V2/QuoteWizard policy) |
| Pass depth rule for Forex 10 mm | template-fixed 3+2 | **documented + tested** in `intake_v4_cnc_router_pass_policy_service.py` |

**Not fixed in this build (documented gaps):**

**Known blocker next build:**
CostEngine still runs `back_cut` even when backing is absent in Intake V4.
Example IV4-46499080: back_cut phantom = **57.26 EUR**.
This build does not fix that gate.

**Quote final must not proceed until `back_cut` is gated by backing presence.**

- `back_cut` CostEngine operation still runs when **no backing layer** (57.26 EUR phantom on IV4-46499080) — needs conditional gating build.
- Intake V4 UI has **no** face/back bevel toggles, backing selector, or CNC cost preview panel.
- Live DB template JSON may need **re-seed** to pick up `perimeter_quote_input_key` on deployed environments (tests use seed components directly).

---

## Documented rules found

| Source | Rule | Runtime? |
|--------|------|----------|
| `backend/seeds/seed_build4_templates.py` — `face_cnc_cut` | CNC_ROUTER, `pass_count=2` (1 cut + 1 bevel), plexiglas face 3 mm | **Yes** (after perimeter key fix) |
| `backend/seeds/seed_build4_templates.py` — `back_cut` | `base_pass_count=3`, `bevel_pass_count=2`, gated by `back_bevel_enabled` | **Yes** (always runs; backing gate missing) |
| `backend/services/formula_handlers.py` — `_handle_perimeter_pass_linear_meter` | `total_ml = letter_perimeter × pass_count`; supports `perimeter_quote_input_key` | **Yes** |
| `docs/architecture/TPL_VOLUMETRIC_LETTERS_INPUT_CONTRACT_AUDIT.md` §4 | CNC 1.5 EUR/ml/pass; face 2 passes; back 3 vs 5 passes | **Yes** (rates via workcenter registry) |
| `backend/tests/test_volumetric_operation_unit_pricing.py` | 18 m × 2 × 1.5 = 54 EUR face; 18 m × 3 × 1.5 = 81 EUR back | **Yes** (regression baseline) |
| Owner rule (this audit) | Forex 10 mm: `ceil(depth/3.5)` cut passes; bevel 7 mm → 2 passes | **Policy service + tests**; template uses **fixed** 3+2 (matches owner math) |
| `frontend/.../V2ProductionStage.tsx` | `back_bevel_enabled` checkbox for Forex 10 mm | **V2 only** — not Intake V4 |
| `docs/architecture/TPL_VOLUMETRIC_LETTERS_INPUT_CONTRACT_AUDIT.md` §C | `face_bevel_enabled` default **true** (implicit); `back_bevel_enabled` default **false** | Face: implicit 2-pass template; back: **false** in V4 patch |

### Rules missing or incomplete

| Rule | Status |
|------|--------|
| `face_bevel_enabled` explicit quote_input / V4 UI | **Missing** — face always 2-pass in template |
| Depth-driven pass calculation at CostEngine runtime | **Missing** — passes are **template constants** (3+2), not computed from 3.5 mm in engine |
| `back_cut` skip when no backing layer | **Missing** — operation always priced |
| Intake V4 backing Forex 10 mm selector | **Missing** — layer role `backing` absent on pbl-layere |
| CNC cost preview in Intake V4 UI | **Missing** — next build MVP |
| Inner holes on face bevel — explicit owner decision | **Decision needed** — CNC perimeter **includes holes** (same as cutting) |

---

## Mandatory Q&A

| # | Question | Answer |
|---|----------|--------|
| 1 | Perimetru debitare CNC față? | **`cnc_cutting_perimeter_ml`** (via `perimeter_quote_input_key` on `face_cnc_cut`) |
| 2 | Include goluri/interioare? | **Da** — 12.725 ml = outer 11.6299 + holes 1.0951 |
| 3 | Perimetru șanfren față? | **Același contur CNC** (`bevel_perimeter_ml` = `cnc_cutting_perimeter_ml`); 1 pass bevel separat în template |
| 4 | Șanfren față = trecere separată? | **Da** — template `cut_passes=1`, `bevel_passes=1`, total 2 |
| 5 | Cost CNC = 1.5 EUR/ml/trecere? | **Da** — workcenter `CNC_ROUTER` `rate_per_linear_meter=1.5` (excl. TVA) |
| 6 | Față plexi 3 mm — șanfren implicit? | **Da (implicit)** — template fixed 2 passes; no `face_bevel_enabled` toggle in V4 |
| 7 | Backing Forex 10 mm selectabil în V4? | **Nu** — no backing layer on IV4-46499080; no V4 form field |
| 8 | Backing cu/fără șanfren? | **V2/QuoteWizard only** (`back_bevel_enabled`); V4 defaults **false** |
| 9 | Backing absent — inventează Forex? | **Material breakdown: absent ✓**; **CostEngine `back_cut` still priced ✗** (gap) |
| 10 | Ce e `led_perimeter_ml`? | Outer face letters only; policy `outer_face_letters_excludes_holes_and_artwork` |
| 11 | LED separat de CNC? | **Da** — 11.6299 vs 12.725 ml |
| 12 | Return/cant separat de CNC? | **Da** — 14.5711 ml (outer + holes + artwork return) |
| 13 | Pricing input / CostEngine folosește treceri? | **Da** — `perimeter_pass_linear_meter` × pass_count × rate; V4 now supplies `cnc_cutting_perimeter_ml` |
| 14 | QuoteWizard / V2 avea logica? | **Da** — `back_bevel_enabled` in V2 Production stage + template `bevel_quote_input_key` |

---

## Perimeter definitions (runtime IV4-46499080)

| Metric | Value (ml) | Use |
|--------|------------|-----|
| `led_perimeter_ml` | **11.6299** | LED modules, PSU pitch |
| `cnc_cutting_perimeter_ml` | **12.725** | CNC face + back cut formulas (outer + inner holes) |
| `face_cutting_perimeter_ml` | **13.1322** | Total contour from parts (includes fragment overhead) — **not** used for CNC after fix |
| `bevel_perimeter_ml` | **12.725** | Dry-run / task inputs (aligned to CNC cutting scope) |
| `return_material_perimeter_ml` | **14.5711** | Cant aluminiu — separate from CNC |

---

## Numeric CNC verification (IV4-46499080)

Perimeter **`cnc_cutting_perimeter_ml = 12.725`**, rate **1.5 EUR/ml/pass** (excl. TVA):

| Scenario | Passes | Formula | Cost EUR |
|----------|--------|---------|----------|
| Face plexi 3 mm **cu** șanfren (template default) | 2 | 12.725 × 2 × 1.5 | **38.175** |
| Face plexi 3 mm **fără** șanfren (hypothetical) | 1 | 12.725 × 1 × 1.5 | **19.0875** |
| Forex 10 mm **fără** șanfren (if backing active) | 3 | 12.725 × 3 × 1.5 | **57.2625** |
| Forex 10 mm **cu** șanfren 7 mm (if backing active) | 5 | 12.725 × 5 × 1.5 | **95.4375** |

**CostEngine after fix (seed components, IV4 quote_input):**

| Operation | linear_m | line_total EUR | Notes |
|-----------|----------|----------------|-------|
| `face_cnc_cut` | 25.45 | **38.17** | ✓ 12.725 × 2 |
| `back_cut` | 38.175 | **57.26** | ⚠ runs despite **no backing** on workspace |

**Before fix:** `face_cnc_cut` used `letter_perimeter_m` 11.6299 → 11.6299 × 2 × 1.5 = **34.89 EUR** (under-counted holes).

---

## Owner rule — Forex 10 mm depth / 3.5 mm

```txt
max_depth_per_pass_mm = 3.5
cut_passes = ceil(10 / 3.5) = 3
bevel_passes (7 mm) = ceil(7 / 3.5) = 2
total with bevel = 5
```

Implemented in `intake_v4_cnc_router_pass_policy_service.py` for audit/preview; template uses equivalent **fixed** counts (3 + 2).

---

## Material breakdown vs Pricing / CostEngine

| Layer | Contents |
|-------|----------|
| **Material Breakdown (Intake V4)** | **Materials + consumables only** (plexi m², cant ml, LED, PSU) — **no CNC operation EUR lines** |
| **Pricing input / CostEngine** | **Operations + materials** — CNC via `face_cnc_cut`, `back_cut` on `CNC_ROUTER` linear-meter basis |

---

## UI gaps (Intake V4 Review)

| Control | Present? |
|---------|----------|
| Face plexi thickness / material | Partial (implicit 3 mm template) |
| Face șanfren da/nu | **No** |
| Face CNC passes / cost preview | **No** |
| Backing Forex active | **No** (layer role driven; absent on pbl-layere) |
| Back șanfren da/nu | **No** (V2 has checkbox) |
| Back CNC passes / cost | **No** |

**MVP next build:** read-only CNC estimate panel using `build_cnc_operation_estimate_preview()` + optional `back_bevel_enabled` when backing layer confirmed.

---

## Files changed (uncommitted)

| File | Change |
|------|--------|
| `backend/services/intake_v4_cnc_router_pass_policy_service.py` | **New** — pass policy + cost preview |
| `backend/services/intake_v4_pricing_input_service.py` | Patch `cnc_cutting_perimeter_ml`, `bevel_perimeter_ml`, `back_bevel_enabled` |
| `backend/services/intake_v4_finish_adapter.py` | Path geometry bevel/CNC fields for dry-run |
| `backend/seeds/seed_build4_templates.py` | CNC ops use `cnc_cutting_perimeter_ml` key |
| `backend/tests/test_intake_v4_cnc_router_passes_and_bevel_costing.py` | **New** — 14 tests |
| `backend/tests/test_volumetric_operation_unit_pricing.py` | Add `cnc_cutting_perimeter_ml` to fixture |
| `docs/qa/BUILD_INTAKE_V4_CNC_ROUTER_PASSES_AND_BEVEL_COSTING_AUDIT.md` | This doc |

**Boundary:** No ExecutionPlan, tasks_json, real tasks, stock, Pricing Registry rate edits, CostEngine formula handler changes.

---

## Commands + results

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_cnc_router_passes_and_bevel_costing.py -q
# 14 passed

.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_quote_geometry.py -q
# passed

.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_pricing_input.py -q
# passed

.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_task_generation_dry_run.py -q
# passed

.\.venv\Scripts\python.exe -m pytest tests/test_volumetric_operation_unit_pricing.py -q
# 3 failed (painting + integration — return_painting gate / registry env; CNC face/back tests PASS)
```

---

## Verdict

| Gate | Status |
|------|--------|
| Perimeter separation LED/CNC/cant documented | **PASS** |
| CNC face uses outer+holes perimeter | **PASS** (after fix) |
| Pass policy matches owner Forex 3.5 mm rule | **PASS** (policy service + template constants) |
| V4 quote_input supplies CNC fields | **PASS** |
| Missing backing suppresses all Forex cost | **PARTIAL** — material absent; **CostEngine back_cut still runs** (known blocker — next build) |
| V4 UI for bevel/backing/CNC | **FAIL** — next build |
| ExecutionPlan / tasks_json | **PASS** — not touched |

**Recommend commit** for perimeter key + quote_input patch + policy service; **separate build** for back_cut conditional gating + V4 CNC UI.

---

## Next builds

1. **BUILD_INTAKE_V4_BACKING_AND_BEVEL_FORM_FIELDS** — wire `back_bevel_enabled`, backing layer confirm, face bevel toggle.
2. **BUILD_TPL_VOLUMETRIC_BACK_CUT_CONDITIONAL_GATE** — skip `back_cut` when no backing role/material.
3. **BUILD_INTAKE_V4_CNC_COST_PREVIEW_PANEL** — show passes × perimeter × 1.5 EUR read-only on Review.
