# Boundary Integrity

**Repo:** `C:\w\psiso`  
**Date:** 2026-07-31  
**Mode:** Verify-only (code + prior 20E boundary evidence + live envelopes)

---

## Required project_sources

All of the following are **MISSING** on disk under scanned roots (`psiso`, handoff, `workflow-adv`, common `C:\w` neighbors). Contents were **not invented**:

- `project_sources/01-03_PRODUCT_DEFINITION_COMPILER.md`
- `project_sources/02-12_HR_PONTAJ_EMPLOYEE_COST_BOUNDARY.md`
- `project_sources/03-05_PRODUCT_AGGREGATE_FLOW.md`
- `project_sources/04-10_EXECUTION_PLAN_TASK_GRAPH.md`
- `project_sources/05-08_EXECUTION_PLAN_FLOW.md`
- `project_sources/06-14_MACHINES_UTILAJE_CAPACITY_BOUNDARY.md`
- `project_sources/07-21_WORKOS_IMPLEMENTATION_ROUTE.md`
- `project_sources/08-18_GOVERNANCE_SETTINGS_POLICY.md`
- `project_sources/09-08_PRICING_REGISTRY_SEPARATION.md`

Boundary confirmation below uses live code, AGENTS.md, Batch 20E pricing-time check, and envelope observations instead.

---

## Checks

### 1) Pricing separated from measured / planning time

| Evidence | Result |
|----------|--------|
| Batch 20E `pricing-time-boundary-check.md` | **PASS** — materialize wrote ops only; minutes remain null; no price fields |
| Live ops 92401 | `estimated_time_minutes=null` ×18; warning `PLANNING_MINUTES_SOURCE_REQUIRED` (planning honesty, not commercial) |
| No Pricing/CostEngine product edits in this audit | N/A (read-only) |
| Gate/materialize modules do not set commercial prices from minutes | Spot-check clean |

**Verdict:** **PASS**

### 2) HR / pontaj separate from Pricing

| Evidence | Result |
|----------|--------|
| Attendance events | 0 |
| Scoped orders have no Employee Mobile participants/help | 0 / 0 |
| Dirty employee WIP present on branch | **WARN** — unrelated local HR lifecycle edits; must not be treated as capacity/Pricing work |
| Pre-existing `is_valid_for_cost_engine` helper in `employees.py` | Historical coupling surface (cost-engine employee validity), **not** pontaj→Pricing Registry; dirty diff appears reformat/move |

**Verdict:** **PASS WITH WARNINGS** (dirty HR WIP hygiene)

### 3) Capacity remains planning / load / internal-control only

| Evidence | Result |
|----------|--------|
| Materialize did not invent minutes/WC/assignments | Live nulls retained |
| Ops-graph read_clarity treats machine_type as requirement class, not capacity unit price | Present on tasks |
| No Capacity formula product edits this audit | N/A |

**Verdict:** **PASS**

### 4) Product Truth separate from Pricing Registry

| Evidence | Result |
|----------|--------|
| AGENTS.md ownership: operator confirms Product Truth; Pricing is separate registry | Binding |
| 20E zero ProductDefinition / Aggregate logic changes | Prior report |
| This audit made no PD/Pricing edits | Confirmed |

**Verdict:** **PASS**

### 5) ExecutionPlan / task graph boundaries clean

| Evidence | Result |
|----------|--------|
| 92401 envelope: 18 ops / 18 planned / plan 13 only | Clean |
| 973010 envelope: 12 ops / plan 12 only · hash stable | Clean |
| Lifecycle on ops = `pending` plan status — explicitly not ExecutionActuals/session | read_clarity notes |
| `execution_tasks_created` / materialized flags consistent via API | True / ready |

**Verdict:** **PASS**

### 6) No business logic hidden in UI components (spot-check)

| Evidence | Result |
|----------|--------|
| `MaterializedOpsGraph.tsx` remains read-only ops surface | No start/stop/assign added |
| DEC-009 authorize is server constant + gate | Backend |
| Frontend still must not invent minutes/prices (AGENTS + prior batches) | Held for 20E path |

**Verdict:** **PASS** (lab Product System pages still contain readiness chrome — tracked under product-direction, not as new boundary breach)

---

## Verdict

**PASS WITH WARNINGS** — Core pricing/time, ExecutionPlan, and Capacity boundaries hold. Warning: missing `project_sources/*` pack on disk + unrelated dirty HR WIP on the active checkout.
