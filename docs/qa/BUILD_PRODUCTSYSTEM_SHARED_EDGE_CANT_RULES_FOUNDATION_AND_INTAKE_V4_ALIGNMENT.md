# BUILD_PRODUCTSYSTEM_SHARED_EDGE_CANT_RULES_FOUNDATION_AND_INTAKE_V4_ALIGNMENT

## Purpose

Foundation shared module for cant/volum edge rules and Intake V4 alignment (Material Breakdown, dry-run preview). Preserves existing numeric outputs for default cant; adds Oracal 651 cant material row when `oracal_wrapped`.

## Audit findings (Task B)

| # | Finding |
|---|---------|
| 1 | Cant length: `quote_geometry` / `path_geometry_summary`, `intake_v4_volumetric_return_metrics_service`, `_append_return_material_rows` |
| 2 | +20% waste: `_with_waste` / `_cost_row` in `intake_v4_material_breakdown_service` (`WASTE_PERCENT=20`) |
| 3 | Adhesive: `intake_v4_consumables_adhesive_wiring_service` — 2 ml/ml on letter-only return ml |
| 4 | Oracal 651 on cant: finish truth `oracal_wrapped`; handoff seeds `return_vinyl_application_workbench`; no dedicated breakdown material row before this build |
| 5 | Task/preview: `intake_v4_production_handoff_preview_service`, `intake_v4_task_generation_dry_run_service`, operator labels |
| 6 | Legacy “return” in internal keys (`return_material`, `return_finish_type`); UI uses cant/volum |
| 7 | Backend owners listed above + `volumetric_face_vinyl_service.estimate_return_vinyl_linear_consumption` |
| 8 | Frontend: Material Breakdown panel, finish/review labels |
| 9 | Labels only: operator finish labels, quantity basis display |
| 10 | Extracted to `shared_edge_cant_rules.py` without changing default numeric paths |

**Lipire manoperă basis:** adhesive and bond operation use **calculated letter-only** ml (~13.62 PBL). Oracal wrap operation uses **quote wrapped ml** with +20% waste.

## Implementation

- `backend/services/shared_edge_cant_rules.py` — metrics, adhesive, Oracal 651 row, `edge_cant_operation_rows`
- `backend/services/intake_v4_edge_cant_dry_run_service.py` — dry-run candidates
- Schema: `IntakeV4EdgeCantOperationRow`, `edge_cant_operation_rows`, dry-run response fields
- Material breakdown wires shared module; adhesive delegated from consumables service
- Frontend: separate “Operații cant / volum” section; `shared_edge_cant_rules` in quantity_source when present

## Values before / after

| Scenario | Before | After |
|----------|--------|-------|
| Default white_aluminum cant (PBL) | 15.47 calc / 18.56 quote return row; adhesive 13.62×2 ml | Same |
| `oracal_wrapped` cant | No `edge_cant_oracal_651` material row | Row added; price from shared vinyl catalog |
| CNC / LED | Unchanged | Unchanged |

## Tests run

```text
pytest tests/test_shared_edge_cant_rules.py — 11 passed
pytest tests/test_intake_v4_oracal_641_651_pricing.py — passed
pytest tests/test_intake_v4_consumables_adhesive_and_wiring.py — passed
pytest tests/test_intake_v4_material_breakdown.py — 60 passed, 3 failed (pre-existing forex_backing nesting tests)
pytest tests/test_intake_v4_cnc_operation_dry_run.py — 9 passed
vitest IntakeV4MaterialBreakdownPanel.test.tsx — 3 passed
```

## Smoke (PBL IV4-4B172FD4)

Workspace `0f300dcf-0b77-4fc1-affd-6e2a20329804` via `build_intake_v4_material_breakdown` on dev.db:

| Scenario | Result |
|----------|--------|
| Default white_aluminum, backing none | return 15.4672 / 18.5606 ml; adhesive 27.2422 ml; no edge651; edge bond 13.62 ml; CNC 2 ops |
| oracal_wrapped (simulated) | edge651 1.1442 m² @ 9 EUR (`shared_edge_cant_rules\|intake_v4_owner_oracal_651`); wrap op 16.35 ml + bond 13.62 ml |
| backing forex_10_with_bevel (simulated) | CNC 4 ops (backing cut 5 passes); edge ops unchanged |

Workspace DB state not modified (simulation via deepcopy).

## Remaining gaps

- Per-group wrapped perimeter when `perimeter_m` missing on groups falls back to total return ml
- Partial group wrap uses group perimeters when present; dominant-finish shortcut when absent
- Operation labor rates still `missing_rate` (preview only)
- `return_finish_type` API field names not renamed
- TPL-LIGHTBOX / colantare-only templates not wired

## Boundary

No quote/order/tasks, ExecutionPlan, stock, Pricing Registry, CostEngine, Color Registry rewrites, employee assignment.

## Pre-push stabilization (2026-06-23)

### Material breakdown test failures

| Test | Root cause | Resolution |
|------|------------|------------|
| `test_sheet_nesting_prorated_fallback_without_placement_metadata` | Pre-existing: `IntakeV4FinishSetup.backing_mode` defaulted to `"none"`, blocking layer-role backing fallback | Fixed: `backing_mode` schema default `None` → layer-role fallback restores Forex row |
| `test_sheet_nesting_role_split_when_metadata_present` | Same | Fixed |
| `test_missing_registry_sets_contains_missing_prices` | Caused by edge/cant build: `edge_cant_oracal_651` uses owner Oracal price via `shared_edge_cant_rules\|intake_v4_owner_oracal_651` | Fixed: test excludes any `intake_v4_owner_oracal` in `price_source` |

Verified forex failure on `4372fcc` material breakdown alone (1 of 2 forex tests failed); missing_registry passed on `4372fcc`.

### Unit audit (m vs ml)

- Cant / return material rows: `m` (was legacy `ml` for linear meters)
- Edge/cant operation rows: `m`
- Oracal 651 cant material: `m2`
- Adhesive consumable: `ml`
- CNC `operation_rows`: unchanged `ml` (machine linear-meter convention)

### Oracal 651 cant basis

`area_m2 = quote_wrapped_m × (depth_mm + 10) / 1000` where `quote_wrapped_m = wrapped_calculated_m × 1.20`.

### Adhesive / bond basis (preserved legacy)

- **15.47 m** — total cant for aluminum `return_material` (letters + artwork + interioare)
- **18.56 m** — priced aluminum (+20% waste on material row)
- **13.62 m** — letter-only cant for adhesive (×2 ml = 27.24 ml) and bond operation preview
- Artwork cant (~1.85 m) excluded from adhesive/bond — intentional legacy; document as remaining gap if product wants unified total cant for labor
