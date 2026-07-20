# Allowlist — Product System Authoring Continuation

| Field | Value |
|-------|--------|
| Date | 2026-07-20 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Kickoff HEAD | `e2f3fc9c6d5ddd247422fea65e094184fc643b21` |
| Rule | Stage **only** paths listed below per commit. Never `git add .` / `-A`. Never reset/stash/clean foreign dirty tree. |

## Kickoff confirmation (20 items)

| # | Item | Result |
|---|------|--------|
| 1 | Repo | `C:\w\psiso` |
| 2 | Branch | `feature/product-system-active-path-isolation-v1` (unchanged) |
| 3 | HEAD | `e2f3fc9` — **reconfirmed** |
| 4 | Dirty tree | ~360 entries — **preserved** |
| 5 | Prior commits | Foundation + build + closure + completion + external boundary kept |
| 6 | Boundary doc | `docs/architecture/artwork-understanding/2026-07-20_EXTERNAL_ARTWORK_ANALYSIS_OWNERSHIP.md` present |
| 7 | Runtime spine | Unchanged — PT/PD/Agg/Qty/Snap/Order/EP not reopened for formula |
| 8 | DB | Local `backend/dev.db`; create_all; no destructive migration |
| 9 | Routes | `/product-system/products`, `/product-system/products/:code`, `/product-system/blueprint-dossier` |
| 10 | UI baseline | NEEDS_POLISH preserved as start state |
| 11 | Figma | File `0CDPIuqoaZ1OQgNnvNyl1F`, page `91:2`, frames `91:3`…`91:100` |
| 12 | Allowlist | this file |
| 13 | Contract map | Family → PT → links (usage_mode + instance_schema) → Dossier → readiness → publication → runtime |
| 14 | Agents | A–G as needed; Lead freezes shared contracts first (CP0) |
| 15 | Checkpoints | CP0–CP6 |
| 16 | Test matrix | BE lifecycle/links/contracts/readiness; FE panels/routes; no formula reopen |
| 17 | PASS conditions | Separate verdicts; Aluminiu BLOCKED; no fake Publication ready for VL |
| 18 | Master plan | Continue existing — **no new Master Plan** |
| 19 | Worklog | living section PRODUCT SYSTEM AUTHORING CONTINUATION |
| 20 | Forbidden | CT table, PI/CI, Build 2, Aluminiu activate, pricing reopen, desktop transport, SVG analysis |

## Do not stage (foreign)

- Preexisting dirty under `docs/qa/*` other builds, intake-v6, segmented-background, utf8
- `.compound-engineering/**` preexisting research
- Unrelated `frontend/src/App.tsx` demo foreign unless inseparable PS route (preserve demo)
- `backend/tests/test_acm_boxed_mounting_standalone_offer_v1.py` foreign dirty
- Any path requiring Aluminiu activation or CostEngine reopen

## Build-owned paths

### Docs

- `docs/worklog/realignment/2026-07-20_product_system_authoring_runtime_codesign_e2e_build.md`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/AUTHORING_CONTINUATION_ALLOWLIST.md`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/AUTHORING_CONTINUATION_CP0_CONTRACT_MAP.md`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/AUTHORING_CONTINUATION_FINAL_REPORT.md`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/FIGMA_READY_STRUCTURE.md` (classification updates only)
- `docs/qa/product-system-authoring-runtime-codesign-e2e/screenshots/**` (continuation pack only)
- `docs/qa/product-system-authoring-runtime-codesign-e2e/runtime/**` (continuation evidence only)
- `docs/qa/product-system-authoring-runtime-codesign-e2e/UI_AUDIT_AUTHORING_CONTINUATION.md`

### Backend

- `backend/routers/product_template_module_links.py` (expose usage_mode / instance_schema_id; composition update fields)
- `backend/tests/test_product_template_module_links_composition_v1.py` (new)
- Existing publication/contract/readiness tests only if BUILD_REGRESSION

### Frontend

- `frontend/src/api/productTemplateModuleLinks.ts`
- `frontend/src/features/product-system/productSystemUnifiedCatalogTypes.ts`
- `frontend/src/features/product-system/ProductSystemTemplateDetailPanel.tsx`
- `frontend/src/features/product-system/TemplateCompositionAuthoringPanel.tsx` (+ test)
- `frontend/src/features/product-system/TemplateRuntimePreviewPanel.tsx` (+ test)
- `frontend/src/features/product-system/TemplateDualStatusChips.tsx` (+ test)
- `frontend/src/features/product-system/ComponentContractUsedByPanel.tsx` (mount/wire only if needed)
- `frontend/src/pages/BlueprintDossierStudio.tsx` (sticky footer + template deep-link)
- Related `*.test.tsx` / `*.test.ts` for above

## Commit groups (allowlist)

| Group | Scope |
|-------|--------|
| docs-cp0 | allowlist + contract map + worklog kickoff |
| shell-lifecycle | dual status + tab shell + readiness/publication tabs |
| composition-contracts | module link API exposure + composition authoring + contracts tab |
| dossier-studio | sticky Save→Validate→E2E→Publish + deep-link |
| runtime-preview | read-only PD preview tab |
| tests | BE/FE targeted tests |
| docs-qa | final report + UI audit + screenshots evidence |

## Stop conditions (abort if hit)

- ComponentTemplate table unavoidable
- Lifecycle unsafe / major publication schema
- Bridge cannot demote
- Destructive migration
- Aluminiu activation required for honest path
- Pricing / CostEngine change
- Build 2 / desktop transport / SVG analysis needed
- Inseparable dirty-tree conflict
- Figma fundamentally different flow
