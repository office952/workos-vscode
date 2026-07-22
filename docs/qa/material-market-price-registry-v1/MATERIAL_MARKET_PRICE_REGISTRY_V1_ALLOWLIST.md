# MATERIAL_MARKET_PRICE_REGISTRY_V1 — Strict Allowlist

## Allowed

### Backend
- `backend/schemas/material_market_price_registry.py` (new)
- `backend/services/material_market_price_registry_service.py` (new)
- `backend/routers/material_market_price_registry.py` (new)
- `backend/services/product_price_breakdown_service.py` — material provenance enrich only
- `backend/schemas/product_price_breakdown.py` — additive optional fields only
- `backend/tests/test_material_market_price_registry_v1.py` (new)

### Frontend
- `frontend/src/api/materialMarketPriceRegistry.ts` (new)
- `frontend/src/features/pricing/MaterialMarketPriceRegistryPanel.tsx` (new)
- `frontend/src/components/pricing/PricingRegistrySpaciousView.tsx` — compose panel
- `frontend/src/api/pricingRegistry.ts` — types only if needed
- targeted vitest

### Docs
- `docs/qa/material-market-price-registry-v1/**`
- canonical realignment worklog append

## Forbidden

Alembic · invented supplier prices · OCR · scraping · labor AI redesign · lifecycle · Execution · artwork parser · push/PR · emptying Inventory
