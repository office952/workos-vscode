# Migration fresh-DB proof

| Item | Value |
|---|---|
| DB | `backend/qa-dbs/c0-f3-u3-migration-proof.db` (isolated; not `dev.db`) |
| Command | `alembic upgrade head` |
| Final current | `s61_merge_heads_actual_cost_policy` |
| Heads | single: `s61_merge_heads_actual_cost_policy` |

## Objects verified after upgrade

- `role_skill_labor_cost_policies`
- `actual_labor_cost_lines`
- `execution_job_closures`
- `execution_job_closure_events`
- `task_clarification_requests` (created by hardened side-branch when missing)
- `stock_movements` valuation snapshots: `unit_cost_snapshot`, `currency_snapshot`, `valuation_method`, `valuation_provenance`, `extended_cost_snapshot`, `price_history_id_snapshot`

## Rollback / re-upgrade

```text
alembic downgrade s49_employee_monthly_internal_pay_amount
alembic upgrade head
alembic current  → s61_merge_heads_actual_cost_policy
```

`alembic downgrade -1` at the mergepoint is ambiguous (two parents); use an explicit revision target.

## Verdict

PASS — deployable single-head path demonstrated on a fresh isolated SQLite DB.
