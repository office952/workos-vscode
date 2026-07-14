# W3-T02 — INTAKE_V6_OFFICIAL_7G_COMMERCIAL_PRICING_SPINE_V1

**Date:** 2026-07-14  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Starting HEAD:** `3eae7c4`  
**Verdict:** `W3_V6_7G_SPINE_PASS_COMMITTED`

## Scope

Wire Intake V6 priced-quote dry-run and operator pricing display to **7G (`CommercialPriceProposalService`)** as the only official commercial authority. Remove cost-plus override from official totals. Keep **7H** separate. No snapshot/Offer/Order/tariff/volum persistence work.

## Root cause

`build_intake_v6_priced_quote_dry_run` replaced 7G totals with `_build_cost_plus_totals()` when material breakdown internal cost existed, emitting warning `official_v6_pricing_uses_cost_plus_from_material_breakdown`. Frontend mirrored this via `buildIntakeV6OfferModel()` fallback when backend totals were absent.

## Implementation

- Backend: official `commercial_totals` only when 7G subtotal > 0 and no blockers; `pricing_authority=commercial_price_proposal_7g`; cost-plus moved to `diagnostic_cost_plus_trace` (TD-W3-V6-DIAG-COST-PLUS-001).
- Frontend: `intakeV6OfficialPricing.ts` helper; hero/slider/full panels use 7G totals only; client calculator relegated to non-authoritative internal structure / diagnostic label.

## Runtime (IR-MRJS4VIK / `80570a4a-a806-4305-a39c-b34a72092694`)

| Field | Value |
|-------|-------|
| `pricing_authority` | `commercial_price_proposal_7g` |
| Official `total_gross` | 1888.68 RON (7G) |
| Diagnostic cost-plus `total_gross` | 5926.91 RON (non-authoritative) |
| 7H trace | partial/blocked (missing MAT-ACM-BOND-PANEL unit_cost) |
| `volum_aluminum_module_template_code` | null (upstream gap; does not synthesize price) |

## Tests

- `tests/test_intake_v6_priced_quote_dry_run.py` — 24 passed (incl. blocked-7G no cost-plus, 7G vs diagnostic divergence)
- `tests/test_intake_v6_priced_quote_dry_run_runtime.py` — passed
- `tests/test_product_aggregate_graph_cost_projection.py` — passed (W3-T01 regression)
- `src/lib/intakeV6/intakeV6OfficialPricing.test.ts` — 4 passed

## Preexisting debt (non-blocking)

- `test_estimated_internal_cost_preview.py::test_post_endpoint_returns_preview` — **AUTH_OR_ROUTE_TEST_CONFIGURATION** (404)
- `test_commercial_price_proposal_preview.py::test_post_endpoint_returns_preview` — **AUTH_OR_ROUTE_TEST_CONFIGURATION** (404)

## W3-T03 boundary

`snapshot_v2` synthetic CPP and pricing registry completeness remain for W3-T03.

## Temporary debt

- **TD-W3-V6-DIAG-COST-PLUS-001** — `diagnostic_cost_plus_trace`; consumer: admin/debug; removal: W3-T03 or when no consumer needs legacy preview.
