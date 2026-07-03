# BUILD — INTAKE_V3_GEOMETRY_PATH_PERIMETER_CLASSIFICATION

## Purpose

Classify SVG path/layer geometry into production-role perimeters (face, backing, return/cant, bevel) **only when safely attributable**, persist results in `geometry_metrics_snapshot.path_perimeter_classification`, and feed Material Breakdown, Production Task Dry-Run, and Production Readiness — without Execution, Inventory, or CostEngine side effects.

## Context

- Base commit: `4751c88` — geometry metrics snapshot from SVG/confirmed model paths
- Branch: `local/integration-pr4-plus-svg-path`
- Boundary: read-only GET endpoints + snapshot merge; no production start, no task creation, no cost mutation

## Audit — path_geometry_summary / SvgMetricsService

| Topic | Finding |
|-------|---------|
| Aggregate metrics | `SvgMetricsService.parse_svg_metrics` → bbox, approximate area/perimeter at upload |
| Layer breakdown | **New:** `build_layer_path_geometry_from_svg_text` groups closed paths by nearest `<g id>` |
| Per-path length | `parse_path_metrics()` summed per layer → `perimeter_mm` |
| Per-layer bbox/area | Layer `area_mm2` when closed path area available |
| Layer id / name | `layer_id` from group `id`; optional `data-name` |
| Role mapping | **New:** `normalize_svg_layer_role()` — synonym map (LITERE→face, SPATE→backing, GOLURI→inner_hole, CANT→return, etc.) |
| Confirmed model mapping | Counts only (18/27/9); no perimeter fields on model |
| Safe classification today | Face/backing/return/bevel when layer id/name matches known roles **and** layer has path perimeter |
| Not classifiable without upload | Role attribution without SVG layer groups; inner/outer split without hole layers |
| Snapshot builder | `classify_geometry_path_perimeters` + `merge_classification_into_geometry_snapshot` in geometry snapshot build |

## Classification rules

- **Face:** layer role face/letters/LITERE with path perimeter — not bbox, not letter count alone
- **Backing:** explicit backing/SPATE/FOREX layer only — never derived from face
- **Return/cant:** explicit return/CANT layer only — never derived from face total
- **Bevel:** explicit bevel/SANFREN layer only — never assumed equal to face
- **Holes:** `inner_hole` role; contribute to contour split, not letter count
- **Quality:** `complete` / `partial` / `missing` / `unsupported`; warnings per missing role

## Schema — `path_perimeter_classification_v1`

Nested under `geometry_metrics_snapshot.path_perimeter_classification` with classified perimeter entries (`value`, `unit`, `quality`, `source`, `basis`), `classified_layers`, `unclassified_layers`, `contour_split`, `warnings`.

Root snapshot `perimeters.*_ml` updated only when classification quality is `high` or `medium`.

## Backend

- `backend/services/intake_v3_svg_layer_path_geometry.py` — layer path metrics at upload
- `backend/services/intake_v3_geometry_path_perimeter_classification_service.py` — classification + GET response builder
- Extended `intake_v3_geometry_metrics_snapshot_service.py` — layer merge + classification merge
- GET endpoints:
  - `/api/v1/intake-v3/workspaces/{id}/geometry-path-perimeter-classification`
  - `/api/v1/intake-v3/quotes/{id}/geometry-path-perimeter-classification`
  - `/api/v1/intake-v3/orders/{id}/geometry-path-perimeter-classification`

## Integrations

| Consumer | Change |
|----------|--------|
| Material Breakdown | Reads classified face perimeter; exposes `perimeter_classification_status` / source |
| Production Task Dry-Run | Face/return/bevel inputs + specific warnings (`face_perimeter_missing`, etc.) |
| Production Readiness | `available_data.perimeter_classification_status` + per-role availability flags |

## Frontend

- `IntakeV3PathPerimeterClassificationPanel` + contracts + API fetchers
- Flow step: **Perimeter Classification** between Geometry Snapshot and Material Breakdown
- Minimal status hooks in Geometry / Material / Task Dry-Run / Readiness panels

## Tests run

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_geometry_path_perimeter_classification.py tests/test_intake_v3_geometry_metrics_snapshot.py tests/test_intake_v3_material_quantity_breakdown.py tests/test_intake_v3_order_production_readiness.py tests/test_intake_v3_production_task_dry_run.py -q
# 68 passed, 1 skipped

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v3/IntakeV3PathPerimeterClassificationPanel.test.tsx src/lib/intakeV3/flowState.test.ts
# 28 passed
```

## Boundary confirmation

- No ExecutionPlan / ExecutionTask / WorkSession
- No Inventory / StockMovement
- No CostEngine
- No Order/Quote status mutation
- No operational cost or labor introduction

## Open questions

- User-confirmed layer→role mapping UI (currently name/id synonym only → medium confidence)
- Persisting raw SVG for recomputation without re-upload
- Template-specific role maps beyond volumetric letters pilot

## Next build recommended

**INTAKE_V3_OPERATOR_LAYER_ROLE_CONFIRMATION** — allow operator to confirm layer roles at upload/review for high-confidence perimeter classification without relying on layer naming alone.

## Files changed (summary)

Backend: classification service, layer geometry helper, geometry snapshot, material breakdown, dry-run, readiness, schemas, router, workspace wrappers, tests.

Frontend: panel, contracts, api, flowState, IntakeV3App, panel integrations, tests.

Docs: this file + intake-v3 status/roadmap/decisions/readiness updates.
