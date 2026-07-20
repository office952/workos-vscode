# REAL PRODUCT CONFIGURATION — Allowlist

| Field | Value |
|-------|--------|
| Date | 2026-07-20 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Kickoff HEAD | `5382525` (reconfirmed) |
| Dirty tree | ~360 — **preserved**; allowlist-only staging |

## Kickoff confirmation

1. Branch locked — no checkout/switch  
2. HEAD `5382525` reconfirmed  
3. No Aluminiu activation  
4. No CT table / PI / CI / Build 2 / pricing / Execution materialization  
5. No SVG/DWG/DXF parse or desktop transport  
6. No force-publish  
7. No git reset/stash/clean/add -A  

## Allowlist paths

### Config / seed

- `backend/seeds/seed_tpl_volumetric_letters_component_modules_v1.py`
- `backend/seeds/seed_tpl_volumetric_letters_v2.py` (Aluminiu inactive preserve only)
- `backend/scripts/seed_sync_all.py` (pipeline entry)

### Contracts / aggregate / readiness surface

- `backend/services/product_aggregate_service.py` (CHILD_TEMPLATE_MINI_MODULE map)
- `backend/services/product_template_component_contract_service.py`
- `backend/schemas/product_template_component_contract.py`

### UI (System Link Check only — config visibility)

- `frontend/src/features/product-system/ProductE2EReadinessPanel.tsx`
- `frontend/src/features/product-system/ProductE2EReadinessPanel.test.tsx`

### Tests

- `backend/tests/test_vl_real_product_configuration_v1.py`
- `backend/tests/test_product_aggregate_volumetric_v2.py` (fixture + assertion alignment)

### Docs / evidence

- `docs/qa/product-system-authoring-runtime-codesign-e2e/REAL_PRODUCT_CONFIGURATION_ALLOWLIST.md`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/REAL_PRODUCT_CONFIGURATION_FINAL_REPORT.md`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/runtime/vl_real_product_config_system_link_check.json`
- `docs/worklog/realignment/2026-07-20_product_system_authoring_runtime_codesign_e2e_build.md` (§ PRODUCT SYSTEM REAL PRODUCT CONFIGURATION)

## Commit groups (planned)

1. `feat(product-system): complete VL component module composition contracts`
2. `feat(product-system-ui): System Link Check status table on readiness`
3. `test(product-system): VL real product configuration proofs`
4. `docs(qa): VL real product configuration report + worklog`
