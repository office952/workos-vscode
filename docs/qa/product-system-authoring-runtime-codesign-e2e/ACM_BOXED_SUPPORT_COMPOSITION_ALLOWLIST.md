# ACM Boxed Support Composition Extension — Allowlist

| Field | Value |
|-------|--------|
| Date | 2026-07-21 |
| Kickoff HEAD | `5dfe807a` (reconfirmed) |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Subject | Extend `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` — letters XOR logo + optional frame |
| Decision | **A** locked |

## Commit sequence (allowlist only)

| # | Message |
|---|---------|
| 1 | `feat(product-system): extend ACM boxed support composition` |
| 2 | `feat(product-system): add letters-logo XOR and optional frame contracts` |
| 3 | `feat(product-system): compile ACM composite truth quantities and readiness` |
| 4 | `fix(product-system-ui): expose applied content and optional frame configuration` |
| 5 | `test(product-system): prove ACM composition and reuse invariants` |
| 6 | `docs(qa): finalize ACM second-product evidence` |

## Allowed paths

### Backend

- `backend/seeds/seed_tpl_acm_boxed_mounting_support_v1.py`
- `backend/services/acm_boxed_support_composition_v1.py` (new)
- `backend/services/product_definition_composition_contract.py`
- `backend/services/product_definition_builder_service.py` (ACM standalone composition only)
- `backend/services/product_aggregate_service.py` (ACM child mapping only)
- `backend/services/product_e2e_readiness_service.py` (ACM composition readiness only)
- `backend/services/acm_quote_input_helpers.py` (applied_content helpers only)
- `backend/services/acp_internal_frame_domain.py` (optional-frame operator marker only if needed)
- `backend/tests/test_acm_boxed_support_composition_v1.py` (new)
- `backend/tests/test_acm_boxed_mounting_standalone_offer_v1.py` (narrow extensions)
- `backend/tests/test_acm_boxed_mounting_template_v1.py` (narrow extensions)
- `backend/tests/test_product_definition_composition_contract*.py` (if present; ACM XOR only)
- `backend/tests/test_acp_internal_frame_domain_v1.py` (optional frame only if needed)

### Frontend

- `frontend/src/features/product-system/AcmBoxedAppliedContentPanel.tsx` (new)
- `frontend/src/features/product-system/AcmBoxedAppliedContentPanel.test.tsx` (new)
- `frontend/src/features/product-system/TemplateCompositionAuthoringPanel.tsx`
- `frontend/src/features/product-system/ProductSystemTemplateDetailPanel.tsx`
- `frontend/src/features/product-system/productSystemAdminDisplay.ts` (labels only)
- `frontend/src/lib/intakeV6/acmPanel/types.ts` (applied_content type only if needed)
- `frontend/src/lib/intakeV6/acmPanel/operatorPatch.ts` (applied_content / frame optional only if needed)

### Docs / QA / worklog

- `docs/qa/product-system-authoring-runtime-codesign-e2e/ACM_BOXED_SUPPORT_COMPOSITION_*`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/runtime/acm_boxed_support_composition_*`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/screenshots/acm-boxed-composition/**`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/BOND_SECOND_PRODUCT_CP0_FREEZE.md` (pointer to frozen A)
- `docs/worklog/realignment/2026-07-20_product_system_authoring_runtime_codesign_e2e_build.md` (section **ACM BOXED SUPPORT COMPOSITION EXTENSION** only)

## Forbidden

- New panel / composite root SKU
- Publishing any product; auto-activating inactive children; VL publication
- Schema migrations / Alembic / PI / CI / ComponentTemplate tables
- Pricing redesign / CostEngine formula invent / VL Aluminiu formula changes
- SVG/DWG/DXF / artwork analysis / Build 2 / Execution materialization
- Treating logo RETURN/cant as full logo product
- Automatic metal-frame thresholds
- `git add -A`, stash, reset, clean, push, PR
- Unrelated dirty-tree paths
