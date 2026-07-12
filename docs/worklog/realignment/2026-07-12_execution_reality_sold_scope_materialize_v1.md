# ExecutionReality sold scope materialize V1

**Date:** 2026-07-12  
**Task:** EXECUTION_REALITY_SOLD_SCOPE_MATERIALIZE_V1  
**HEAD before:** 57407be

## Change

Confirmed V2 materialization already consumes filtered `planned_tasks[]` from persisted `execution_plan.tasks_json` — no aggregate/resolver rerun. Tightened guards and identity passthrough on operational task rows.

## Path

`OrderSnapshotV2` → filtered preview → persist `planned_tasks[]` → `materialize_execution_plan_v2_operational_tasks()` → `operational_tasks[]` in plan envelope.

## Guards added

- Reject materialize when `preview_status` starts with `blocked_`
- Reject when operational count ≠ planned count (no hidden extras)

## Identity

Operational tasks now explicitly carry: `source_operation_code`, `source_task_rule_code`, `linked_segment_key` (when component ref is namespaced).

## Tests

- `backend/tests/test_execution_reality_sold_scope_materialize.py` — 14 scenarios (legacy, FACE/RETURN-CANT/BACK/union, blocked, idempotent, parity, identity, linked logo)

## Files

- `backend/services/execution_plan_task_parser.py`
- `backend/services/execution_plan_v2_materialize_service.py`
- `backend/tests/test_execution_reality_sold_scope_materialize.py`

## Deferred

- `execution_reality` table row seeding (observations still created on task start only)
- Employee Mobile UI changes

## Commit

Respect sold component scope in execution reality

## Next step

Ensure Employee Mobile / operator task lists read `operational_tasks[]` identity fields for subset orders in production smoke.
