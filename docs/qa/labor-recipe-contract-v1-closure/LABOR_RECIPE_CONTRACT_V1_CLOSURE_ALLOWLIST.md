# LABOR_RECIPE_CONTRACT_V1_CLOSURE — Strict Allowlist

## Allowed

### Frontend
- `frontend/src/features/product-system/ProductSystemTemplateDetailPanel.tsx`
- `frontend/src/features/product-system/templatePricingStudioEligibility.ts` (new, if needed)
- `frontend/src/features/product-system/TemplatePricingStudioPanel.tsx`
- `frontend/src/api/templatePricingRecipe.ts`
- targeted FE tests only if required

### Backend
- `backend/schemas/template_pricing_recipe.py` (additive 1.1.1)
- `backend/services/template_labor_recipe.py`
- `backend/services/template_labor_formula_truth.py` (new)
- `backend/services/template_pricing_recipe_service.py` (wire only)
- `backend/tests/test_template_labor_recipe.py`
- `backend/tests/test_template_labor_formula_truth.py` (new)

### Docs / evidence
- `docs/qa/labor-recipe-contract-v1-closure/**`
- append only: `docs/worklog/realignment/2026-07-20_product_system_authoring_runtime_codesign_e2e_build.md`

## Forbidden

Rate values · workcenter seed data · Inventory · Alembic · HR · ACM calc · XOR · dual-select · Execution · artwork · mobile · push/PR
