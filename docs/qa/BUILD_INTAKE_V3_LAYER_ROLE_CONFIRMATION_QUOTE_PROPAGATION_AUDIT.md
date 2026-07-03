# BUILD — INTAKE_V3_LAYER_ROLE_CONFIRMATION_QUOTE_PROPAGATION_AUDIT

## Purpose

Audit and implement layer role confirmation propagation between workspace, quote linkage snapshots, and order read context. Expose stale snapshot detection, effective source rules, and optional guarded technical refresh for draft/priced draft quotes.

## Context

- Branch: `local/integration-pr4-plus-svg-path`
- Parent HEAD: `1b02326` — operator layer role confirmation
- Policy closes open question: quote linkage refresh after workspace re-confirm

## Audit summary

| Question | Finding |
|----------|---------|
| Workspace write | `PUT .../layer-role-confirmation` → `payload_json.layer_role_confirmation_snapshot` |
| Quote snapshot copy | `build_quote_creation_snapshot_payload()` at draft quote create |
| `source_workspace_id` | `quote.notes.intake_v3_linkage_v1.source_workspace_id` |
| Live hydration | `hydrate_live_workspace_snapshot_sections()` in material breakdown loader (existing) |
| Stale detection | **New** — `intake_v3_layer_role_confirmation_propagation_service.py` compares pre-hydration quote sections vs live workspace |
| Timestamps | `confirmed_at` on layer role snapshot; geometry `generated_at` |
| Safe quote notes update | Refresh POST updates linkage sections only via `QuotesService.update(notes=...)` |

## Chosen policy

**Live hydration + explicit stale warnings** (not silent overwrite).

- **Effective source**: workspace live confirmation when `source_workspace_id` resolves and workspace has confirmation; else quote linkage snapshot.
- **Snapshot source**: quote linkage `snapshot.sections.layer_role_confirmation_snapshot` (frozen at quote create / last explicit refresh).
- **Stale rules**: role map diff OR workspace `confirmed_at` > quote snapshot `confirmed_at`.
- **Downstream**: material breakdown, path perimeter, geometry metrics, production readiness, task dry-run use effective source via shared `downstream_propagation_fields()` and emit warnings when stale.
- **Accepted/converted quotes**: refresh **blocked**; live effective hydration + stale warnings only.
- **Draft/priced draft** (`quote.status` in `draft`, `priced`, not accepted/converted): guarded POST refresh allowed.

## Refresh endpoint

`POST /api/v1/intake-v3/quotes/{quote_id}/layer-role-confirmation/refresh-technical-snapshot`

Updates only:

- `quote.notes.intake_v3_linkage_v1.snapshot.sections.layer_role_confirmation_snapshot`
- `...geometry_metrics_snapshot`

Does **not** modify quote status, totals, order, inventory, execution, CostEngine.

## Files changed

### Backend

- `backend/services/intake_v3_layer_role_confirmation_propagation_service.py` (new)
- `backend/services/intake_v3_material_quantity_breakdown_service.py` — `linkage_sections` on `Iv3SourceContext`
- `backend/services/intake_v3_geometry_path_perimeter_classification_service.py`
- `backend/services/intake_v3_geometry_metrics_snapshot_service.py`
- `backend/services/intake_v3_order_production_readiness_service.py`
- `backend/services/intake_v3_production_task_dry_run_service.py`
- `backend/services/intake_v3_layer_role_confirmation_service.py`
- `backend/services/intake_v3_workspace_service.py`
- `backend/schemas/intake_v3.py`
- `backend/routers/intake_v3_workspaces.py`
- `backend/tests/test_intake_v3_layer_role_confirmation_propagation.py` (new)

### Frontend

- `frontend/src/lib/intakeV3/layerRolePropagationContracts.ts` (new)
- `frontend/src/lib/intakeV3/api.ts`
- `frontend/src/components/workos/intake-v3/IntakeV3LayerRolePropagationPanel.tsx` (new)
- `frontend/src/components/workos/intake-v3/IntakeV3MaterialBreakdownPanel.tsx`
- `frontend/src/lib/intakeV3/flowState.ts`
- `frontend/src/pages/IntakeV3App.tsx`
- Tests: panel, flowState

## Commands + results

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_intake_v3_layer_role_confirmation_propagation.py tests/test_intake_v3_layer_role_confirmation.py tests/test_intake_v3_geometry_path_perimeter_classification.py tests/test_intake_v3_geometry_metrics_snapshot.py tests/test_intake_v3_material_quantity_breakdown.py tests/test_intake_v3_order_production_readiness.py tests/test_intake_v3_production_task_dry_run.py -q
# 94 passed, 1 skipped

cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/components/workos/intake-v3/IntakeV3LayerRolePropagationPanel.test.tsx src/components/workos/intake-v3/IntakeV3LayerRoleConfirmationPanel.test.tsx src/components/workos/intake-v3/IntakeV3PathPerimeterClassificationPanel.test.tsx src/pages/IntakeV3App.test.tsx src/lib/intakeV3/flowState.test.ts
# 174 passed
```

## Boundary

- No ExecutionPlan / ExecutionTask / WorkSession
- No Inventory / StockMovement
- No CostEngine
- No quote/order status mutation (except explicit refresh POST on `notes` only)
- No pricing/totals mutation on refresh
- No production start / task generation buttons in UI

## Open questions

- Should accepted quotes ever allow operator-initiated technical resnapshot with dual audit trail?
- IV3 audit log pattern for refresh events (no repo pattern yet — follow-up)

## Next build recommended

**IV3 production preview consolidation** — optional grouping of propagation + geometry + material panels under a single “Production Preview” accordion once operator UX is validated.
