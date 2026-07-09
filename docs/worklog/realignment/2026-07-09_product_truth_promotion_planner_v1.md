# PRODUCT_TRUTH_PROMOTION_PLANNER_V1

Status: PASS

Scope:
- backend read-only planner only
- no Product Truth writer
- no UI
- no Pricing / Quote / Order / Execution
- no DB / migration / seed
- no ProductAggregate / TaskGraph
- no ProductDefinition consumer change
- no endpoint change

Implemented:
- new backend planner service: `backend/services/product_truth_promotion_planner_service.py`
- focused pytest coverage: `backend/tests/test_product_truth_promotion_planner_service.py`

Planner output:
- `planner_version = "v1"`
- `eligible_entries[]`
- `blocked_entries[]`
- `blockers[]`
- `downstream_write_intent` with all flags false

Planner behavior:
1. Reuses `build_form_system_runtime_capture_read_model(...)` as the fail-closed source of field state.
2. Promotes only entries with `state = confirmed`.
3. Splits `svg.selected_layer_refs[]` into layer-level entries keyed by stable `layer_id`.
4. Splits `finish.print_required` and `finish.lamination_required` into row-level entries keyed by stable `layer_key`.
5. Blocks row entries when row identity is missing.
6. Blocks artwork booleans when only `execution_type` evidence exists.
7. Blocks `mounting_scope` when only `mounting_system` exists.
8. Blocks `support_type` when only support/mounting/SVG evidence exists.
9. Performs no Product Truth, Pricing, Quote, Order, Execution, ProductAggregate, TaskGraph, or DB write.

Validation target:
- `backend/tests/test_form_system_runtime_capture_read_model.py`
- `backend/tests/test_product_truth_promotion_planner_service.py`

Remaining blocked by design:
- no Product Truth writer
- no ProductDefinition consumer switch to planner output
- no endpoint exposure for planner output
- no downstream unlocks