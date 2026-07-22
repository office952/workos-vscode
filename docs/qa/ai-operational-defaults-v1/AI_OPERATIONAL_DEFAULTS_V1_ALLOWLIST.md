# AI_OPERATIONAL_DEFAULTS_V1 — Strict Allowlist

## Allowed

### Backend
- `backend/data/ai_operational_defaults_v1.py` (new)
- `backend/data/ai_operational_defaults_overrides_v1.json` (new, optional overrides)
- `backend/services/ai_operational_defaults.py` (new)
- `backend/schemas/template_pricing_recipe.py` (additive 1.2.0)
- `backend/services/template_pricing_recipe_service.py`
- `backend/services/template_labor_formula_truth.py` (wire only if needed)
- `backend/routers/*` or product-system router — additive PATCH/GET for overrides
- `backend/tests/test_ai_operational_defaults.py` (new)
- targeted existing pricing recipe tests

### Frontend
- `frontend/src/api/templatePricingRecipe.ts`
- `frontend/src/features/product-system/TemplatePricingStudioPanel.tsx`
- `frontend/src/features/product-system/AiOperationalDefaultsSection.tsx` (new)
- targeted FE tests

### Docs
- `docs/qa/ai-operational-defaults-v1/**`
- append: canonical realignment worklog

## Forbidden

Alembic · HR/payroll · Inventory rate rewrites · ACM treatment unblock · XOR · dual-select · Execution · artwork · mobile · push/PR
