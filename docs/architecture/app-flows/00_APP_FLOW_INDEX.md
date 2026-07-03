# App Flow Documentation — Index

**Version:** 1.1.0  
**Date:** 2026-06-30  
**Branch:** `feature/step-7g-commercial-price-proposal`  
**Repo:** `C:\Users\offic\Desktop\workos-active`

---

## Purpose of this folder

`docs/architecture/app-flows/` is the **operational system map** for WorkOS: pages, routes, data handoffs, source-of-truth rules, gaps, and legacy paths — aligned with the **real application**, not aspirational-only docs.

---

## Doc 21 vs app-flows

| Document | Role |
| -------- | ---- |
| [21_WORKOS_IMPLEMENTATION_ROUTE.md](../realignment/21_WORKOS_IMPLEMENTATION_ROUTE.md) | **Implementation route** — phases 0–10, gates, owner GO, when materialize/sessions/Mobile become safe |
| **app-flows/** (this folder) | **Operational flow map** — pages, routes, data handoffs, **roles/responsibilities**, Form/Product modularization, order lifecycle |

Use **Doc 21** to decide *what to build next*. Use **app-flows** to understand *how the app works now*.

---

## Canonical chain (V2 pilot)

```
Intake V6 workspace
  → Form System (mini-modules / form contract)
  → ProductSystem (template / dossier / modules)
  → ProductDefinition
  → ProductAggregate + task_rules
  → CommercialPriceProposal (CPP) + EstimatedInternalCost (EIC)
  → Quote Snapshot V2 freeze
  → Accept + Owner gates
  → Order Snapshot V2
  → ExecutionPlan V2 preview / persist
  → Materialization audit GET
  → operational_tasks (later — BLOCKED)
  → Sessions / ExecutionActuals (later — FROZEN)
  → ProfitabilityAnalysis (PARTIAL)
  → Employee Mobile (final-final — FROZEN on V2 path)
```

**Pilot template:** `TPL-VOLUMETRIC-LETTERS_v2`  
**Reference fixture:** order `88002`, quote snapshot `id=3`, plan `id=2`

---

## Flow documents

| # | Document | Flow | Status |
| - | -------- | ---- | ------ |
| 01 | [01_INTAKE_V6_FLOW.md](./01_INTAKE_V6_FLOW.md) | Intake V6 + intake list/legacy entry | VALIDATED_WITH_GUARDS |
| 02 | [02_FORM_SYSTEM_FLOW.md](./02_FORM_SYSTEM_FLOW.md) | Modular form contract | PARTIAL |
| 03 | [03_PRODUCT_SYSTEM_FLOW.md](./03_PRODUCT_SYSTEM_FLOW.md) | Templates, dossier, modules | PARTIAL |
| 04 | [04_PRODUCT_DEFINITION_FLOW.md](./04_PRODUCT_DEFINITION_FLOW.md) | Product compiler | VALIDATED |
| 05 | [05_PRODUCT_AGGREGATE_FLOW.md](./05_PRODUCT_AGGREGATE_FLOW.md) | Technical graph + task_contract | VALIDATED_WITH_GUARDS |
| 06 | [06_PRICING_AND_INTERNAL_COST_FLOW.md](./06_PRICING_AND_INTERNAL_COST_FLOW.md) | CPP + EIC + legacy pricing | IMPLEMENTED_PREVIEW_ONLY |
| 07 | [07_OFFER_QUOTE_ORDER_FLOW.md](./07_OFFER_QUOTE_ORDER_FLOW.md) | Quote → snapshot → order | VALIDATED_WITH_GUARDS |
| 08 | [08_EXECUTION_PLAN_FLOW.md](./08_EXECUTION_PLAN_FLOW.md) | ExecutionPlan V2 + materialization audit | VALIDATED_WITH_GUARDS |
| 09 | [09_WORKCENTERS_MACHINES_EMPLOYEES_FLOW.md](./09_WORKCENTERS_MACHINES_EMPLOYEES_FLOW.md) | WC, utilaje, HR registries | PARTIAL |
| 10 | [10_PROFITABILITY_AND_ACTUALS_FLOW.md](./10_PROFITABILITY_AND_ACTUALS_FLOW.md) | Profitability MVP + actuals future | PARTIAL |
| 11 | [11_UI_PAGES_AND_ROUTES_MAP.md](./11_UI_PAGES_AND_ROUTES_MAP.md) | Full UI route map | PARTIAL |
| 12 | [12_LEGACY_AND_DEAD_PATHS_MAP.md](./12_LEGACY_AND_DEAD_PATHS_MAP.md) | Frozen / legacy / dead | DEAD_LEGACY_RISK |
| 13 | [13_ORDER_LIFECYCLE_FLOW.md](./13_ORDER_LIFECYCLE_FLOW.md) | End-to-end order lifecycle | VALIDATED_WITH_GUARDS |
| 14 | [14_APP_ROLES_AND_PAGE_RESPONSIBILITIES.md](./14_APP_ROLES_AND_PAGE_RESPONSIBILITIES.md) | Who uses what; write boundaries; misleading UI | PARTIAL |
| 15 | [15_FORM_SYSTEM_MODULARIZATION_PLAN.md](./15_FORM_SYSTEM_MODULARIZATION_PLAN.md) | Form System modular model (no duplicate forms) | PARTIAL |
| 16 | [16_VOLUMETRIC_LETTERS_TEMPLATE_MODULARIZATION.md](./16_VOLUMETRIC_LETTERS_TEMPLATE_MODULARIZATION.md) | Volumetric pilot template modules + DEC-003/004 | VALIDATED_WITH_GUARDS |

---

## Top 10 gaps (cross-flow)

| # | Gap | Severity |
| - | --- | -------- |
| 1 | All 12 planned tasks: `workcenter` null on fixture | CRITICAL |
| 2 | POST materialize blocked; `operational_tasks[]` empty | CRITICAL |
| 3 | Duplicate lateral module ops vs parent task_rules (DEC-003/004) | HIGH |
| 4 | Legacy `POST /quotes/price` still callable | HIGH |
| 5 | Intake task dry-run (V3/V4 catalog) ≠ ExecutionPlan V2 path | MEDIUM |
| 6 | `estimated_minutes` null — no planning source (DEC-006) | HIGH |
| 7 | Linear dependency chain vs shop DAG (DEC-007) | HIGH |
| 8 | Employees/skills not linked to planned graph | HIGH |
| 9 | UI preview vs official offer labeling incomplete (Step 11) | MEDIUM |
| 10 | Doc lag: some realignment docs say 7G NOT STARTED; preview exists | MEDIUM |

---

## Top 10 forbidden paths

| # | Rule |
| - | ---- |
| 1 | No commercial hourly pricing as client offer basis |
| 2 | No `/price` as canonical path for new V2 volumetric quotes |
| 3 | No CostEngine as commercial price generator |
| 4 | No QuoteOrchestrator as canonical V2 path |
| 5 | No POST materialize without owner GO (DEC-009) |
| 6 | No sessions before Step 11 / Faza 6 GO |
| 7 | No Employee Mobile as V2 production driver before final-final |
| 8 | No retroactive quote reprice from actuals |
| 9 | No treating Intake live preview as official offer |
| 10 | No Step 12 cleanup before canonical route stable |

---

## Employee Mobile rule

**Employee Mobile is final-final (Faza 10).** Requires materialized operational tasks, workcenter truth, eligibility, sessions hardened, and UI labels. **Not** active on canonical V2 path while `operational_tasks[]` is empty.

Routes exist (`/employee-app/*`, `/employee-app-v2/*`) — treat as **FROZEN** relative to V2 order lifecycle until Doc 21 Faza 10 GO.

---

## Related documentation

- [21_WORKOS_IMPLEMENTATION_ROUTE.md](../realignment/21_WORKOS_IMPLEMENTATION_ROUTE.md)
- [20_ROADMAP_STEPS_7G_TO_12.md](../realignment/20_ROADMAP_STEPS_7G_TO_12.md)
- Worklogs: `docs/worklog/realignment/2026-06-30_full_flow_alignment_audit.md`
