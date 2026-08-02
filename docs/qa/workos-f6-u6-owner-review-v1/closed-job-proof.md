# Closed-job proof — C3

Guards live in `backend/services/closed_job_mutation_guard.py` and are called from mutation owners:

- `material_actuals_service.py` (issue / return / scrap)
- `inventory_deduction_service.py`
- `inventory_stock_adjustment_service.py` (order-linked reversal)

Close/reopen API: `backend/routers/actual_cost_policy_runtime.py` with `execution.job_close` (admin/manager). Reopen requires reason (`reopen_reason_required`).

## Reproved via targeted tests (F5/F6)

| Scenario | Result |
|----------|--------|
| closed consumption → rejected | PASS |
| closed scrap → rejected | PASS (F5 + F6) |
| closed return → rejected | PASS (material actuals suite) |
| cross-job isolation | PASS (F6 three families) |
| unauthorized reopen | fail-closed via permission |
| reopen without reason → rejected | PASS (runtime service) |
| authorized reopen with reason → allowed | PASS |
| final result while reopened → unavailable | PASS (F6) |
| correction after reopen → controlled | PASS |
| reclose → allowed | PASS |
| new frozen result → consistent | PASS |
