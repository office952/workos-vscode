# ACTIVE_TEMPLATE_CRITICAL_MATERIAL_FILL_V1 — Allowlist

## Allowed

- `backend/services/material_variant_selector_policy.py` (new — shared selector identity)
- `backend/services/material_market_price_registry_service.py` — critical/selector classification
- `backend/schemas/material_market_price_registry.py` — additive role fields only
- `backend/data/product_system_reference_finish_line_v1.py` — seed reclassify PSU
- `backend/services/product_system_reference_finish_line_service.py` — critical honesty
- `backend/tests/test_active_template_critical_material_fill_v1.py`
- adjust `test_product_system_reference_finish_line_v1.py` critical assertion if needed
- FE display only if registry already surfaces warning (prefer backend-only)
- `docs/qa/active-template-critical-material-fill-v1/**`
- canonical worklog append

## Forbidden

Supplier Import · invent generic PSU price · unrelated materials · offer/markup · Execution · SVG · Alembic · push/PR
