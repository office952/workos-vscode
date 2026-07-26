# TEMPLATE_ACTIVATION_V1 — Strict Allowlist

## Allowed

### Backend
- `backend/services/product_template_publication_service.py` — structural vs warning blockers; AI provenance evidence
- `backend/services/template_activation_eligibility.py` (**new**) — shared activation map
- `backend/services/product_e2e_readiness_service.py` — optional ACM logo honesty status demotion only
- `backend/schemas/product_template_publication.py` — additive eligibility/AI fields
- `backend/routers/product_system_publication.py` — only if response needs new fields
- `backend/tests/test_product_template_publication_v1.py`
- `backend/tests/test_template_activation_eligibility.py` (**new**)
- targeted ACM composition / e2e tests if status expectation changes

### Frontend
- `frontend/src/App.tsx` — Inventar `end` exact match
- `frontend/src/features/product-system/productSystemPublicationGate.ts`
- `frontend/src/features/product-system/ProductTemplatePublicationPanel.tsx`
- `frontend/src/features/product-system/TemplateActivationReadinessPanel.tsx` (**new**, optional compose)
- `frontend/src/api/productTemplatePublication.ts`
- targeted FE gate tests

### Docs
- `docs/qa/template-activation-v1/**`
- append canonical realignment worklog

## Forbidden

New Alembic · new pricing rates · AI formula redesign · HR · Inventory data · Execution materialization · artwork · mobile · dual-select · push/PR
