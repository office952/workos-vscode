# ACM Face-Treatment Optical Catalog Closure — Allowlist

| Field | Value |
|-------|--------|
| Date | 2026-07-21 |
| Kickoff HEAD | `9bdcfaa8` (reconfirmed) |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Subject | Optical / plexiglas / illumination catalog closure Axis B |
| Decision | Owner GO — close honest commercial blockers; no invent rates |

## Commit sequence (allowlist only)

| # | Message |
|---|---------|
| 1 | `docs(qa): freeze ACM face-treatment optical catalog CP0 and shared map` |
| 2 | `feat(product-system): add face-treatment optical catalog resolution map` |
| 3 | `feat(product-system): scope optical and illumination commercial blockers` |
| 4 | `fix(product-system-ui): expose face-treatment commercial readiness and blockers` |
| 5 | `test(product-system): prove optical catalog partial close and CPP scenarios` |
| 6 | `docs(qa): finalize ACM face-treatment optical illumination catalog closure` |

## Allowed paths

### Backend

- `backend/services/acm_face_treatment_commercial_path_v1.py`
- `backend/services/acm_panel_pd_projection.py` (project catalog + UI summary fields only)
- `backend/tests/test_acm_face_treatment_commercial_path_v1.py`
- `backend/data/product_system/acp_face_treatment_registry_v1.py` (markers only if needed)
- `backend/data/product_system/acp_local_face_modules_v1.py` (markers only if needed)

### Frontend

- `frontend/src/features/product-system/AcmBoxedFaceTreatmentPanel.tsx`
- `frontend/src/features/product-system/AcmBoxedFaceTreatmentPanel.test.tsx`
- `frontend/src/features/product-system/ProductSystemTemplateDetailPanel.tsx` (mount/onChange only if needed; **no XOR**)

### Docs / QA / worklog

- `docs/qa/product-system-authoring-runtime-codesign-e2e/ACM_FACE_TREATMENT_OPTICAL_CATALOG_*`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/ACM_FACE_TREATMENT_OPTICAL_ILLUMINATION_CATALOG_CLOSURE_*`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/runtime/acm_face_treatment_optical_catalog_*`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/screenshots/acm-face-treatment-optical-catalog/**`
- `docs/worklog/realignment/2026-07-20_product_system_authoring_runtime_codesign_e2e_build.md` (section **ACM FACE-TREATMENT OPTICAL AND ILLUMINATION CATALOG CLOSURE** only)

## Forbidden

- XOR / dual-select / publication / new SKU / PI/CI/CT
- Inventing optical/LED/PSU rates; remapping volumetric or LIGHT-ROUTED into Axis B
- Broad pricing redesign; hourly commercial price; Alembic; Execution materialization
- `git add -A`, stash, reset, clean, push, PR
- Unrelated dirty-tree paths
