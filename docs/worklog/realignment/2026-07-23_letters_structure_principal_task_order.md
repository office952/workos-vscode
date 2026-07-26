# Letters structure — principal task order on cards

**Date:** 2026-07-23  
**Status:** display SoT on Product System structure detail pages

## Clarificare

- Cele **4 carduri** (Vizual față · Volum · Capac spate · Sistem LED) = **componente**.
- **Taskurile** = cum obții componentele.
- SoT afișare: `frontend/src/features/product-system/lettersStructurePrincipalTaskOrder.ts`
- UI: panou «Cum obții · ordine taskuri» pe fiecare `Letters*StructureDetailPage`.

## Scope

- Litere, **fără suport comun**, **fără emblemă**.
- Nu ExecutionPlan / CostEngine / Intake runtime.

## Cum obții (principal)

| Componentă | Taskuri principale |
|------------|-------------------|
| Vizual față | prep vector → fișier CNC (ArtCAM/DWG) → CNC față (+ șanfren) |
| Capac spate | același prep → CNC Forex (± șanfren) |
| Volum | prep traseu → (Oracal înainte) → formare → lipire → (RAL după) |
| Sistem LED | Forex gata → montaj → cablare/PSU → colet |

Finisaj față Oracal/print = task **târziu** după asamblare (notat pe cardul Față).

## Boundary

Memoriul T01–T19E / TASK_LOGIC rămân referință istorică owner; **citirea operațională pe UI** e din modulul TS + cele 4 pagini.
