# PRODUCT_SYSTEM_REFERENCE_FINISH_LINE_V1 — Allowlist

## Allowed

### Backend
- `backend/data/product_system_reference_finish_line_v1.py`
- `backend/data/intake_v6_vl_form_field_ownership_map_v1.py`
- `backend/schemas/product_system_reference_finish_line.py`
- `backend/schemas/workflow_adv_analyzer_io_contract_v1.py`
- `backend/services/product_system_reference_finish_line_service.py`
- `backend/routers/product_system_reference_finish_line.py`
- `backend/schemas/product_price_breakdown.py` — label fields only
- `backend/services/product_price_breakdown_service.py` — ownership note only
- `backend/tests/test_product_system_reference_finish_line_v1.py`

### Frontend
- `frontend/src/api/productSystemReferenceFinishLine.ts`
- `frontend/src/features/product-system/PriceBreakdownSection.tsx` — production-cost labels
- `frontend/src/features/product-system/TemplateCompositionAuthoringPanel.tsx` — lab limitation banner
- `frontend/src/features/product-system/ProductSystemReferenceFinishLinePanel.tsx` (optional surface)
- `frontend/src/features/product-system/ProductSystemTemplateDetailPanel.tsx` — wire panel if minimal
- targeted vitest

### Docs
- `docs/qa/product-system-reference-finish-line-v1/**`
- canonical worklog append

## Forbidden

Supplier Import · material price writes · Form Builder · SVG parser · offer/markup · Execution · Alembic · push/PR
