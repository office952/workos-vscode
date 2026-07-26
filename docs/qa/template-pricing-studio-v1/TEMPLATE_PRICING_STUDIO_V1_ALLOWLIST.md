# TEMPLATE_PRICING_STUDIO_V1 — Strict Allowlist

## Allowed

### Backend (additive)
- `backend/schemas/template_pricing_recipe.py`
- `backend/services/template_pricing_recipe_service.py`
- `backend/routers/template_pricing_recipe.py`
- `backend/tests/test_template_pricing_recipe.py`

### Frontend
- `frontend/src/api/templatePricingRecipe.ts`
- `frontend/src/features/product-system/TemplatePricingStudioPanel.tsx`
- `frontend/src/features/product-system/ProductSystemTemplateDetailPanel.tsx` (tab wiring only)
- `frontend/src/features/product-system/productSystemUnifiedCatalogTypes.ts` (`pricing` section)
- Optional thin helpers under `frontend/src/features/product-system/` if required for section sync

### Docs / evidence
- `docs/qa/template-pricing-studio-v1/**`
- Canonical worklog append only:
  `docs/worklog/realignment/2026-07-20_product_system_authoring_runtime_codesign_e2e_build.md`

## Read-only dependencies (call, do not rewrite values)
- `backend/services/pricing_registry_service.py`
- `backend/services/pricing_typed_catalog.py`
- `backend/data/commercial_rules_volumetric_v2.py`
- `backend/data/internal_cost_rules_volumetric_v2.py`
- `backend/services/acm_face_treatment_commercial_path_v1.py`
- `backend/services/volum_aluminiu_component_contract.py`
- `backend/services/template_architecture_scope.py`

## Forbidden
- Pricing value / seed changes
- Inventory material row edits
- workcenter_rates data edits
- Alembic / migrations
- ACM calculation service formula changes
- XOR, logo lifecycle publish, Execution, mobile
- Broad Product System redesign
