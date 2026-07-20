# FINAL COMPLETION GATE — allowlist

| Field | Value |
|-------|--------|
| Date | 2026-07-20 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Kickoff HEAD | `1bad731e3d60c344733175667e7c4da535d07644` |
| Prior closure SHAs | `2e77e7c`, `ed3605e`, `f593cb7`, `670a4e2`, `b8a4c0a`, `2ed6b01`, `705a701`, `a10efeb`, `b0560bc`, `e50f99b`, `034dbea` + foundation `ef349ef`, `136f38b`, `70b2fdf`, `6a1c1d1` |
| Rule | Stage **only** paths below. Never reset/stash/clean/`git add .`. |

## Kickoff reconfirm

| # | Item | Result |
|---|------|--------|
| 1 | Repo | `C:\w\psiso` |
| 2 | Branch | `feature/product-system-active-path-isolation-v1` |
| 3 | HEAD | `1bad731` (reported closure tip `2e77e7c` superseded by docs commits through `1bad731`) |
| 4 | Dirty tree | preserved (~360+ unrelated) |
| 5 | Ports | Canonical BE **8001** / FE **3000**; live BE **8000** has publication/e2e routes; live BE **8001** stale (404 on publication) |
| 6 | Already DONE kept | HTTP confirm, DB persist, revision/hash, idempotency, stale, 409, Snap freeze, Order, EP, Readiness no-write, BUILD vs TEMPLATE, Figma PROPOSED `91:2` |

## Allowed paths

### Provenance + Quantity + EIC (commits 1–2, 4)

- `backend/schemas/product_aggregate.py`
- `backend/schemas/product_definition.py`
- `backend/schemas/commercial_measurement_contract.py`
- `backend/services/product_truth_job_confirm_service.py`
- `backend/services/letter_group_instance_authority.py`
- `backend/services/letters_commercial_measurement_service.py`
- `backend/services/product_definition_builder_service.py`
- `backend/services/product_aggregate_workspace_composition_service.py`
- `backend/services/product_aggregate_explicit_composition_service.py`
- `backend/services/intake_v6_quote_snapshot_v2_service.py`
- `backend/services/estimated_internal_cost_service.py`
- `backend/tests/test_product_truth_revision_quantity_convergence_v1.py`

### UI mount (commit 3)

- `frontend/src/features/product-system/ProductSystemTemplateDetailPanel.tsx`
- Related panel tests only if touched (existing panel tests unchanged)

### Docs / evidence (commit 5)

- `docs/worklog/realignment/2026-07-20_product_system_authoring_runtime_codesign_e2e_build.md`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/**`

## Proxy finding (no vite default change)

Canonical contract remains BE **8001**. FE3000→8001 publication 404 is **ENVIRONMENT_FAILURE** (stale process on 8001). Current code serves publication on **8000**. Fix: restart BE on 8001 with current tree, or launch FE with `BACKEND_PORT=8000`. Do **not** flip vite default to 8000 (breaks `canonical_startup_contract.test.mjs`).

## Forbidden

PI/CI, CT table, Build 2, aluminiu activation, CostEngine redesign, Execution materialization, push/PR, dirty-tree bulk stage.
