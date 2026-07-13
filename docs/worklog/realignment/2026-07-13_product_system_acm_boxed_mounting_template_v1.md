# Product System ACM Boxed Mounting Template v1

**Task:** PRODUCT_SYSTEM_ACM_BOXED_MOUNTING_TEMPLATE_V1  
**Date:** 2026-07-13  
**HEAD before:** 3382e89  
**Canonical template code:** `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`

## Owner decision (locked)

ACM casetat MUST be a separately offerable Product System template, internally composed from reusable casetted components (face, returns, fasteners), selectable as linked child from Intake V6 mounting preparation, independently calculable, offerable, snapshot-safe, and executable.

## Phases

| Phase | Scope | Status |
|-------|-------|--------|
| 1 | Worklog + seed template/dossier/module_link | in progress |
| 2 | Policy, availability, mini-module, pricing registry | pending |
| 3 | mounting_solution_service + linked module input | pending |
| 4 | Frontend Intake V6 selector + ACM config fields | pending |
| 5 | Tests (pytest + vitest) | pending |
| 6 | Playwright + QA evidence | pending |
| 7 | Commit + delivery report | pending |

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
