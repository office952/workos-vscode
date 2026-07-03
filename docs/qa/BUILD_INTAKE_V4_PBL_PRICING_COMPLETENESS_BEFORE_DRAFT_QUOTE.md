# BUILD_INTAKE_V4_PBL_PRICING_COMPLETENESS_BEFORE_DRAFT_QUOTE

## Purpose

Close Intake V4 **pricing/material preview** consistency for PBL (`pbl-layere.svg`) **before** any draft-quote policy change. No quote creation, no production tasks, no stock consumption.

## Context

- Analyzer child-parts fix landed at **`f453b92`** (`fix(intake-v4): preserve child parts on fresh SVG analysis`).
- Runtime smoke on fresh upload (`IV4-F29F5ED4` / `e3aeacfd-7542-456a-bcb7-6a4a7512fc90`) **PASS** for analyzer path:
  - `parts.items = 11`, `real_letters_count = 10`, `inner_hole_count = 2`
  - Plexiglas face ≈ **0.5834 m²** (nesting active, no 6.0 m² full-sheet fallback)
  - LED modules = **47**

## Deviations investigated (pre-fix)

| # | Symptom | Root cause |
|---|---------|------------|
| 1 | `quote_geometry.artwork_piece_count` / `volumetric_piece_count` = **null** in workspace payload | Counters are produced by `enrich_quote_geometry_with_volumetric_return()` inside `resolve_v4_quote_geometry()`, but **only persisted** at analysis-bundle time via `build_quote_geometry_from_analysis()` (no finish enrich). Finish-setup save did not re-persist enriched geometry. |
| 2 | Return/cant **14.5534 ml** vs checklist **14.5711 ml** (Δ 0.0177 ml) | Not an enrich/aggregation bug. **14.5711** comes from frozen golden analysis JSON fixture; **14.5534** is canonical for the **fresh desktop upload** after the shapeBounds child-part fix (outer letter perimeter −0.016 ml, inner hole −0.0017 ml; artwork return identical 1.8461 ml). |
| 3 | PSU missing from material breakdown | `led_psu` row requires `finish_setup.psu_configuration`. Smoke finish had `illuminated=true` but no auto lighting sync on save — only LED modules were estimated from geometry in breakdown (250 mm pitch). |

## Fixes applied

1. **`intake_v4_pricing_preview_sync_service.py`**
   - `apply_v4_pricing_preview_derived_state()` — persists canonical `quote_geometry` + merged `path_geometry_summary`.
   - `sync_intake_v4_finish_lighting()` — auto-derives `estimated_led_watts`, `required_psu_watts`, `psu_configuration` (via `propose_psu_units`, 30% reserve) when operator has not set PSU; preserves operator PSU when present.

2. **`intake_v4_workspace_service.py`** — call sync after:
   - `save_finish_setup`
   - `save_analysis_bundle` (when SVG not replaced)
   - `save_layer_roles` (when finish already present)

## Before / after (runtime smoke workspace)

| Signal | Before | After fix |
|--------|--------|-----------|
| `quote_geometry.artwork_piece_count` | null | **1** |
| `quote_geometry.volumetric_piece_count` | null | **11** |
| `quote_geometry.return_material_perimeter_ml` | 11.6139 (stale pre-enrich) | **14.5534** (fresh analysis canonical) |
| `finish_setup.psu_configuration` | `[]` | **`[100]`** (auto for 47 modules @ 1.44 W, 30% reserve) |
| Material breakdown PSU row | absent | **`led_psu` × 1** |
| Material breakdown LED | 47 modules | **47 modules** (unchanged) |
| Plexiglas face | 0.5834 m² | **0.5834 m²** (unchanged) |

### Perimeter note

- **`volumetric_piece_count`** = `real_letters_count` + artwork pieces with **active return** (official definition in `enrich_quote_geometry_with_volumetric_return`).
- Golden checklist **14.5711 ml** remains valid for the **golden analysis fixture**; fresh desktop file is **14.5534 ml** after analyzer fix — do not mask with tolerance.

### PSU note

- Golden workspace `IV4-46499080` had operator-style **`psu_configuration: [200, 60]`** sized for **226.87 W** (legacy higher-watt path).
- Auto preview for **47 modules** → **67.68 W** estimated → **87.98 W** with reserve → **`propose_psu_units` → [100] (1 PSU)**.
- Operator PSU arrays are **not overwritten** when already set.

## Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v4_pbl_pricing_completeness.py tests/test_intake_v4_pbl_child_parts_analyze_regression.py -q
```

**Result:** 17 passed.

## Files changed

- `backend/services/intake_v4_pricing_preview_sync_service.py` (new)
- `backend/services/intake_v4_workspace_service.py`
- `backend/tests/test_intake_v4_pbl_pricing_completeness.py` (new)
- `docs/qa/BUILD_INTAKE_V4_PBL_PRICING_COMPLETENESS_BEFORE_DRAFT_QUOTE.md`

## Boundary (unchanged)

- **No quote policy change** — L1 `needs_decision` still blocks draft quote (`422 artwork_execution_undecided`).
- **No quote / order / real tasks / ExecutionPlan / tasks_json / stock consumption**.
- **No CostEngine or Pricing Registry changes**.
- **No push** (owner request).

## Remaining blockers

1. Quote policy: artwork `needs_decision` → draft quote still blocked (separate build).
2. Production handoff / task dry-run only — out of scope.
3. Optional UX: operator may override PSU; auto `[100]` is preview estimate, not golden `[200, 60]` legacy sizing.

## Commands run

- Pre-flight git verification
- `pytest tests/test_intake_v4_pbl_pricing_completeness.py tests/test_intake_v4_pbl_child_parts_analyze_regression.py -q`
- Runtime DB sync verification on `e3aeacfd-7542-456a-bcb7-6a4a7512fc90`
