# W5-T03 — OrderSnapshotV2 planning/readiness adapter v1

**Date:** 2026-07-15  
**Task:** W5-T03 `ORDER_SNAPSHOT_V2_PLANNING_AND_READINESS_ADAPTER_HARDENING_V1`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Starting HEAD:** `b3d2682`  
**Application commit:** `4224022`  
**Verdict:** `W5_PLANNING_ADAPTER_PASS_COMMITTED`

## `load_order_quote_input` classification

**`REPLACE_WITH_ORDER_SNAPSHOT_V2_ADAPTER_NOW`**

Delegated to `load_order_planning_readiness_input` — V2 orders read frozen `snapshot_v2_json`; legacy orders use isolated `snapshot_line_items` path only.

## Adapter contract

`order_snapshot_v2_planning_readiness/v1` — preparation input from `product_definition_snapshot.canonical_values` with explicit `_planning_readiness_authority`.

## Authority routing

| Order type | Source | Fail mode |
|------------|--------|-----------|
| V2 (`quote_snapshot_v2_id` or `snapshot_v2_json`) | `FROZEN_ORDER_SNAPSHOT_V2` | Fail closed on missing/corrupt snapshot |
| Legacy | `LEGACY_ORDER_INPUT` | `extract_quote_input_from_snapshot` |

## Callers updated

- `task_start_gate_service.load_order_quote_input` → adapter
- `employee_mobile_tasks_service._attach_readiness_to_tasks` → same gate path (unchanged import)

## Preserved

- W5-T01 production-release guard (order-level)
- W5-T02 frozen task identity (no key regeneration)
- Material readiness via `build_procurement_enriched_context` (operational)
- Planning minutes: `DERIVED_FROM_FROZEN_TASK_CONTRACT` / partial warnings unchanged

## Tests

103 focused pytest (adapter + identity + guard + preview + step9 + production gates)

## Runtime (`:8001`)

Gate order `22099` — frozen authority, legacy line items ignored, snapshot unchanged.

Evidence: `docs/qa/product-system-active-path-isolation-v1/w5_t03_runtime_gate_evidence.json`

## Next task

**W5-INT-02** — Post-implementation gate
