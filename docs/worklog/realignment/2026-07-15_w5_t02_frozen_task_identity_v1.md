# W5-T02 — Frozen component graph → execution task identity v1

**Date:** 2026-07-15  
**Task:** W5-T02 `FROZEN_COMPONENT_GRAPH_TO_EXECUTION_TASK_IDENTITY_V1`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Starting HEAD:** `64fe7c2`  
**Application commit:** `136df46`  
**Docs commit:** `b994c25`  
**Verdict:** `W5_TASK_IDENTITY_PASS_COMMITTED`

## Task identity contract

`frozen_task_identity/v1` on `PlannedTaskPreview.frozen_identity` and materialized operational tasks.

Deterministic key: `{source_graph_node_id}:{source_task_rule_code}`  
Linked logo: `{node}:seg:{segment_key}:{task_rule_code}`

## Implementation

- **Service:** `execution_plan_v2_frozen_task_identity_service.py`
- **Preview hook:** `_build_planned_tasks` enriches rules from frozen graph + synthesizes child-node tasks from namespaced operations
- **Materialize:** propagates `frozen_identity` + top-level identity fields on operational tasks
- **No live Product System rebuild** on V2 path

## Component coverage

| Component | Result |
|-----------|--------|
| Root product | `FULL_FROZEN_COMPONENT_IDENTITY` via `node:root_product:{template}` |
| Mounting panel | Graph node + template + instance binding |
| Premount structure | Graph-derived operation tasks when present |
| Volum/cant | `COMPONENT_LOCAL` scope on `volum_aluminum` node |
| Logo segments | `PARTIAL_IDENTITY_NONBLOCKING` — segment + instance preserved |

## `load_order_quote_input`

**Classification:** `KEEP_READ_ONLY_FOR_W5_T03`  
Reads legacy `snapshot_line_items` only for readiness gates; does not affect V2 task identity.

## Owner-decision scope

Production guard remains **order-level** (`ORDER_SCOPE_ONLY`). Identity fields enable future narrowing but do not change W5-T01 behavior.

## Tests

```
test_execution_plan_v2_frozen_task_identity.py — 15
+ preview/persist/materialize/step9/guard/order_convert — 160
Total focused: 175 passed / 0 failed
```

## Runtime (`:8001`)

Gate order `21099` — preview keys stable, mounting tasks graph-bound, snapshot unchanged.

Evidence: `docs/qa/product-system-active-path-isolation-v1/w5_t02_runtime_gate_evidence.json`

## Next task

**W5-INT-02** — Post-implementation gate
