# VOLUM ALUMINIU Controlled Activation — Allowlist

| Field | Value |
|-------|--------|
| Date | 2026-07-21 |
| Kickoff HEAD | `6dcf7bc1` |
| Subject | `TPL-VOLUM-ALUMINIU_v1` activate-only |

## Commit sequence (allowlist only)

| # | Message |
|---|---------|
| 1 | `chore(product-system): activate canonical aluminium return component` |
| 2 | `test(product-system): prove activation identity and calculation invariants` |
| 3 | `docs(qa): record controlled activation and parent readiness evidence` |

## Allowed paths

### Backend

- `backend/scripts/activate_tpl_volum_aluminiu_v1.py`
- `backend/seeds/seed_tpl_volumetric_letters_v2.py`
- `backend/seeds/seed_tpl_volumetric_letters_component_modules_v1.py`
- `backend/services/volum_aluminiu_component_contract.py`
- `backend/services/product_e2e_readiness_service.py`
- `backend/tests/test_volum_aluminiu_controlled_activation_v1.py`

### Docs / QA

- `docs/qa/product-system-authoring-runtime-codesign-e2e/VOLUM_ALUMINIU_CONTROLLED_ACTIVATION_*`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/volum-aluminiu-activation/**`
- `docs/worklog/realignment/2026-07-20_product_system_authoring_runtime_codesign_e2e_build.md`

## Forbidden

- Parent / child publish transitions
- Logo-return activation
- Schema migrations / Alembic
- Pricing / formula / module-link relation edits
- `git add -A`, stash, reset, clean, push, PR
- Unrelated dirty-tree paths
