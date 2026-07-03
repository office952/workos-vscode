# BUILD — INTAKE_V3_OPERATOR_LAYER_ROLE_CONFIRMATION

## Purpose

Allow the operator to confirm SVG layer→production role mapping so `confirmed_role` overrides auto-normalized synonyms with **high** confidence, feeding path perimeter classification, geometry snapshot, material breakdown, production readiness, and task dry-run — without Execution, Inventory, CostEngine, or commercial status side effects.

## Context

- Base commit: `9787398` — geometry path perimeter classification (auto layer role mapping, medium confidence)
- Branch: `local/integration-pr4-plus-svg-path`
- Boundary: workspace PUT persists snapshot + refreshes geometry snapshot only

## Audit — layer/path data

| # | Question | Finding |
|---|----------|---------|
| 1 | Where are SVG layers? | `workspace.payload.path_geometry_summary.layers` from `build_layer_path_geometry_from_svg_text` at upload |
| 2 | Layer fields | `layer_id`, `layer_name`, `perimeter_mm`, `area_mm2`, `closed_contour_count`, `path_count` |
| 3 | id/name/data-name? | `layer_id` from `<g id>`; `layer_name` optional |
| 4 | Per-layer metrics? | Yes — path-summed perimeter/area/contour count |
| 5 | Auto role normalization | `normalize_svg_layer_role()` in path perimeter classification service; reused by layer role confirmation draft |
| 6 | Geometry snapshot persistence | `workspace.payload.geometry_metrics_snapshot` rebuilt on save |
| 7 | Workspace payload | `intake_v3_workspaces.payload_json` JSON blob — no migration |
| 8 | Operator decision pattern | Owner decision / guarded accept patterns exist; layer roles follow workspace PUT snapshot pattern |
| 9 | Workspace update endpoints | Existing field editor + new PUT `/layer-role-confirmation` |
| 10 | Snapshot without migration | `payload.layer_role_confirmation_snapshot` |
| 11 | Classification consumer | `classify_geometry_path_perimeters(..., layer_role_confirmation=...)` |
| 12 | Confirmed priority | `confirmed_role` + `confirmation_state=confirmed` wins over auto synonym; `ignore` excluded |
| 13 | UI | New `IntakeV3LayerRoleConfirmationPanel` before Geometry Snapshot |
| 14 | Tests | `test_intake_v3_layer_role_confirmation.py` + panel/flow/app frontend tests |

## Schema — `layer_role_confirmation_v1`

Persisted at:

- `workspace.payload.layer_role_confirmation_snapshot`
- Quote linkage: `notes.intake_v3_linkage_v1.snapshot.sections.layer_role_confirmation_snapshot` (on draft quote creation)

Separate fields:

- `auto_role` / `auto_confidence` — system suggestion (medium when synonym matched)
- `confirmed_role` / `confirmed_confidence` — operator decision (high when confirmed)

Allowed roles: `face`, `backing`, `return`, `bevel`, `inner_hole`, `support_panel`, `frame`, `vinyl`, `drill`, `reference`, `ignore`, `unknown`.

## Confidence rules

| Source | Confidence |
|--------|------------|
| Operator confirmed production role | `high` on classified perimeter + layer entry |
| Auto synonym match | `medium` |
| Unknown / unconfirmed | excluded or unclassified |
| Ignore | excluded from perimeters; listed in `ignored_layers` |

## Integrations

| Consumer | Change |
|----------|--------|
| Path perimeter classification | `classification_source` includes `layer_role_confirmation_snapshot`; confirmed layers quality `high` |
| Geometry metrics snapshot | `layer_role_confirmation_status`, `source_keys` includes confirmation snapshot |
| Material breakdown | `operator_confirmed_layer_roles`, source prefix `operator_confirmed_layer_role+...` |
| Production readiness | `layer_role_confirmation_status`, confirmed/unconfirmed/ignored counts, perimeter confidence |
| Production task dry-run | Higher input quality when operator-confirmed; `layer_roles_unconfirmed` warning |

## Backend

- `backend/services/intake_v3_layer_role_confirmation_service.py`
- Schemas + router GET/PUT workspace, GET quote/order
- PUT side effect: merge snapshot → rebuild `geometry_metrics_snapshot` only

## Frontend

- `layerRoleConfirmationContracts.ts`, API fetchers, `IntakeV3LayerRoleConfirmationPanel`
- Flow step: **Layer Role Confirmation** between Finish Assignment path and Geometry Snapshot
- Status hooks in Path Perimeter / Geometry / Material / Readiness / Task Dry-Run panels

## Tests run

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_layer_role_confirmation.py tests/test_intake_v3_geometry_path_perimeter_classification.py tests/test_intake_v3_geometry_metrics_snapshot.py tests/test_intake_v3_material_quantity_breakdown.py tests/test_intake_v3_order_production_readiness.py tests/test_intake_v3_production_task_dry_run.py -q
# 82 passed, 1 skipped

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v3/IntakeV3LayerRoleConfirmationPanel.test.tsx src/components/workos/intake-v3/IntakeV3PathPerimeterClassificationPanel.test.tsx src/pages/IntakeV3App.test.tsx src/lib/intakeV3/flowState.test.ts
# 169 passed
```

## Boundary confirmation

- No ExecutionPlan / ExecutionTask / WorkSession
- No Inventory / StockMovement
- No CostEngine
- No Order/Quote status mutation from layer role PUT
- No operational cost, labor, markup, or production start buttons

## Open questions

- Audit log for operator role confirmations (no existing IV3 audit pattern)
- Partial save / per-layer autosave vs batch confirm
- Template-specific default role maps beyond synonym table

## Next build recommended

**INTAKE_V3_LAYER_ROLE_CONFIRMATION_QUOTE_PROPAGATION_AUDIT** — verify quote/order read paths after workspace confirm + re-quote snapshot refresh; optional operator re-confirm on quote review.

## Files changed (summary)

Backend: layer role confirmation service, schemas, router, integrations (classification, geometry, material, readiness, dry-run, quote creation snapshot), tests.

Frontend: contracts, api, panel, flowState, IntakeV3App, downstream panel hooks, tests.

Docs: this file + intake-v3 status/roadmap/decisions/readiness updates.
