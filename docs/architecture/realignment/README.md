# WorkOS Realignment Architecture — Documentation Index

**Status:** Target architecture + **Step 9 persist draft VALIDATED_WITH_GUARDS** (sync 2026-06-30)  
**Repo:** `C:\Users\offic\Desktop\workos-active`  
**Date:** 2026-06-30 (sync after Step 9 persist draft validation)  
**Verdict accepted:** `HIGH_RISK_DEVIATED` / `HIGH_RISK_MINUTES_AS_PRICE`  
**Branch:** `feature/step-7g-commercial-price-proposal` — commit `b12889c` (Step 9 persist draft)

---

## Ce sunt aceste documente

Set de **22 documente de arhitectură țintă** care descriu cum **vrem** să funcționeze WorkOS. Documentele marchează explicit ce este **IMPLEMENTED**, **VALIDATED**, **PLANNED**, **WATCH** sau **NOT STARTED** — fără optimism fals.

Fiecare document descrie **un singur sistem** cu aceeași structură:

1. Rolul sistemului  
2. Ce detine  
3. Ce NU detine  
4. Inputuri  
5. Outputuri  
6. Source of truth  
7. Conexiuni cu celelalte sisteme  
8. Reguli owner obligatorii  
9. Riscuri actuale din audit  
10. Target state  
11. Forbidden behavior  
12. Acceptance criteria  

---

## Ordinea de citire recomandată

| Ordine | Document | De ce |
|--------|----------|-------|
| 1 | [00_WORKOS_TARGET_ARCHITECTURE_OVERVIEW.md](./00_WORKOS_TARGET_ARCHITECTURE_OVERVIEW.md) | Imaginea mare, flux canonic, interdicții globale |
| 2 | [01_INTAKE_V6_PRODUCT_TRUTH.md](./01_INTAKE_V6_PRODUCT_TRUTH.md) | Sursa produsului cerut |
| 3 | [02_PRODUCT_SYSTEM_TEMPLATE_CONTRACT.md](./02_PRODUCT_SYSTEM_TEMPLATE_CONTRACT.md) | Ce este posibil tehnologic |
| 4 | [03_PRODUCT_DEFINITION_COMPILER.md](./03_PRODUCT_DEFINITION_COMPILER.md) | Compiler produs concret |
| 5 | [04_PRODUCT_AGGREGATE_TECHNICAL_GRAPH.md](./04_PRODUCT_AGGREGATE_TECHNICAL_GRAPH.md) | Graful tehnic complet |
| 6 | [05_COMMERCIAL_PRICE_PROPOSAL.md](./05_COMMERCIAL_PRICE_PROPOSAL.md) | Preț comercial client (mp/ml/buc/set) |
| 7 | [06_ESTIMATED_INTERNAL_COST.md](./06_ESTIMATED_INTERNAL_COST.md) | Cost intern estimativ |
| 8 | [07_COST_ENGINE_REALIGNMENT.md](./07_COST_ENGINE_REALIGNMENT.md) | Rol nou Cost Engine |
| 9 | [08_PRICING_REGISTRY_SEPARATION.md](./08_PRICING_REGISTRY_SEPARATION.md) | Separare registry |
| 10 | [09_QUOTE_ORDER_SNAPSHOT_CONTRACT.md](./09_QUOTE_ORDER_SNAPSHOT_CONTRACT.md) | Snapshot dual comercial + intern |
| 11 | [10_EXECUTION_PLAN_TASK_GRAPH.md](./10_EXECUTION_PLAN_TASK_GRAPH.md) | Taskuri din graf tehnic |
| 12 | [11_EXECUTION_ACTUALS_AND_TASK_SESSIONS.md](./11_EXECUTION_ACTUALS_AND_TASK_SESSIONS.md) | Minute reale post-job |
| 13 | [12_HR_PONTAJ_EMPLOYEE_COST_BOUNDARY.md](./12_HR_PONTAJ_EMPLOYEE_COST_BOUNDARY.md) | HR intern |
| 14 | [13_INVENTORY_MATERIAL_REGISTRY.md](./13_INVENTORY_MATERIAL_REGISTRY.md) | Materiale și stoc |
| 15 | [14_MACHINES_UTILAJE_CAPACITY_BOUNDARY.md](./14_MACHINES_UTILAJE_CAPACITY_BOUNDARY.md) | Utilaje și capacitate |
| 16 | [15_HUB_COLLABORATORS_BOUNDARY.md](./15_HUB_COLLABORATORS_BOUNDARY.md) | WorkOS vs HUB extern |
| 17 | [16_PROFITABILITY_ANALYSIS.md](./16_PROFITABILITY_ANALYSIS.md) | Analiză post-job |
| 18 | [17_UI_NAVIGATION_AND_LABELING_POLICY.md](./17_UI_NAVIGATION_AND_LABELING_POLICY.md) | Etichetare UI |
| 19 | [18_GOVERNANCE_SETTINGS_POLICY.md](./18_GOVERNANCE_SETTINGS_POLICY.md) | GO owner, feature flags |
| 20 | [19_LEGACY_DEAD_PIECES_CLEANUP_POLICY.md](./19_LEGACY_DEAD_PIECES_CLEANUP_POLICY.md) | Clasificare legacy/dead |
| 21 | [20_ROADMAP_STEPS_7G_TO_12.md](./20_ROADMAP_STEPS_7G_TO_12.md) | Pași implementare viitori |

**Documente sursă (citite, nemodificate):**

- `docs/architecture/WORKOS_COMMERCIAL_PRICING_VS_INTERNAL_COST_CONTRACT.md`
- `docs/architecture/WORKOS_REALIGNMENT_MASTER_PLAN.md`
- `docs/architecture/WORKOS_FULL_SYSTEM_REALITY_AUDIT_ACCEPTANCE.md`
- `docs/architecture/MODULAR_PRODUCT_FLOW_CONTRACT.md`
- `docs/architecture/TPL_VOLUMETRIC_LETTERS_COSTING_LOGIC_AUDIT.md`
- `tmp/FULL_MODULAR_PRODUCT_FLOW_AUDIT_REPORT_20260630.md`

---

## Regula owner (obligatorie)

> **Doar ownerul decide dacă modificăm ceva sau nu.**

Fără **GO explicit**, este interzis:

- implementare runtime (Step 7G+)
- refactor Cost Engine / QuoteOrchestrator
- reprice Quote 4
- apply Step 7E.2
- modificări DB / seed / migration
- apel `/price` ca „fix”
- modificări UI / CSS
- modificări Pricing Registry ca soluție ad-hoc
- ștergere cod / cleanup / depreciere fără decizie

Aceste documente **propun** arhitectura țintă. Nu o aplică.

---

## Principiu central

**WorkOS nu trebuie să mai devieze spre „minute = preț”.**

P-Media **nu** ofertează clientului „100 ore × tarif oră”. Prețurile comerciale se bazează pe **produs / soluție**: mp, ml, buc, literă, set, minim lucrare, complexitate, material, finisaj, urgență.

**Minutele** sunt doar pentru: task start/stop, ExecutionActuals, capacitate, statistică, ProfitabilityAnalysis post-job.

---

## Roadmap (awareness only)

| Step | Nume | Status |
|------|------|--------|
| 7F | Contract comercial vs cost intern (docs) | **DONE** |
| 7F.1 | Audit acceptance + freeze intent | **DONE** |
| **7G** | CommercialPriceProposal (read-only preview) | **NOT STARTED** — preview services exist; full runtime **NEEDS OWNER GO** |
| **7H** | EstimatedInternalCost non-hourly | **NEEDS OWNER GO** |
| **7I** | Pricing Registry separation | **NEEDS OWNER GO** |
| **8** | Quote snapshot dual (commercial + internal) | **VALIDATED_WITH_GUARDS** — live chain **VALIDATED**: freeze snapshot V2 → pricing review from snapshot V2 commercial total → owner approval → accept → convert to order snapshot V2; **126 pytest**; runtime evidence snapshot `QSN2-2026-0003`, quote 1 `accepted_snapshot_v2_id=3`, order `88002`; convert creates **no** execution_plan/tasks; **no** `/price`/CE/QO |
| **9** | ExecutionPlan V2 from Order snapshot V2 | **PARTIAL — VALIDATED_WITH_GUARDS** — preview **VALIDATED** (`8dd67e9`); persist draft **VALIDATED_WITH_GUARDS** (`b12889c`); order `88002`, plan `id=2`, `source_quote_snapshot_v2_id=3`; **107 pytest** persist suite; **no** execution_tasks/sessions; HTTP persist **pending fresh backend restart**; materialize **BLOCKED / NEEDS OWNER GO** |
| **10** | ProfitabilityAnalysis | **PARTIAL** — **10.1** **IMPLEMENTED**; **10.2+10.3** read-only MVP GET **IMPLEMENTED + VALIDATED**; **10.4** minimal ExecutionDetail panel **IMPLEMENTED** (`378b42b`); complete post-job truth **DEFERRED**; actual margin $ **DEFERRED**; no dedicated route |
| **11** | UI labels / deprecation (no redesign) | **NEEDS OWNER GO** |
| **12** | Dead pieces cleanup | **NEEDS OWNER GO** |

**Runtime validated (2026-06-30):** Execution Plan V2 operational readiness (order `88001`), DivergenceService read-only, controlled QA fixture, profitability MVP GET + ExecutionDetail panel, order financial immutability individual + batch PUT, **Step 8 dual quote snapshot flow VALIDATED_WITH_GUARDS** (snapshot `QSN2-2026-0003`, order `88002`; convert creates no plan/tasks), **Step 9 preview from Order snapshot V2 VALIDATED** (order `88002`, `partial_missing_planning_minutes`, 12 task candidates, `no_write=true`), **Step 9 persist draft VALIDATED_WITH_GUARDS** (plan `id=2`, `source_quote_snapshot_v2_id=3`, `tasks_json` with 12 planned tasks / 17 operations; idempotency `already_exists`; service-level QA; HTTP **pending backend restart**). **Worklogs:** `docs/worklog/realignment/` — fără worklog = task neînchis.

Detalii: [20_ROADMAP_STEPS_7G_TO_12.md](./20_ROADMAP_STEPS_7G_TO_12.md)

---

## Clasificări legacy (referință)

| Tag | Semnificație |
|-----|--------------|
| `ACTIVE_OPERATIONAL` | Producție reală |
| `ACTIVE_READONLY_TRUTH` | Adevăr read-only (ex. Aggregate BOM preview) |
| `ADMIN_REGISTRY` | Registry administrativ |
| `ANALYTICS_ONLY` | Statistică, post-job |
| `FUTURE_RESERVED` | Boundary viitor (ex. HUB) |
| `LEGACY_COMPATIBILITY` | Compatibilitate veche |
| `MISLEADING_UI` | UI sugerează altceva decât realitatea |
| `DEAD_PIECE` | Neconectat la flux |
| `HIGH_RISK_WRONG_DIRECTION` | Minute=preț, cost-plus universal |
| `NEEDS_OWNER_DECISION` | UNKNOWN — owner decide |

---

## Git / repo note

La crearea acestor documente, directorul `workos-active` **nu era repo git** (`fatal: not a git repository`). Documentația este locală în checkout activ; nu atinge `C:\Users\offic\workos`.
