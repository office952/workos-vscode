# ACM / Bond Face-Treatment Commercial Path — Allowlist

| Field | Value |
|-------|--------|
| Date | 2026-07-21 |
| Kickoff HEAD | `290a4540` (reconfirmed) |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Subject | Axis B face-treatment commercial path on ACM boxed root |
| Decision | Owner GO Axis B — FACE-TREATMENT LOCAL COMMERCIAL PATH FIRST |

## Commit sequence (allowlist only)

| # | Message |
|---|---------|
| 1 | `docs(qa): freeze ACM face-treatment commercial path CP0` |
| 2 | `feat(product-system): add ACM face-treatment commercial path domain` |
| 3 | `feat(product-system): wire face treatments through PT PD Aggregate readiness` |
| 4 | `fix(product-system-ui): expose Bond ACM face-treatment section` |
| 5 | `test(product-system): prove face-treatment commercial path coexistence` |
| 6 | `docs(qa): finalize ACM face-treatment commercial path evidence` |

## Allowed paths

### Backend

- `backend/data/product_system/acp_face_treatment_registry_v1.py` (commercial markers only if needed)
- `backend/data/product_system/acp_local_face_modules_v1.py` (commercial markers only if needed)
- `backend/services/acm_face_treatment_commercial_path_v1.py` (**new**)
- `backend/services/acp_local_face_module_service.py` (commercial projection hooks only if needed)
- `backend/services/acm_quote_input_helpers.py` (preserve face-treatment markers)
- `backend/services/acm_panel_pd_projection.py` (project face treatments into PD values)
- `backend/services/product_definition_builder_service.py` (ACM standalone + face-treatment projection only)
- `backend/services/product_truth_job_confirm_service.py` (pin `acm_face_treatments` bag only)
- `backend/services/product_e2e_readiness_service.py` (face-treatment readiness check only)
- `backend/services/product_aggregate_service.py` (no double sheet — face-treatment projection only if needed)
- `backend/tests/test_acm_face_treatment_commercial_path_v1.py` (**new**)
- `backend/tests/test_acp_face_treatment_authority_v1.py` (narrow extensions)
- `backend/tests/test_acp_local_face_modules_v1.py` (narrow extensions)
- `backend/tests/test_acm_boxed_support_composition_v1.py` (orthogonality only if needed)

### Frontend

- `frontend/src/features/product-system/AcmBoxedFaceTreatmentPanel.tsx` (**new**)
- `frontend/src/features/product-system/AcmBoxedFaceTreatmentPanel.test.tsx` (**new**)
- `frontend/src/features/product-system/ProductSystemTemplateDetailPanel.tsx` (mount panel only)
- `frontend/src/features/product-system/AcmBoxedAppliedContentPanel.tsx` (**do not change XOR**; touch only if import adjacency required)

### Docs / QA / worklog

- `docs/qa/product-system-authoring-runtime-codesign-e2e/ACM_FACE_TREATMENT_COMMERCIAL_PATH_*`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/runtime/acm_face_treatment_commercial_*`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/screenshots/acm-face-treatment-commercial/**`
- `docs/worklog/realignment/2026-07-20_product_system_authoring_runtime_codesign_e2e_build.md` (section **ACM / BOND FACE-TREATMENT COMMERCIAL PATH** only)

## Forbidden

- XOR demote / dual letters+logo select
- Creating applied_content volumetric composition links
- New panel / composite root SKU; LIGHT-ROUTED revival
- Publishing ACM / VL / logo
- Inventing optical/LED/PSU prices or catalogs
- Alembic / PI / CI / ComponentTemplate tables
- SVG/DWG/DXF parsers / desktop analysis
- `git add -A`, stash, reset, clean, push, PR
- Unrelated dirty-tree paths
