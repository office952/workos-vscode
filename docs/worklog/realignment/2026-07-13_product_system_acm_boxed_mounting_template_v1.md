# Product System ACM Boxed Mounting Template v1

**Task:** PRODUCT_SYSTEM_ACM_BOXED_MOUNTING_TEMPLATE_V1
**Realignment:** PRODUCT_SYSTEM_ACM_BOXED_MOUNTING_PLAYWRIGHT_SPEC_REALIGNMENT_V1
**Date:** 2026-07-13
**HEAD before:** 5d7bbc5
**Canonical template code:** `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`

## Owner decision (locked)

ACM casetat MUST be a separately offerable Product System template, internally composed from reusable casetted components (face, returns, fasteners), selectable as linked child from Intake V6 mounting preparation, independently calculable, offerable, snapshot-safe, and executable.

## Phases

| Phase | Scope | Status |
|-------|-------|--------|
| 1 | Worklog + seed template/dossier/module_link | done |
| 2 | Policy, availability, mini-module, pricing registry | done |
| 3 | mounting_solution_service + linked module input | done |
| 4 | Frontend Intake V6 selector + ACM config fields | done |
| 5 | Tests (pytest + vitest) | done — 21 pytest + 9 vitest PASS |
| 6 | Playwright + QA evidence | realigned — official spec mirrors `capture-evidence.mjs` (IR-MRI01769 operator route, legacy bucket, PUT helpers) |
| 7 | Commit + delivery report | pending realignment closeout |

## Missing owner rates (honest — do not invent)

| Code | Basis | Notes |
|------|-------|-------|
| PANEL_CUTTING | workcenter | CUT_ACM_PANEL |
| ASSEMBLY | workcenter | FOLD_CASSETTE, MOUNT_ACM_PANEL |
| MAT-SURUBURI-GEN | material | comp_mounting_fasteners |
| MAT-ACM-BOND-4MM | material | needs_review — 3MM confirmed 15 EUR/mp |
| V_GROOVE_ROUTER | workcenter | basis mismatch vs perimeter formula |

## Boundary

- v1 scope: casetted components 1–3 from inactive `TPL-ACM-CASSETTED-PANEL` slice
- Do NOT activate `TPL-ACP-LIGHT-ROUTED`, `TPL-COMP-LETTER-MOUNTING_v1`, or full `TPL-ACM-CASSETTED-PANEL` as mounting solution
- Metal premount regression must pass

## Playwright realignment (2026-07-13)

| Mismatch | Before | After |
|----------|--------|-------|
| Product System route | `?template=` deep link | `/product-system` bare + testids |
| Intake route | `/intake-v6/{uuid}` | `/intake-v6/IR-MRI01769/operator` |
| Catalog bucket | implicit candidate | filter-all + expand `legacy-shared-modules` |
| Montaj tab | skipped | `gotoMontajTab` helper |
| Flow B | env uuid + bare selector | `preparation_only` PUT + ACM/metal PUT helpers |
| Wait strategy | networkidle (hang) | `domcontentloaded` for product-system |

Official spec: `frontend/e2e/product-system-acm-boxed-mounting-template-v1.spec.ts`
Evidence capture script (unchanged): `docs/qa/product-system-acm-boxed-mounting-template-v1/capture-evidence.mjs`
