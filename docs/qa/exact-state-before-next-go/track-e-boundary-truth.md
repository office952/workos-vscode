# Track E — Boundary Truth (Exact State Before Next GO)

**Repo:** `C:\w\psiso`  
**Date:** 2026-07-31  
**Mode:** READ-ONLY (grep / read / git scope — no product edits)  
**Branch:** `feat/capacity-batch-20d-scoped-b-92401` @ `a1c28854`

**Prior integrity pack:** [`docs/qa/app-integrity-before-next-go/`](../app-integrity-before-next-go/) — especially [`boundary-integrity.md`](../app-integrity-before-next-go/boundary-integrity.md) and [`WORKOS_APP_INTEGRITY_BEFORE_NEXT_GO_REPORT.md`](../app-integrity-before-next-go/WORKOS_APP_INTEGRITY_BEFORE_NEXT_GO_REPORT.md)  
**Handoff / workflow-adv:** [`C:\w\workflow-adv\docs\qa\capacity-batch-20e\pricing-time-boundary-check.md`](../../../../workflow-adv/docs/qa/capacity-batch-20e/pricing-time-boundary-check.md) (Batch 20E materialize — **PASS**)

---

## Required `project_sources/*`

**Still MISSING** on disk under scanned roots (`C:\w\psiso`, handoff, `C:\w\workflow-adv`, common `C:\w` neighbors). Nine canonical boundary docs absent (01–03 through 09–08 pack listed in prior `boundary-integrity.md`). Boundary confirmation below uses live code, AGENTS.md, Batch 20E evidence, and prior QA packs — contents **not invented**.

---

## Checks

### 1) Pricing does not consume measured time / pontaj

| Evidence | Result |
|----------|--------|
| `pontaj` / `attendance` / `productive_hours` / `timesheet` in `backend/**/commercial*.py` | **No hits** (grep) |
| `commercial_price_proposal_service.py` imports no capacity/pontaj modules | **Clean** |
| `FORBIDDEN_HOURLY_TOKENS` in `commercial_rules_volumetric_v2.py` includes `estimated_minutes`, `rate_per_hour` | **Intact** |
| Batch 20E pricing-time check: materialize wrote ops only; null minutes ×18; no price fields | **PASS** |

**Verdict:** **PASS**

### 2) HR / Pontaj separate from Pricing

| Evidence | Result |
|----------|--------|
| `employee_productive_hours.py` header | `HR/Pontaj = internal cost & availability — never client tariff` |
| Attendance UI (`Attendance.tsx`) / registry nav labels | Separate domain from `/inventory/pricing` |
| Dirty WIP on branch: `employees.py`, `employee_productive_hours.py`, lifecycle tests | **WARN** — unrelated HR lifecycle edits; not pontaj→Pricing Registry coupling |

**Verdict:** **PASS WITH WARNINGS** (dirty HR WIP hygiene)

### 3) Capacity separate from pricing engine

| Evidence | Result |
|----------|--------|
| `capacity_batch_02_readiness.py` | `no CostEngine, no HR hours denominator, no client pricing, no invent util%` |
| `capacity_shift_model.py` | `Client pricing is never derived from this model` |
| `capacity_batch_04_gates.py` | Capacity warnings explicitly non-blocking for commercial |
| No pricing/commercial imports in `backend/services/capacity*.py` | **Clean** |

**Verdict:** **PASS**

### 4) Product Definition / Aggregate not mixed with Pricing Registry ownership

| Evidence | Result |
|----------|--------|
| `product_definition_builder_service.py` | `Read-only … — no pricing, no DB writes` |
| `product_aggregate_service.py` | Aggregate builder; open question on preview/price unification documented, not silent merge |
| AGENTS.md + `currentTruthControlCenter.ts` | CPP 7G + `/inventory/pricing` = commercial authority; PD/Aggregate = separate owners |
| Product System surface chips | Labels only; no compiler/aggregate/pricing logic |

**Verdict:** **PASS**

### 5) ExecutionPlan / task graph does not invent missing truth (null minutes honesty)

| Evidence | Result |
|----------|--------|
| `capacity_batch_02_readiness.py` DEC-006 | missing minutes → null + warn (no invent) |
| `execution_ops_graph_read_clarity.py` | Classifies null `estimated_time_minutes` / `planning_minutes_source` with CAP-004 honesty |
| `MaterializedOpsGraph.tsx` | Read-only; surfaces `estimated_time_minutes=null` explicitly |
| Batch 20E live 92401 | `PLANNING_MINUTES_SOURCE_REQUIRED` = planning honesty, not commercial |

**Verdict:** **PASS**

### 6) UI does not hold hidden business logic for materialize / pricing

| Evidence | Result |
|----------|--------|
| `MaterializedOpsGraph.tsx` | READ-ONLY; no POST materialize; no start/stop/assign; no price-from-minutes |
| Materialize gates / DEC-009 | Server-side constants + backend gates |
| `Pricing.tsx` `computeEstimatedNetPrice` | Admin registry helper (unit_cost + markup display); dry-run defers to backend API — **WARN** carry: FE markup math on registry page is display hygiene, not CPP 7G quote authority |
| Dashboard / Utilaje tests | Domain-separated data gaps; honesty banners for null minutes |

**Verdict:** **PASS WITH WARNINGS** (registry UI display math carry)

### 7) No SVG/DWG processing added recently (AGENTS ownership)

| Evidence | Result |
|----------|--------|
| AGENTS.md §1.1 | Desktop app owns SVG/DWG/DXF intelligence; WorkOS consumes external structured results only |
| Pre-existing `frontend/src/lib/svgGeometryParser.ts` | MVP suggestions-only parser (lab legacy) |
| Commit `69e0260f` (2026-07-20) | Added `acm_dxf_path_measurement.py` (ezdxf SPLINE measurement) — **WARN**: in-repo DXF parse/measure path exists despite AGENTS external-analyzer ownership |
| Recent git on svg/dxf paths | Mostly docs + intake-v6 truth-chain fixes; no new central-app parser expansion beyond ACM DXF measurement module |

**Verdict:** **PASS WITH WARNINGS** (AGENTS ownership tension on ACM DXF measurement; not a pricing/time leak)

---

## Integrated verdict

**PASS WITH WARNINGS**

Core pricing/time, HR/Pontaj, Capacity, Product Definition, ExecutionPlan, and materialize UI boundaries **hold**. Warnings (non-blockers):

1. `project_sources/*` pack still missing on disk  
2. Unrelated dirty HR lifecycle WIP on active checkout  
3. Carried Pricing Registry UI display math (`computeEstimatedNetPrice`)  
4. AGENTS §1.1 tension: in-repo ACM DXF measurement (`acm_dxf_path_measurement.py`, Jul 2026) coexists with external-analyzer ownership rule  
5. Pre-existing MVP SVG geometry parser in frontend (suggestions-only, not quote authority)

**0 BLOCKER** for next GO on pricing/time / capacity / ExecutionPlan separation.
