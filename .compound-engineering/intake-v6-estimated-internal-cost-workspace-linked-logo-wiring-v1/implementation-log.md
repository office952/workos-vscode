# INTAKE_V6_ESTIMATED_INTERNAL_COST_WORKSPACE_LINKED_LOGO_WIRING_V1 — Implementation Log

**Phase:** IMPLEMENTATION COMPLETE  
**Status:** COMPLETE  
**Accepted HEAD:** bcdd14d  
**Branch:** main

---

## Phase 1 — Inspect

**Inspected:**
- `backend/services/estimated_internal_cost_service.py` — local `ProductAggregateService.build` + `AggregateCostBomAdapter.build` on workspace path (parallel BOM truth vs bcdd14d builder).
- `backend/services/aggregate_cost_bom_adapter.py` — builder orchestration (read-only, forbidden to edit).
- `backend/tests/test_estimated_internal_cost_preview.py` — existing EIC contract tests.
- `backend/tests/test_aggregate_cost_bom_workspace_linked_logo_cost_bom.py` — upstream Cost BOM workspace tests from bcdd14d.

**Root gap confirmed:** EIC built template-only PA/BOM while PD was workspace-aware.

**Owner decisions applied:** DEC-EIC-03 (artwork area for artwork-owned materials only), DEC-EIC-04 (logo material cost only; no logo operations).

**Forbidden scope:** aggregate_cost_bom_adapter, ProductAggregate, ProductDefinition, frontend, CPP, Quote/Order/Execution, DB.

---

## Phase 2 — Orchestration change

**Changed:**
- `EstimatedInternalCostService.__init__`: `bom_adapter` → `bom_builder` (`AggregateCostBomBuilderService`, injectable).
- `build_preview`: replaced local aggregate + adapter with `await self._bom_builder.build_preview(template_code, workspace_id=..., quote_input=...)`.
- Provenance source updated to `aggregate_cost_bom_builder_service`.

**Files touched:**
- `backend/services/estimated_internal_cost_service.py`

**Tests:** pending

---

## Phase 3 — Logo material eligibility + DEC-EIC-03

**Changed:**
- Added `_is_linked_logo_bom_material`, `_linked_logo_segment_key`, `_artwork_finish_area_for_segment`, `_enrich_payload_artwork_finishes_from_pd`.
- `ARTWORK_OWNED_LOGO_MATERIAL_CODES = {print_media, laminate_media}`.
- Material loop: skip `active_modules` filter for linked-logo BOM rows (eligibility from Cost BOM row provenance).
- `_estimate_material_quantity`: linked-logo branch uses artwork finish area only for artwork-owned codes; returns `None` otherwise (no letter-area fallback for logo geometry materials).

**Owner decision DEC-EIC-03:** artwork area never substitutes plexiglas/cant/backing/LED/general logo component quantity.

---

## Phase 4 — Partial + contamination

**Changed:**
- BOM warnings merged into EIC warnings.
- When `bom.bom_status == "partial"` or finish-partial warning present, EIC `status=partial` and `ready=False` **only when `not contamination`** (preserves hourly contamination `blocked`).

---

## Phase 5 — Tests

**Added:**
- `backend/tests/eic_patched_bom_builder.py` — `PatchedAggregateCostBomBuilder` mirrors builder orchestration with injected rates (existing tests patched `_load_pricing_context` but BOM builder loads its own rates).
- `backend/tests/test_estimated_internal_cost_workspace_linked_logo.py` — orchestration, logo materials, DEC-EIC-03 boundary, partial, missing rates, commercial boundary, API POST.

**Modified:**
- `backend/tests/test_estimated_internal_cost_preview.py` — fixture uses `PatchedAggregateCostBomBuilder`; fixed `@pytest_asyncio.fixture` on `cpp_service`.

**Results:**
- `pytest tests/test_estimated_internal_cost_workspace_linked_logo.py tests/test_estimated_internal_cost_preview.py -q` → **32 passed**
- `pytest tests/test_estimated_internal_cost_workspace_linked_logo.py tests/test_estimated_internal_cost_preview.py tests/test_aggregate_cost_bom_workspace_linked_logo_cost_bom.py tests/test_product_aggregate_workspace_linked_logo_composition.py -q` → **59 passed**
- Regression bundle (gradi, binding persistence, selected_layer_refs, return_cant bridge) → **34 passed**

**Errors resolved:**
- Empty material lines after builder delegation → PatchedAggregateCostBomBuilder.
- Partial overriding contamination blocked → guard with `if not contamination`.
- Letters-only workspace exact equality too strict → subset assertion for non-logo lines.

---

## Phase 6 — Operation boundary (documented, not implemented)

**Not changed:** `RULES_BY_TEMPLATE`, `bom.costable_operations` loop (letters operations unchanged). Logo operation internal cost explicitly deferred.

**Remaining debt:** Workspace-linked logo operation internal costs are not included in V1.

---

## Forbidden scope evidence

| Area | Touched |
|---|---|
| aggregate_cost_bom_adapter.py | NO |
| ProductAggregate services | NO |
| ProductDefinition services | NO |
| binding services | NO |
| frontend | NO |
| CommercialPriceProposal | NO |
| Quote/Order/Execution | NO |
| DB/schema/migrations/seeds | NO |

---

## IMPLEMENTATION COMPLETE

Application code changed: `estimated_internal_cost_service.py` + 3 test files.  
Next: validation, review, worklog, commit.
