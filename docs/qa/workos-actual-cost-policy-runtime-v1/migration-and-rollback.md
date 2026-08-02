# Migration and rollback

Migration `s60_actual_cost_policy_runtime_v1` uses inspect-before-add and batch alter for StockMovement fields. It is applied only to `backend/qa-dbs/f3-actual-cost.db`; downgrade removes only these additive objects.

