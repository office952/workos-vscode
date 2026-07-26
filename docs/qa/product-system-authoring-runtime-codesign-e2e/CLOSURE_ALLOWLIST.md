# Closure allowlist — FINAL CLOSURE GATE

| Field | Value |
|-------|--------|
| Date | 2026-07-20 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Confirmed HEAD at kickoff | `705a701a6e48f2bee1f638e44031f32f6d19d751` |
| Rule | Stage **only** paths listed below. Never `git add .` / reset / stash / clean. Dirty tree (~361) preserved. |

## Kickoff confirmation (20 items)

| # | Item | Result |
|---|------|--------|
| 1 | Repo | `C:\w\psiso` |
| 2 | Branch | `feature/product-system-active-path-isolation-v1` |
| 3 | HEAD | `705a701` (full `705a701a6e48f2bee1f638e44031f32f6d19d751`) |
| 4 | Build `034dbea` | CP0 docs + allowlist + Figma-ready + proof script + FINAL_REPORT |
| 5 | Build `e50f99b` | publication lifecycle + component contracts BE |
| 6 | Build `b0560bc` | publication + contract UI in PS + dossier studio |
| 7 | Build `a10efeb` | record commit SHAs in worklog/report |
| 8 | Build `705a701` | include HEAD SHA in FINAL_REPORT |
| 9 | Foundation kept | `ef349ef`, `136f38b`, `70b2fdf`, `6a1c1d1` |
| 10 | Dirty tree | status short **361**; staged **0**; modified **28**; untracked **~1015** |
| 11 | Ports canonical | BE **8000**, FE **3000** (AGENTS.md) |
| 12 | Live stack observed | BE **8011** + FE **3011** healthy with `dev.db`; FE also **3000** up; BE **8000** down at kickoff |
| 13 | DB path | `C:\w\psiso\backend\dev.db` (~28.8 MB, mtime 2026-07-20 21:39) |
| 14 | Fixture preference | `TPL-VOLUMETRIC-LETTERS_v2` + ACM boxed if safe; **never** activate `TPL-VOLUM-ALUMINIU_v1` |
| 15 | Prior allowlist | `ALLOWLIST_MANIFEST.md` (build paths) |
| 16 | Worklog | `docs/worklog/realignment/2026-07-20_product_system_authoring_runtime_codesign_e2e_build.md` |
| 17 | Prior report | `docs/qa/product-system-authoring-runtime-codesign-e2e/FINAL_REPORT.md` (PARTIAL 78%) |
| 18 | Current failures (pre-closure) | Live HTTP confirm→DB thin; screenshot pack thin; Figma PS FINAL frames absent |
| 19 | Dependency graph | CP-A → CP-B → CP-C → CP-D → CP-E; CP-F parallel after A; CP-G/H after UI surfaces exist |
| 20 | PASS conditions | Full DoD: HTTP→DB→reload→compilers→qty→freeze→Order→EP→Readiness→UI→screenshots→tests; separate BUILD vs TEMPLATE PUBLICATION |

## Closure-owned paths (may edit / stage)

### Docs / evidence (always)

| Path | Why | Foreign risk | Closure portion | Mixing avoided |
|------|-----|--------------|-----------------|----------------|
| `docs/worklog/realignment/2026-07-20_product_system_authoring_runtime_codesign_e2e_build.md` | Living worklog FINAL CLOSURE GATE | none if only this file | append section | append-only |
| `docs/qa/product-system-authoring-runtime-codesign-e2e/**` | Report, allowlist, screenshots, runtime proofs | none (build-owned folder) | all closure evidence | stay in folder |
| This file `CLOSURE_ALLOWLIST.md` | Gate allowlist | none | new | n/a |

### Backend — build-caused closure fixes only

| Path | Why | Foreign risk | Closure portion | Mixing avoided |
|------|-----|--------------|-----------------|----------------|
| `backend/services/product_truth_job_confirm_service.py` | HTTP confirm persist/reload gaps | check diff before edit | confirm persist only | stop if foreign hunks inseparable |
| `backend/routers/intake_v6_workspaces.py` | confirm-job / job-status route only | likely foreign dirty elsewhere | route wiring only | patch only confirm endpoints |
| `backend/schemas/product_e2e_readiness.py` | Dual axes fields (build_closure / template_publication) | clean companion | contract only | no redesign |
| `backend/services/product_e2e_readiness_service.py` | BUILD vs TEMPLATE publication distinction | stop if foreign | readiness verdict labels | surgical |
| `backend/services/product_template_publication_service.py` | publish 409 honesty | committed clean | gate only | no redesign |
| `backend/tests/test_product_truth_job_confirm_v1.py` | persist/reload proofs | clean in HEAD | add assertions | no weaken |
| `backend/tests/test_product_e2e_readiness_v1.py` | aluminiu BLOCKED + dry_run | clean in HEAD | closure cases | no activate aluminiu |
| `backend/tests/test_product_template_publication_v1.py` | publish gate | clean | closure | no weaken |
| `backend/tests/test_active_scope_snapshot_freeze.py` | freeze from pin | clean | classify/fix build-caused only | no weaken |
| New under `docs/qa/.../runtime/*` | live HTTP proof scripts | none | evidence | n/a |

### Frontend — UI honesty + screenshots only

| Path | Why | Foreign risk | Closure portion | Mixing avoided |
|------|-----|--------------|-----------------|----------------|
| `frontend/src/features/product-system/ProductTemplatePublicationPanel.tsx` | active≠published | clean in HEAD | labels | no redesign |
| `frontend/src/features/product-system/ProductE2EReadinessPanel.tsx` | BUILD PASS vs TEMPLATE BLOCKED | may need check | banner distinction | surgical |
| `frontend/src/features/product-system/*.test.tsx` | UI honesty tests | clean | closure | no weaken |
| `frontend/src/pages/BlueprintDossierStudio.tsx` | sticky footer honesty | committed; check WT | labels only | stop if foreign |
| `frontend/src/pages/ProductSystem.tsx` | wire only | **DIRTY foreign likely** | stop if inseparable | do not stage foreign |

## Explicitly forbidden to stage

- Entire dirty tree / `git add .`
- `frontend/src/App.tsx` (foreign demo route)
- Unrelated intake-v6 / ACM soak / segmented-background / utf8 docs
- `.compound-engineering/**`
- CostEngine / pricing redesign / aluminiu activation
- Any PI/CI / ComponentTemplate table / Build 2 / ACM Cassetted Logo activation

## Commit grouping (closure)

| Group | Intent |
|-------|--------|
| docs-closure-allowlist | this file + worklog kickoff section |
| product-truth-persist | CP-A live HTTP→DB proof (+ fix if needed) |
| quantity-eic / compilers | CP-B/C only if build-caused gap |
| snapshot-freeze | CP-D only if build-caused |
| ui-readiness-states | CP-F/G honesty banners |
| e2e-tests-evidence | tests + screenshots + FINAL_REPORT |

## Stop condition

If a required file has inseparable foreign working-tree changes: **STOP**, report exact conflict path + hunk summary. Do not reset/stash/checkout-over.
