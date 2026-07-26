# PRICING_FOUNDATION_V1 — Strict Allowlist

## Allowed writes

### Frontend
- `frontend/src/lib/inventory/inventoryMaterialClassification.ts` (new)
- `frontend/src/lib/inventory/inventoryMaterialClassification.test.ts` (new)
- `frontend/src/hooks/useInventoryData.ts`
- `frontend/src/lib/mockData.ts` (StockStatus / InventoryMaterial additive only)
- `frontend/src/lib/inventoryEngine.ts` (null-stock safety only)
- `frontend/src/pages/Inventory.tsx`
- `frontend/src/api/pricingRegistry.ts` (additive fields)
- `frontend/src/lib/pricingRegistry.ts`
- `frontend/src/lib/pricingRegistry.test.ts`
- `frontend/src/lib/pricing/pricingTypedCatalog.ts` (new)
- `frontend/src/lib/pricing/pricingTypedCatalog.test.ts` (new)
- `frontend/src/lib/pricing/pricingDisplayNaming.ts` (new)
- `frontend/src/components/pricing/PricingRegistrySpaciousView.tsx`
- `frontend/src/components/pricing/PricingEntryRow.tsx` (labels / warnings only)
- `frontend/src/components/pricing/pricingRegistryUi.ts` (tab meta if needed)

### Backend
- `backend/services/pricing_typed_catalog.py` (new)
- `backend/services/pricing_registry_service.py` (additive metadata only)
- `backend/tests/test_pricing_typed_catalog.py` (new)
- `backend/tests/test_pricing_registry.py` (additive assertions only)

### Docs / evidence
- `docs/qa/pricing-foundation-v1/**`
- `docs/worklog/realignment/2026-07-20_product_system_authoring_runtime_codesign_e2e_build.md` (append section)
- screenshots under `docs/qa/pricing-foundation-v1/screenshots/**`

## Forbidden
- ACM services / face-treatment commercial wiring
- CPP/EIC formula changes
- Product Templates / seeds / pricing values
- DB migrations / Alembic
- HR
- Execution / mobile
- XOR / volumetric dual-select
- Template Pricing Studio
