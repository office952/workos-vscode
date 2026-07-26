# VL Pre-Publication E2E Proof — Allowlist

| Field | Value |
|-------|--------|
| Date | 2026-07-21 |
| Kickoff HEAD | `520f3f01` |
| Subject | Close six NOT_TESTED for `TPL-VOLUMETRIC-LETTERS_v2` without publishing |

## Commit sequence (allowlist only)

| # | Message |
|---|---------|
| 1 | `test: intake through quantity` |
| 2 | `test: CPP EIC snapshot` |
| 3 | `test: order EP preview boundaries` |
| 4 | `fix: evidence-backed E2E defects only` (skip if empty) |
| 5 | `docs(qa): finalize pre-publication proof` |

## Allowed paths

### Backend

- `backend/services/product_e2e_readiness_service.py`
- `backend/tests/test_vl_pre_publication_e2e_proof_v1.py`
- `backend/tests/test_product_e2e_readiness_v1.py` (runtime assertion updates only — if touched)

### Docs / QA / worklog

- `docs/qa/product-system-authoring-runtime-codesign-e2e/VL_PRE_PUBLICATION_E2E_*`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/vl-pre-publication-e2e/**`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/runtime/vl_pre_publication_*`
- `docs/worklog/realignment/2026-07-20_product_system_authoring_runtime_codesign_e2e_build.md`

## Forbidden

- Parent / child publish transitions
- Logo-return activation
- Schema migrations / Alembic
- Pricing / formula / module-link relation edits
- Live customer Quote/Order mutation
- Execution plan materialization
- SVG/DWG/DXF parse / Build 2
- `git add -A`, stash, reset, clean, push, PR
- Unrelated dirty-tree paths
