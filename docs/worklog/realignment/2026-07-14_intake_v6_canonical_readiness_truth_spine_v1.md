# W1-L-SPINE — INTAKE_V6_CANONICAL_READINESS_TRUTH_SPINE_V1

**Task:** W1-L-SPINE  
**Starting HEAD:** `fe6c6f7`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Date:** 2026-07-14

## Lane reservation (operating model §4)

| Field | Value |
|-------|-------|
| Start HEAD | `fe6c6f7` |
| Canonical truths reserved | `mounting_solution`, runtime capture blockers, workspace `readiness_status`, pricing `is_ready_for_quote`, handoff policy fatal/review sets |
| Services reserved | `intake_v6_canonical_readiness_service`, `intake_v6_workspace_service`, `intake_v6_pricing_input_service`, `intake_v6_commercial_quote_service`, `intake_v4_internal_draft_quote_policy_service`, `form_system_runtime_capture_read_model_service`, `form_system_contract_backbone_service`, `form_system_contract_mapping_adapter_service`, `intake_v4_finish_truth_service`, `product_truth_promotion_planner_service` |
| Tests reserved | `test_intake_v6_canonical_readiness_spine.py`, runtime capture + backbone + planner suites |
| Downstream consumers | Product Definition preview (read-only), priced-quote dry-run adapter_blockers, promotion planner |
| Collision risks | W1-L-FINISH finish persistence, W1-L-CANT return contract — deferred |
| Integration point | W1-INT-01 |

## Root cause

Parallel readiness authorities: workspace `_derive_readiness_status` ignored runtime capture blockers; capture gated legacy `support.support_type` instead of canonical `mounting_solution`; handoff policy did not consume pricing adapter blockers; `merge_policy_findings` unwired.

## Implementation summary

- Added `mounting_solution_runtime_state` and `mounting.mounting_solution` runtime capture field.
- Legacy `support.support_type` demoted to compatibility-only in backbone; does not block when canonical mounting satisfies.
- `list_runtime_capture_fatal_blocker_codes` + `apply_readiness_spine_to_pricing_preview` centralize effective blockers.
- `_derive_readiness_status` returns `runtime_capture_blocked` when capture blockers active.
- Handoff policy consumes capture + pricing adapter blockers; `merge_policy_findings` wired in V6 quote handoff preview and draft create.

## Tests

```text
pytest tests/test_intake_v6_canonical_readiness_spine.py \
  tests/test_form_system_runtime_capture_read_model.py \
  tests/test_form_system_contract_backbone.py \
  tests/test_product_truth_promotion_planner_service.py \
  tests/test_form_system_runtime_capture_read_model_endpoint.py -q
→ 62 passed
```

## Runtime verification (fixture `80570a4a-a806-4305-a39c-b34a72092694`)

| Check | Result |
|-------|--------|
| `mounting_solution` persisted (ACM) | confirmed |
| Stale `SUPPORT_TYPE_MISSING` in capture | absent |
| Unrelated finish blockers | preserved (FINISH_TARGET, print/lamination) |
| Derived readiness with blockers | `runtime_capture_blocked` |
| Stored DB readiness (pre-resave) | `ready_for_quote_preview` (stale until next persist) |

## Gates

- Task gate: PASS (focused tests)
- W1-INT-01: PASS (mounting, capture, policy merge, readiness, handoff aligned in code path)
