# LABOR_RECIPE_CONTRACT_V1 — Allowlist

## Allowed

### Backend
- `backend/schemas/template_pricing_recipe.py` (additive labor models + version)
- `backend/services/template_labor_recipe.py` (new extraction helper)
- `backend/services/template_pricing_recipe_service.py` (wire labor_recipes)
- `backend/tests/test_template_labor_recipe.py` (new)
- `backend/tests/test_template_pricing_recipe.py` (additive assertions only)

### Frontend
- `frontend/src/api/templatePricingRecipe.ts`
- `frontend/src/features/product-system/TemplatePricingStudioPanel.tsx`
- Optional: `frontend/src/features/product-system/TemplateLaborRecipeSection.tsx`

### Docs
- `docs/qa/labor-recipe-contract-v1/**`
- Worklog append only:
  `docs/worklog/realignment/2026-07-20_product_system_authoring_runtime_codesign_e2e_build.md`

## Forbidden
Rate values, seeds, HR, Alembic, ACM calc changes, XOR, dual-select, Execution, mobile.
