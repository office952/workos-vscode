# Allowlist manifest — Product System Authoring + Runtime Co-Design E2E

| Field | Value |
|-------|--------|
| Date | 2026-07-20 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Base HEAD | `6a1c1d1` |
| Rule | Stage **only** paths listed below per commit. Never `git add .`. Never touch foreign dirty files except additive non-destructive merges that preserve foreign intent. |

## Do not stage (foreign / unrelated dirty)

- `backend/services/product_template_availability_service.py` — unless publication offerability patch preserves ACM dual-role filter (document in commit)
- `frontend/src/App.tsx` — demo route foreign; only stage if PS route addition is inseparable and demo import preserved
- All preexisting `docs/qa/*` screenshots/runtime from other builds unless this build owns a new evidence folder
- `.compound-engineering/**` preexisting research
- Unrelated intake-v6 / segmented-background / utf8 worklogs

## Build-owned paths (expected)

### Docs

- `docs/worklog/realignment/2026-07-20_product_system_authoring_runtime_codesign_e2e_build.md`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/**`

### Backend — publication lifecycle + readiness gate

- `backend/models/product_templates.py`
- `backend/models/product_template_module_links.py` (usage_mode / instance_schema_id additive)
- `backend/schemas/product_template_publication.py`
- `backend/schemas/product_template_component_contract.py`
- `backend/services/product_template_publication_service.py`
- `backend/services/product_template_component_contract_service.py`
- `backend/routers/product_system_publication.py`
- `backend/routers/product_system_component_contracts.py`
- `backend/main.py` (router include only)
- `backend/tests/test_product_template_publication_v1.py`
- `backend/tests/test_product_template_component_contracts_v1.py`
- `backend/tests/test_product_e2e_readiness_v1.py` (gate assertions only if needed)
- `backend/alembic/versions/*publication*` (only if required; prefer create_all + auto column repair)

### Backend — job truth / snapshot (build-caused fixes only)

- `backend/services/product_truth_job_confirm_service.py`
- `backend/services/intake_v6_workspace_service.py`
- `backend/scripts/*product_system_authoring*` / evidence scripts under qa folder
- Snapshot services **only** if this build introduced a regression

### Frontend

- `frontend/src/api/productTemplatePublication.ts`
- `frontend/src/api/productTemplateComponentContracts.ts`
- `frontend/src/features/product-system/ProductTemplatePublicationPanel.tsx`
- `frontend/src/features/product-system/ComponentContractUsedByPanel.tsx`
- `frontend/src/features/product-system/ProductE2EReadinessPanel.tsx` (publish gate UX)
- `frontend/src/features/product-system/ProductSystemTemplateDetailPanel.tsx`
- `frontend/src/features/product-system/TemplateLifecycleReadinessPanel.tsx`
- `frontend/src/pages/BlueprintDossierStudio.tsx` (studio shell / sticky publish)
- `frontend/src/pages/ProductSystem.tsx` (wire panels only)
- Related `*.test.tsx` / `*.test.ts` for above

### Evidence

- `docs/qa/product-system-authoring-runtime-codesign-e2e/screenshots/**`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/runtime/**`

## Commit grouping

| Commit group | Vertical |
|--------------|----------|
| CP0 docs | worklog + allowlist |
| CP1+CP5 | publication + readiness hard gate |
| CP2 | component contracts |
| CP3 | dossier studio shell |
| CP4 | job truth HTTP proof |
| CP6 | snapshot classify / build fixes |
| CP7 | screenshots + final worklog |

## Router registration rule

`backend/main.py` changes limited to `include_router` for new publication/component-contract routers.
