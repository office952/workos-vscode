# Wave 4 — `/modules` accuracy

Source: `PRESENT_SYSTEMS` + `PRESENT_SUPPORT_SYSTEMS` in `currentTruthControlCenter.ts`. Runtime: admin L+D; sales/manager/operator denied.

| NAME | ROLE | OWNER | SOURCE_OF_TRUTH | RUNTIME_STATUS | Class vs code |
|------|------|-------|-----------------|----------------|---------------|
| Catalog produse | reusable language | Product System | templates/registry | PARTIAL | ACCURATE (honest PARTIAL) |
| Intake V6 | capture workspace | Sales/operator comercial | workspace payload | CONFIRMAT | ACCURATE with caveats |
| Product Compiler · Definiție | compile config | Product Compiler | preview API | PARTIAL | PARTIAL — no dedicated UI; verifyRoute `/intake-v6` |
| Product Compiler · Graf | technical graph | Product Compiler | aggregate API | PARTIAL | PARTIAL — verifyRoute `/product-system` |
| Pricing / Commercial | money | Commercial Pricing | CPP | — | ACCURATE as claim |
| Quote / Order snapshots | freeze | Commercial | snapshots | — | ACCURATE |
| Plan / Reality / Post-Job | execution | Execution | EP / reality | — | PARTIAL — Atelier/operator/tablet are Execution projections (not missing systems) |
| Active/Sold scope | scope | PD | compile_active_scope | — | PARTIAL |
| Blueprint Dossier | dossier | PS | dossier | — | ACCURATE as support |
| MachineRun | machine work | Execution | resource-state | — | ACCURATE support; list empty |
| Capacity Stage 1 | capacity | Capacity | — | inactive | ACCURATE inactive |
| CostEngine / QuoteWizard | legacy | — | — | LEGACY | PARTIAL vs Settings still exposing cost UI |

**MODULES_PAGE_ACCURACY = PARTIAL**

Live pages not named on the map (`/shop-floor`, `/operator`, `/tablet`, dashboard, clients, HR) are **projections/pages**, not 12 missing Level-1 systems. See [`WAVE_4_UNREGISTERED_SYSTEM_RECONCILIATION.md`](./WAVE_4_UNREGISTERED_SYSTEM_RECONCILIATION.md) (`UNREGISTERED_SYSTEM_COUNT_FINAL = 0`).

Repo freeze `CURRENT_WORKOS_FROZEN_AS_REFERENCE` is **not** on this page (UNDERDOCUMENTED).
