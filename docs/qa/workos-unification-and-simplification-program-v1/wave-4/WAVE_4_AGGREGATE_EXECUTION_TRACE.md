# Wave 4 gap closure — ProductAggregate → Execution

Fixture (existing, no mutation):

| Field | Value |
|-------|--------|
| WORKSPACE | `IR-MSRB28PU` / header `IV6-F823AA06` |
| ORDER SNAPSHOT | `ORD-IV6-V2-1786318810-31` |
| EXECUTION_PLAN | `/execution/973024` |
| PRODUCT_AGGREGATE_GRAPH_IDENTITY | `TPL-VOLUMETRIC-LETTERS_v2` + child `TPL-VOLUM-ALUMINIU_v1` |
| COMPONENT/OPERATION IDS | `task_contract.task_rules` → `node:root_product:TPL-VOLUMETRIC-LETTERS_v2:…` |
| OPERATIONAL_TASK IDS | materialized `operational_tasks[]` / `GET /api/v1/operator/tasks` |
| ATELIER_VISIBLE_IDENTITY | Live card = **`ORD-92400`** (different work). Job list may show `JOB-973024`. |
| OPERATOR_VISIBLE_IDENTITY | 18 tasks for 973024 buried in unbounded list (`JOB-973024`) |

## Code path (read-only)

ProductAggregate `task_contract`  
→ OrderSnapshotV2 `product_aggregate_snapshot`  
→ `execution_plan_v2_preview_service`  
→ persist envelope  
→ `execution_plan_v2_materialize_service`  
→ `GET /api/v1/operator/tasks`

Frozen-graph preview (`execution_preview_from_frozen_graph_service`) is read-only and was not invoked as a write.

Wave 3 already proved: 973024 has 18 tasks, 0 `in_progress`; Atelier live ≠ this order (`DIFFERENT_ACTIVE_WORK`).

Gap-closure adds a fresh read-only `GET /api/v1/operator/tasks` sample in `runtime/rt-gap-closure-log.json` (`apiProbe`).

**AGGREGATE_TO_EXECUTION_TRACE = PROVEN** at plan/task-id grain.  
UI projection remains PARTIAL (operator/Atelier hide the template graph). That does **not** reopen the architectural model.
