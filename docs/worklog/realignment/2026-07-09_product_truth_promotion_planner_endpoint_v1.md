# PRODUCT_TRUTH_PROMOTION_PLANNER_READ_MODEL_ENDPOINT_V1

Status: PASS

Scope:
- backend read-only endpoint only
- no Product Truth writer
- no UI
- no Pricing / Quote / Order / Execution
- no DB / migration / seed
- no ProductAggregate / TaskGraph
- no ProductDefinition consumer change

Implemented:
- workspace helper: `get_product_truth_promotion_planner_for_workspace(...)`
- endpoint: `GET /api/v1/intake-v6/workspaces/{workspace_id}/product-truth-promotion-planner`
- focused endpoint tests: `backend/tests/test_product_truth_promotion_planner_endpoint.py`

Response shape:
- `read_only`
- `workspace_id`
- `workspace_record_id`
- `workspace_code`
- `planner_version`
- `eligible_entries[]`
- `blocked_entries[]`
- `blockers[]`
- `downstream_write_intent`
- `notes[]`

Read-only guarantees:
1. Reads existing workspace payload only.
2. Reuses the planner service; does not write Product Truth.
3. Does not modify workspace payload.
4. Does not call Pricing, Quote, Order, Execution, ProductAggregate, TaskGraph, or ProductDefinition consumers.
5. Exposes `product_truth_write = false` plus all existing write flags as false.

Validation target:
- `backend/tests/test_product_truth_promotion_planner_service.py`
- `backend/tests/test_product_truth_promotion_planner_endpoint.py`
- optional paired regression with runtime capture endpoint

Remaining blocked by design:
- no Product Truth writer
- no planner UI consumer
- no ProductDefinition consumer switch
- no downstream unlocks