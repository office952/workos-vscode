# Execution sold scope read path V1

**Date:** 2026-07-12  
**Task:** EXECUTION_SOLD_SCOPE_READ_PATH_V1  
**HEAD before:** ffef92a

## Change

Execution Plan V2 preview and persist now filter planned tasks and operations by frozen `OrderSnapshotV2.offer_scope_snapshot.resolved_runtime_sold_modules`. No resolver rerun, no aggregate rebuild, no repricing.

## Filter logic

- **Legacy / full_product:** absent scope, `use_legacy=true`, or `mode=full_product` → no filtering.
- **component_subset:** include rules/ops when `effective_runtime_module` ∈ frozen sold runtime modules.
- **vector_prep:** always included (`file_preparation` / `vector_prep`).
- **linked_segment:** included only when filtering disabled.
- **Invalid subset:** empty `resolved_runtime_sold_modules` → `blocked_missing_sold_scope`.

## Alias

Execution-only: `return_face_bonding` → `modelare_cant` (RETURN-CANT slice). Applied before stored `mini_module_code=asamblare`.

## Tests

- `backend/tests/test_execution_sold_scope_reader.py` — reader unit + no-resolver/no-aggregate guards
- Extended `test_execution_plan_v2_preview.py` — legacy, subsets, linked logo, invalid block
- Extended `test_step9_order_snapshot_to_execution_plan.py` — persist parity + invalid block

## Files

- `backend/services/execution_sold_scope_reader_service.py` (new)
- `backend/services/execution_plan_v2_preview_service.py`
- `backend/schemas/execution_plan_v2.py` (`blocked_missing_sold_scope` status)
- tests above

## Deferred scope

- FINISH / LIGHTING / MOUNTING subset execution
- Logo per-segment sold scope
- Material readiness filtering
- ExecutionReality / materialize changes

## Commit

Filter execution tasks by sold component scope

## Next step

Wire ExecutionReality materialize to respect the same frozen sold scope when task rows are created.
