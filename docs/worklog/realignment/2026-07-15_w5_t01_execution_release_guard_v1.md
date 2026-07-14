# W5-T01 — Execution owner-decision production release guard v1

**Date:** 2026-07-15  
**Task:** W5-T01 `EXECUTION_OWNER_DECISION_PRODUCTION_RELEASE_GUARD_V1`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Starting HEAD:** `4c2d9e1`  
**Verdict:** `W5_EXECUTION_RELEASE_GUARD_PASS_COMMITTED`

## Policy

`ORDER_AND_PLAN_ALLOWED_TASK_START_BLOCKED`

Production blockers: `INTERNAL_SABLON_FOREX_COST`, `INTERNAL_MONTAJ_RULE`, `INTERNAL_CONSUMABLES_RULE`  
Nonblocking: `INTERNAL_AMBALARE_RULE`, `OVERHEAD_ALLOCATION_PENDING`

## Implementation

- **Shared evaluator:** `execution_owner_decision_production_release_service.evaluate_production_release`
- **Task start hook:** `assert_task_startable` calls `assert_production_release_allowed` before readiness (override cannot bypass)
- **Frozen input:** `Order.snapshot_v2_json` → `owner_decisions_snapshot`
- **Operational resolution:** `orders.readiness_snapshot.owner_decision_resolutions_v1` with audit history
- **API:** `GET /api/v1/execution/orders/{id}/production-release-status`; `POST .../owner-decisions/{code}/resolve` (admin/manager)

## Bypass classification

| Path | Classification |
|------|----------------|
| `POST /execution/reality/start-task` | CANONICAL_GUARDED_PATH |
| `POST /operator/task-action` start | CANONICAL_GUARDED_PATH |
| `PATCH /employee-mobile/tasks/{id}/start` | CANONICAL_GUARDED_PATH |
| `POST /execution/plan-v2/from-order` | READ_ONLY_PATH (allowed) |
| Direct `ExecutionRealityService.start_task` in tests | DEAD_PATH (not HTTP) |

## Tests

```
tests/test_execution_owner_decision_production_release_guard.py — 19 passed
+ test_execution_plan_v2_persist.py + test_order_snapshot_v2_convert.py — 68 passed
Total focused: 87 passed / 0 failed / 0 skipped / 0 collection errors
```

## Runtime (`:8001`)

Gate fixture order `29991` (`ORD-W5T01-GATE`):

1. `production-release-status` → `RELEASE_BLOCKED_OWNER_DECISIONS`
2. `start-task` → 409 `production_release_blocked`
3. resolve `INTERNAL_SABLON_FOREX_COST` → `RELEASE_ALLOWED`
4. `start-task` → 200
5. `snapshot_v2_json` unchanged; resolution in `readiness_snapshot`

Evidence: `docs/qa/product-system-active-path-isolation-v1/w5_t01_runtime_gate_evidence.json`

## Temporary debt

| Item | Classification |
|------|----------------|
| Task-level scope mapping | KEEP_FOR_W5_T02 (order-level block used) |
| Rich owner-decision UI | KEEP_FOR_WAVE_6 |
| `load_order_quote_input` V2 gap | KEEP_FOR_W5_T02 |
| Ghost port 8000 | LEGACY_ISOLATED |
| Employee Mobile full UX | MOBILE_DEFERRED_BUT_MUST_BE_GUARDED (guard wired) |

## Next task

**W5-INT-02** — Post-implementation gate
