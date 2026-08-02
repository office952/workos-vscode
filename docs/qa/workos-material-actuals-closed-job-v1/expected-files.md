# F4 expected file list (publish-before-implement)

## Own (F4)

| Path | Ownership |
|---|---|
| `backend/alembic/versions/s62_material_actuals_closed_job_v1.py` | Additive movement linkage + indexes |
| `backend/models/stock_movements.py` | `reverses_movement_id` (+ keep F3 valuation fields) |
| `backend/services/material_actuals_service.py` | NEW — issue/return/scrap semantics + auth + idempotency |
| `backend/services/actual_cost_policy_runtime_service.py` | Material readiness in closure; actual_material_cost netting |
| `backend/services/profitability_actual_read_model_service.py` | Status/reason fields for material/closure completeness |
| `backend/routers/material_actuals.py` | NEW authorized write/read endpoints |
| `backend/tests/test_material_actuals_closed_job_v1.py` | NEW targeted suite + complete fixture |
| `docs/qa/workos-material-actuals-closed-job-v1/*` | Research + proof |
| `docs/worklog/realignment/2026-08-02_material_actuals_closed_job_v1.md` | Worklog |

## Read / integrate (do not broaden)

| Path | Note |
|---|---|
| `backend/services/inventory_deduction_service.py` | Existing CANONICAL consumption path; reuse valuation freeze |
| `backend/models/actual_cost_policy.py` | Closure ledger |
| `backend/routers/actual_cost_policy_runtime.py` | Existing close/reopen |

## Forbidden

- `backend/dev.db` mutation as proof
- Order `973019` fabrication
- Employee Mobile
- Pricing Registry live lookup at profitability read
- Commercial snapshot / ProductDefinition / ProductAggregate edits
- FIFO/LIFO invention

## Runtime identity

| Item | Value |
|---|---|
| Worktree | `C:\w\workos_material_actuals_closed_job_v1` |
| Branch | `feat/material-actuals-closed-job-v1` |
| DB | `backend/qa-dbs/f4-material-actuals.db` |
| Backend port | `8017` |
| Frontend port | `3037` (only if UI verification needed) |
