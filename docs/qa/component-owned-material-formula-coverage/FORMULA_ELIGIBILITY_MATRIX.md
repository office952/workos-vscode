# FORMULA_ELIGIBILITY_MATRIX

**Date:** 2026-08-02  
**Repo tip before code:** `c382f061` (pushed 0/0)  
**Rule:** no formula code before this matrix

---

## Candidate 1 — `return_wrap_area`

| Field | Evidence |
|-------|----------|
| formula key | `return_wrap_area` |
| material family | Return / cant Oracal wrap |
| material code(s) | `MAT-ORACAL-651` (linked_module volum aluminum; gate `return_finish_type=oracal_wrapped`) |
| technical role | Folie pe banda cantului (volum aluminiu) |
| owner component | `TPL-VOLUM-ALUMINIU_v1` / `comp_volum_aluminiu_module` (linked_module); ownership view in `volum_aluminiu_quantity_ownership.py` |
| input paths | `letter_perimeter_m` (or confirmed return perimeter bridge); `return_depth_mm` |
| input owner | Perimeter: return_cant / Product Truth confirmed perimeter with controlled quote_geometry bridge; Depth: finish_setup / return_cant `return_depth_mm` |
| variant conditions | Active only when `return_finish_type ∈ {oracal_wrapped, colantat, oracal}` (seed gate: `oracal_wrapped`); depth size selects profile materials separately |
| geometry semantics | Wrap band area = perimeter × band width; band width = depth + authorized extra trim |
| formula | Demonstrated in `shared_edge_cant_rules.build_edge_cant_oracal_651_material_row`: `area_m2 = quote_perimeter_m × (return_depth_mm + RETURN_VINYL_BAND_EXTRA_MM) / 1000` where `quote_perimeter_m = perimeter_m × (1 + EDGE_CANT_QUOTE_WASTE_PERCENT/100)` with `RETURN_VINYL_BAND_EXTRA_MM=10`, `EDGE_CANT_QUOTE_WASTE_PERCENT=20` |
| input units | perimeter: m (ml synonym); depth: mm |
| output unit | mp / m² (template unit `mp`) |
| conversion policy | mm → m via `/1000`; no SVG |
| rounding policy | `round(..., 4)` as in shared_edge_cant row builder |
| missing-input behavior | Missing perimeter or depth → `resolved=False`, quantity null (**no default depth 60** — unlike pricing helper which invents 60) |
| source/version | `shared_edge_cant_rules` + `RETURN_VINYL_BAND_EXTRA_MM` (`volumetric_face_vinyl_service`); registered as FormulaId `return_wrap_area` |
| freeze behavior | Evaluate at `apply_technical_material_requirements`; freeze into PA materials |
| legacy behavior | Pre-contract snapshots stay `legacy_unspecified` / null |
| **implementation verdict** | **IMPLEMENT_MODEL_A** |
| tests required | derived qty; missing depth/perimeter null; inactive finish absent; mutual exclusion vs paint; provenance intact |
| remaining gaps | Group-level wrap-only perimeter subset (when some groups wrapped, some not) not wired into freeze facts today — uses job-level `letter_perimeter_m` when finish is globally oracal_wrapped |

---

## Candidate 2 — `return_paint_consumption`

| Field | Evidence |
|-------|----------|
| formula key | `return_paint_consumption` |
| material family | Return / cant RAL spray tubes |
| material code(s) | `MAT-VOPSEA-RAL` (linked_module; gate `return_finish_type=ral_paint`); also appears on parent finish with different formula_id in some seeds |
| technical role | Consumabil vopsea spray tub (`buc`) |
| owner component | Intended: volum aluminum linked module; parent finish also lists paint (composition noise) |
| input paths | Seed requires `return_finish_type`, `return_depth_mm`; **no yield, layers, or tube-count path on this formula_id** |
| input owner | Finish type/depth owned; **paint yield / coats / ml-per-tube not owned for this formula** |
| variant conditions | Gate `ral_paint` (and aliases in ownership view) |
| geometry semantics | Surface could reuse wrap-band area conceptually, but **no authorized area→tubes conversion** |
| formula | **Not demonstrated** for `return_paint_consumption`. Separate path `ceil_quote_input_quantity` uses operator/estimate `paint_tube_count` / `estimated_paint_tubes` — different formula_id, not auto-derived from geometry |
| input units | tubes = buc; area would be m² if it existed |
| output unit | `buc` |
| conversion policy | **missing** |
| rounding policy | N/A until yield owned (ceil tubes exists only on other formula) |
| missing-input behavior | Keep null / source_missing |
| source/version | Seed formula_id only; ownership note defers to child formula without defining yield |
| freeze behavior | Emit row when gate matches; quantity null + `source_missing` |
| legacy behavior | unchanged |
| **implementation verdict** | **SOURCE_MISSING** (do **not** invent yield/layers/waste) |
| tests required | gate emits null source_missing; Oracal/Stock do not emit paint; no zero invent |
| remaining gaps | Owner must authorize paint yield (m²/tub or ml/tub), coats, and waste before Model A |

---

## Summary verdicts

| Formula | Verdict |
|---------|---------|
| `return_wrap_area` | **IMPLEMENT_MODEL_A** |
| `return_paint_consumption` | **SOURCE_MISSING** — keep null |
| Other formula-less | Model D `reference_only` (unchanged) |

**STOP condition:** not triggered — at least one formula (`return_wrap_area`) is demonstrably implementable.
