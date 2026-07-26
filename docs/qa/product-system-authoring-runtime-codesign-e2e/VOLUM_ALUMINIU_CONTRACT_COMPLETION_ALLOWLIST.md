# VOLUM ALUMINIU Component Contract Completion — Allowlist

| Field | Value |
|-------|--------|
| Date | 2026-07-21 |
| Kickoff HEAD | `6608cdc5` |
| CP0 map | `VOLUM_ALUMINIU_COMPONENT_CONTRACT_CP0_SHARED_MAP.md` |

## Commit sequence (allowlist only)

| # | Message |
|---|---------|
| 1 | `feat(product-system): complete aluminium return input and provenance contract` |
| 2 | `feat(product-system): close aluminium return quantity and operation ownership` |
| 3 | `feat(product-system): add safe separate calculation preview and readiness` |
| 4 | `fix(product-system-ui): clarify aluminium return contract and confirmation` |
| 5 | `test(product-system): prove aluminium return separate calculation boundaries` |
| 6 | `docs(qa): commit audit and completion evidence` |

## Allowed paths (union across commits)

### Backend

- `backend/schemas/product_template_component_contract.py`
- `backend/schemas/volum_aluminiu_separate_calc_preview.py` (new)
- `backend/services/product_template_component_contract_service.py`
- `backend/services/return_cant_product_truth_bridge.py`
- `backend/services/volum_aluminiu_component_contract.py` (new)
- `backend/services/volum_aluminiu_separate_calc_preview_service.py` (new)
- `backend/services/volum_aluminiu_quantity_ownership.py` (new)
- `backend/services/intake_v6_modular_form_contract_service.py` (depth options only)
- `backend/services/product_e2e_readiness_service.py` (contract completeness findings only; keep inactive blocker)
- `backend/routers/volum_aluminiu_separate_calc_preview.py` (new)
- `backend/tests/test_return_cant_product_truth_bridge.py`
- `backend/tests/test_product_template_component_contracts_v1.py`
- `backend/tests/test_volum_aluminiu_separate_calc_preview.py` (new)
- `backend/tests/test_volum_aluminiu_quantity_ownership.py` (new)
- `backend/tests/test_product_e2e_readiness_v1.py` (only if needed for new findings; do not weaken inactive assertion)

### Frontend (commit 4 only, minimal)

- `frontend/src/features/product-system/productSystemAdminDisplay.ts`
- `frontend/src/features/product-system/productSystemAdminDisplay.test.ts`
- `frontend/src/pages/ProductSystem.tsx` (ownership card status/labels only)
- `frontend/src/features/product-system/TemplateLibraryView.tsx` (label only if needed)
- Related vitest if touched

### Docs / QA (commit 6 + CP0 early)

- `docs/qa/product-system-authoring-runtime-codesign-e2e/VOLUM_ALUMINIU_*`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/volum-aluminiu-audit/**`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/volum-aluminiu-completion/**`
- `docs/worklog/realignment/2026-07-20_product_system_authoring_runtime_codesign_e2e_build.md`

## Forbidden

- Activation / publish transitions
- Schema migrations / Alembic
- Pricing Registry / commercial rule redesign
- Logo return template merge
- `git add -A`, stash, reset, clean, push, PR
- Unrelated dirty-tree paths
