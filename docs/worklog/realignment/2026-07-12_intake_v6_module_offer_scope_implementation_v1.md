# Intake V6 module offer scope implementation v1

**Date:** 2026-07-12  
**Task:** INTAKE_V6_MODULE_OFFER_SCOPE_IMPLEMENTATION_V1  
**HEAD before:** ba3c0e2

## What changed

- Added `offer_scope` schema (`mode`, `sold_modules`) on workspace payload
- Added single canonical map (`FACE` → `debitare_fata`, etc.)
- Added `offer_scope_resolver_service` — legacy default + component_subset sold filter
- Wired BOM, EIC, CPP active-module resolution through resolver
- `calc_modules` derived only (never persisted, never priced)

## Why

Enable component-scoped BOM/EIC/CPP on existing root `TPL-VOLUMETRIC-LETTERS_v2` without new templates or duplicate component truth.

## Tests

```powershell
pytest tests/test_offer_scope_resolver.py tests/test_offer_scope_bom_eic_cpp_filter.py tests/test_aggregate_cost_bom_adapter.py tests/test_commercial_price_proposal_preview.py tests/test_estimated_internal_cost_preview.py tests/test_product_definition_builder.py -q
```

**Result:** 103 passed

## Files

- `backend/schemas/offer_scope.py` (new)
- `backend/data/offer_scope_canonical_map.py` (new)
- `backend/services/offer_scope_resolver_service.py` (new)
- `backend/tests/test_offer_scope_resolver.py` (new)
- `backend/tests/test_offer_scope_bom_eic_cpp_filter.py` (new)
- `backend/schemas/intake_v4.py`
- `backend/services/aggregate_cost_bom_adapter.py`
- `backend/services/estimated_internal_cost_service.py`
- `backend/services/commercial_price_proposal_service.py`

## Deferred

- Intake V6 UI, snapshot, offer, order, execution
- LIGHTING/ELECTRICAL/FINISH/MOUNTING subset offers
- Logo per-segment sold scope
- ProductDefinition module_active alignment

## Next step

`QUOTE_SNAPSHOT_WORKSPACE_AGGREGATE_UNIFICATION_V1` or Intake sold-scope visibility UI
