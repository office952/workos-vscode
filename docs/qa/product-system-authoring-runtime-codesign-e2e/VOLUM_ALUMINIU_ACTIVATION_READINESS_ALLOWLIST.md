# VOLUM ALUMINIU Activation Readiness Closure — Allowlist

| Field | Value |
|-------|--------|
| Date | 2026-07-21 |
| Kickoff HEAD | `a385f156` |
| Convergence map | `VOLUM_ALUMINIU_ACTIVATION_READINESS_CONVERGENCE_MAP.md` |

## Commit sequence (allowlist only)

| # | Message |
|---|---------|
| 1 | `feat(product-system): converge aluminium return canonical identity mappings` |
| 2 | `feat(product-system): converge CPP product-total on confirmed perimeter / control quote_geometry bridge` |
| 3 | `test(product-system): prove identity and geometry equivalence` |
| 4 | `docs(qa): activation readiness closure evidence` |

## Allowed paths

### Backend

- `backend/services/volum_aluminiu_component_contract.py`
- `backend/services/volum_aluminiu_quantity_ownership.py`
- `backend/services/volum_aluminiu_separate_calc_preview_service.py`
- `backend/services/commercial_price_proposal_service.py`
- `backend/services/estimated_internal_cost_service.py`
- `backend/services/letters_commercial_measurement_service.py`
- `backend/services/product_aggregate_service.py`
- `backend/services/product_e2e_readiness_service.py`
- `backend/data/mini_module_registry_volumetric_v2.py`
- `backend/tests/test_volum_aluminiu_identity_geometry_convergence.py`

### Docs / QA

- `docs/qa/product-system-authoring-runtime-codesign-e2e/VOLUM_ALUMINIU_ACTIVATION_READINESS_*`
- `docs/worklog/realignment/2026-07-20_product_system_authoring_runtime_codesign_e2e_build.md`

## Forbidden

- Activation / publish transitions
- Schema migrations / Alembic
- Pricing Registry / commercial formula redesign
- `git add -A`, stash, reset, clean, push, PR
- Unrelated dirty-tree paths
