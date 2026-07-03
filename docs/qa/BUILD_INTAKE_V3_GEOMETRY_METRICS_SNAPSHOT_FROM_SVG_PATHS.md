# BUILD — INTAKE_V3_GEOMETRY_METRICS_SNAPSHOT_FROM_SVG_PATHS

## Purpose

Persist and expose a **technical geometry metrics snapshot** for Intake V3 (`geometry_metrics_snapshot_v1`) derived from confirmed production model, workspace dimensions, and optional SVG path analysis at upload time. Downstream consumers (Material Breakdown, Production Readiness, Production Task Dry-Run) read the snapshot instead of fragile live estimates where possible.

## Context

- Base commit: `1d326c0` — informative material quantity / geometry / material cost breakdown
- Chained with local build: Production Task Generation Dry-Run Contract (uncommitted at start)
- Scope: snapshot only — no ExecutionPlan, ExecutionTask, WorkSession, Inventory, CostEngine, or commercial status mutation

## Geometry source audit

| Question | Answer |
|----------|--------|
| Where is IV3 snapshot stored? | `quote.notes.intake_v3_linkage_v1.snapshot.sections.*`; workspace payload in `intake_v3_workspaces.payload_json` |
| Quote/order/workspace linkage? | `intake_v3_linkage_v1` on quote notes; order inherits via convert snapshot copy |
| Raw SVG analysis? | Stored on workspace at upload (`raw_svg_analysis`); SVG text not persisted long-term |
| Confirmed production model? | `confirmed_production_model` on workspace + `confirmed_production_model_snapshot` in quote sections |
| Already calculated but not persisted? | Path bbox/area at upload via `SvgMetricsService` → now `path_geometry_summary` on workspace |
| Estimate-only metrics? | Area from `width_mm × height_mm`; bounding box from client request or path summary |
| Missing completely? | Letter-classified cutting perimeters, return/cant perimeter, bevel perimeter (not invented) |
| Material Breakdown geometry use? | `extract_geometry_summary()` merges snapshot + legacy section keys |
| Task Dry-Run geometry use? | Reads snapshot for `geometry_partial` warnings and candidate task input quality |
| Duplication avoided? | Single builder `intake_v3_geometry_metrics_snapshot_service.py`; legacy flat dict via `snapshot_to_legacy_geometry_dict()` |

## Persistence

- **Workspace:** `payload.geometry_metrics_snapshot` after production model confirm; `payload.path_geometry_summary` at SVG upload
- **Quote linkage:** `snapshot.sections.geometry_metrics_snapshot` in `build_quote_creation_snapshot_payload`
- **Order:** inherited from quote linkage sections on convert (read via shared `load_iv3_source_context`)

## Snapshot schema (`geometry_metrics_snapshot_v1`)

Key fields:

- `counts`: `real_letter_count`, `cut_contour_count`, `inner_hole_count` (holes ≠ letters)
- `dimensions`: width/height/depth mm, `area_m2`, `bounding_box_source`
- `perimeters`: face/backing/return/bevel — **null when not derivable**
- `areas`: face/backing/estimated/vinyl with quality markers
- `operation_geometry`: per-operation availability/quality/basis
- `metric_source`, `confidence`, `geometry_status`, `warnings`, `source_keys`, `holes_not_letters`

## Rules (holes / letters / contours)

- Holes are **not** letters (`real_letter_count` separate from `cut_contour_count` and `inner_hole_count`)
- HUB-like fixture expectation: 18 / 27 / 9
- Perimeters are **not invented** — missing → null + `perimeter_missing` warning + `geometry_partial`
- Estimated areas marked via `metric_source` / `bounding_box_source` = `estimated` or `confirmed_dimensions`

## Real vs estimated vs missing

| Metric | Source | Quality |
|--------|--------|---------|
| Letter/contour/hole counts | Confirmed production model | high (operator-confirmed) |
| Dimensions / estimated area | Client request dimensions | estimated |
| Path area/bbox | SVG upload analysis (`path_geometry_summary`) | path-derived when present |
| Face/backing cutting perimeter | Not mapped from raw SVG totals | missing |
| Return/cant perimeter | No safe derivation | missing |
| Bevel perimeter | No safe derivation | missing |

## Backend service / endpoints

- **Service:** `backend/services/intake_v3_geometry_metrics_snapshot_service.py`
- **GET** (read-only):
  - `/api/v1/intake-v3/workspaces/{id}/geometry-metrics-snapshot`
  - `/api/v1/intake-v3/quotes/{id}/geometry-metrics-snapshot`
  - `/api/v1/intake-v3/orders/{id}/geometry-metrics-snapshot`
- **POST recompute:** not implemented (deferred — SVG text not stored; risk of silent rewrite)

### Triggers

- SVG upload → `path_geometry_summary`
- Production model confirm → build + persist workspace snapshot
- Draft quote creation → copy into linkage sections

## Integrations

### Material Breakdown

- Merges `geometry_metrics_snapshot` with injectable legacy section
- Sets `geometry_summary.geometry_snapshot_source`
- Reduces ambiguous `geometry_partial` when snapshot counts present

### Production Readiness

- `available_data.geometry_snapshot_available`, `geometry_status`
- Read-only audit — does not block real production automatically

### Production Task Dry-Run

- `geometry_snapshot_available`, `geometry_status` on response
- `geometry_partial` warning when snapshot incomplete
- `will_create_real_task=false` unchanged

## Frontend

- Contracts: `geometryMetricsContracts.ts`
- Panel: `IntakeV3GeometryMetricsPanel.tsx` (before Material Breakdown)
- Flow step: `geometry_snapshot` in `flowState.ts`
- Consumer panels show snapshot source / geometry status

## Boundary confirmation

- No ExecutionPlan / ExecutionTask / WorkSession creation
- No Inventory / StockMovement mutation
- No CostEngine usage
- No Order/Quote status mutation from geometry endpoints
- No operational cost / labor in Material Breakdown

## Tests run

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_geometry_metrics_snapshot.py tests/test_intake_v3_material_quantity_breakdown.py tests/test_intake_v3_order_production_readiness.py tests/test_intake_v3_production_task_dry_run.py -q
```

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/IntakeV3App.test.tsx src/lib/intakeV3/flowState.test.ts src/components/workos/intake-v3/IntakeV3GeometryMetricsPanel.test.tsx
```

IV3 regression subset: see build spec §21 (run before merge).

## Files changed (representative)

- `backend/services/intake_v3_geometry_metrics_snapshot_service.py` (new)
- `backend/tests/test_intake_v3_geometry_metrics_snapshot.py` (new)
- `backend/schemas/intake_v3.py`
- `backend/services/intake_v3_material_quantity_breakdown_service.py`
- `backend/services/intake_v3_order_production_readiness_service.py`
- `backend/services/intake_v3_production_task_dry_run_service.py`
- `backend/routers/intake_v3_workspaces.py`
- `frontend/src/components/workos/intake-v3/IntakeV3GeometryMetricsPanel.tsx` (new)
- `frontend/src/lib/intakeV3/geometryMetricsContracts.ts` (new)
- `frontend/src/lib/intakeV3/api.ts`, `contracts.ts`, `flowState.ts`
- `frontend/src/pages/IntakeV3App.tsx`

## Next build recommended

**INTAKE_V3_GEOMETRY_PATH_PERIMETER_CLASSIFICATION** — map SVG path layers/roles to face/backing cutting perimeters without inventing totals; optional guarded POST recompute when SVG re-upload pipeline stores path text or hash.
