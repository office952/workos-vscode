# Live segmented ACM/ACP background E2E verification

- **Date:** 2026-07-19
- **Branch:** `feature/product-system-active-path-isolation-v1`
- **HEAD initial:** `41129b6` (`feat(product-system): wire segmented background confirmation`)
- **Verdict:** PASS (live Playwright 4/4; narrow runtime fixes included)
- **Direction score:** 92/100%

## Runtime commands

- Backend (current schema): `uvicorn main:app --host 127.0.0.1 --port 8002` (venv + injected env)
- Frontend: `VITE_API_BASE_URL=http://127.0.0.1:8002` → Vite `--host 127.0.0.1 --port 3000`
- Playwright:

```powershell
cd frontend
$env:PW_SKIP_WEB_SERVER='1'
$env:PW_BACKEND_URL='http://127.0.0.1:8002'
$env:PW_BASE_URL='http://127.0.0.1:3000'
npx pnpm@8.10.0 exec playwright test e2e/intake-v6-segmented-background-live-e2e.spec.ts --workers=1
```

API base: `http://127.0.0.1:8002`  
Intake route: `/intake-v6/{workspaceId}/operator`  
Persistence: `PUT /api/v1/intake-v6/workspaces/{id}/finish-setup`  
ProductDefinition: `GET /api/v1/product-system/product-definition/TPL-VOLUMETRIC-LETTERS_v2?workspace_id=`  
ProductAggregate HTTP: `GET /api/v1/product-system/aggregate/...` (shell aggregate; segmented projection is embedded on PD as `canonical_values.segmented_background_aggregate_projection`)

## Real SVG fixtures

| File | Path |
|------|------|
| Basic | `C:\Users\offic\Desktop\fisiere-teste-svg\litere-cu-fundal-acm-segmentat.svg` |
| Crossing | `C:\Users\offic\Desktop\fisiere-teste-svg\litere-cu-fundal-acm-segmentat-litera-peste-imbinare.svg` |
| Distributed | `C:\Users\offic\Desktop\fisiere-teste-svg\situatie-3.svg` |

## Sample workspace IDs (latest green run)

| Case | workspace id | code |
|------|--------------|------|
| CASE 1 | `d04b06ce-0448-4e25-96bc-34f421f6a171` | `IV6-31973A78` |
| CASE 2 | see `runtime/case2_workspace.json` | live-seg-cross |
| CASE 3 | see `runtime/case3_workspace.json` | live-seg-sit3 |
| Reject/blockers | see `runtime/case_reject_workspace.json` | live-seg-reject-block |

## Walkthrough summary

1. Create analyzer_first workspace → open operator → import Desktop SVG.
2. Assign Contur suport → analyzer proposes multi-panel → confirm layer roles → Review → Montaj.
3. Proposal shows panels/IDs/order/dimensions; Confirm enabled (no auto-confirm).
4. Confirm → immediate finish-setup PUT → status CONFIRMED → reload retains state.
5. PD `canonical_values.segmented_background` CONFIRMED; aggregate projection on PD with empty materials/processes/task_rules and `future_task_intent_authority=INFORMATIONAL_ONLY`.
6. CASE 2: no auto-centroid binding → inject applied crossing via finish PUT (documented supported path) → UI two-stage message → Confirm → CONFIRMED with `TWO_STAGE_JOINT_CROSSING`.
7. CASE 3: situatie-3 calm — no generic geometry panic.
8. Reject → REJECTED persists across reload; PD segmented absent.
9. Cutout/insert CONFIRMED writes → HTTP 422; UI Confirm disabled with Romanian blockers.

## Proven defects (live) + fixes

1. **Ghost :8001** stale OpenAPI stripped `segmented_background` → use :8002 + `VITE_API_BASE_URL` honor in `frontend/src/lib/config.ts`.
2. **Sparse finish wipe** after Contur suport → FE `segmentedBackgroundRef` + BE `coalesce_segmented_background_for_finish`.
3. **Review hydrate gap** dropped `segmented_background` → `finishFromPayload` + sync signature.
4. **Confirm/reject debounced only** left UI Confirmat while server still PROPOSED → immediate `persistFinishSetupState` on segmented onPatch (same pattern as mounting_scope).

## Evidence

- Screenshots: `docs/qa/segmented-background-live-e2e-2026-07-19/screenshots/` (`01`–`11`)
- Runtime JSON: `docs/qa/segmented-background-live-e2e-2026-07-19/runtime/`
  - Key: `case1_finish_after_confirm.json`, `case1_pd_after.json`, `case2_finish_after_confirm.json`, `case_cutout_422.json`, `case_insert_422.json`, `case_reject_finish.json`

## Tests

| Command | Result |
|---------|--------|
| `pytest tests/test_acm_segmented_background_confirmation_path_v1.py tests/test_acm_segmented_background_v1.py -q` | 25 passed |
| `vitest` segmentedBackground + panel + liveCandidates | 11 passed |
| Playwright live E2E (Desktop SVGs, :8002) | **4 passed** |

## Remaining gaps / ops notes

- Windows may still host a ghost listener on `:8001` — keep FE pointed at current schema port via `VITE_API_BASE_URL`.
- Dedicated `/product-system/aggregate` response does not yet surface segmented projection; authority for Aggregate shape is PD `segmented_background_aggregate_projection`.
- Applied letter crossing still requires operator/API binding injection (no automatic centroid binding).
- Cutout/insert UI blockers use injected PROPOSED bindings (SVGs do not contain those constructions natively).

## Next recommended build

**Ghost-listener / API-base hygiene for local Intake V6** — ensure default local stack cannot silently attach to a stale `:8001` process (port ownership + startup banner). No pricing/Execution.
