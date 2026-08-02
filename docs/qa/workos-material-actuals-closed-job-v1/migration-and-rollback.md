# Migration and rollback

| Revision | `s62_material_actuals_closed_job_v1` |
|---|---|
| Parent | `s61_merge_heads_actual_cost_policy` |
| Change | Additive `stock_movements.reverses_movement_id` + index |
| Deploy | `alembic upgrade head` |
| Rollback | `alembic downgrade s61_merge_heads_actual_cost_policy` |

Isolated proof DB: `backend/qa-dbs/f4-material-actuals.db` (never `dev.db`).
