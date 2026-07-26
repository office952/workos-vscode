# W3-T01 — PRODUCT_AGGREGATE_GRAPH_TO_COST_PROJECTION_V1

**Date:** 2026-07-14  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Starting HEAD:** `ca258e5`  
**Verdict:** `W3_GRAPH_COST_ADAPTER_PASS_COMMITTED`

## Summary

Introduced canonical graph-to-cost projection from Aggregate `composition_graph` for workspace paths. Wired 7B (cost BOM), 7H (EIC aligns via BOM active modules), and 7G (CPP uses shared resolver with aggregate build). Legacy `_legacy_structural_active_modules` / mounting_system bar inference no longer wins on workspace graph path.

## Contract

- **Service:** `product_aggregate_graph_cost_projection_service.resolve_cost_active_modules`
- **Schema:** `GraphCostProjection` on BOM via `graph_cost_projection`
- **TD-W3-GRAPH-COST-001:** legacy mounting inference disabled when graph present; removal when all consumers graph-only

## Tests

- New: `test_product_aggregate_graph_cost_projection.py` (11 scenarios, Cases A–D)
- Updated: `test_aggregate_cost_bom_adapter.py` (premount graph replaces steel_bars legacy expectation)
- Focused gate: **80 passed / 2 failed** (endpoint 404 — preexisting fixture debt)

## Runtime (IR-MRJS4VIK / workspace `80570a4a-a806-4305-a39c-b34a72092694`)

- Case B confirmed: ACM mounting panel in scope; volum/premount not invented
- `UPSTREAM_TRUTH_MISSING:volum_aluminum_module_template_code` explicit
- Stable repeated projection

## Remaining Wave 3

- W3-T02: V6 commercial spine (7G official, retire cost-plus override)
- W2-PREREQUISITE-VOLUM-TRUTH before full Wave 3 closure
