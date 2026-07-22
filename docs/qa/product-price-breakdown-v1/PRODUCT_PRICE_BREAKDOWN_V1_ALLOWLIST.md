# PRODUCT_PRICE_BREAKDOWN_V1 — Strict Allowlist

## Allowed

### Backend
- `backend/schemas/product_price_breakdown.py` (new)
- `backend/services/product_price_breakdown_service.py` (new)
- `backend/services/product_price_breakdown_fixtures.py` (new)
- `backend/routers/product_price_breakdown.py` (new)
- `backend/main.py` — router include only
- `backend/tests/test_product_price_breakdown_v1.py` (new)

### Frontend
- `frontend/src/api/productPriceBreakdown.ts` (new)
- `frontend/src/features/product-system/PriceBreakdownSection.tsx` (new)
- `frontend/src/features/product-system/TemplatePricingStudioPanel.tsx` — compose section

### Docs
- `docs/qa/product-price-breakdown-v1/**`
- append canonical realignment worklog

## Forbidden

Material price edits · new supplier prices · AI formula redesign · lifecycle/publication changes · Alembic · artwork parser · Execution · mobile · push/PR
