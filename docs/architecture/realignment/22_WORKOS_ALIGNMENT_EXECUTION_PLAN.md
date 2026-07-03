# 22 — WorkOS Alignment Execution Plan

**Version:** 1.0.0  
**Status:** Execution plan for controlled alignment  
**Date:** 2026-06-30  
**Context source:** documentation ZIP exported on Desktop (`documentatie.zip` → `documentatie_vs`) + local app audit in `workos_app_vs`  
**Verdict accepted:** `ALIGNED_MAP_COMPLETE_WITH_GAPS`

**Related:** [20_ROADMAP_STEPS_7G_TO_12.md](./20_ROADMAP_STEPS_7G_TO_12.md) · [21_WORKOS_IMPLEMENTATION_ROUTE.md](./21_WORKOS_IMPLEMENTATION_ROUTE.md) · [00_WORKOS_TARGET_ARCHITECTURE_OVERVIEW.md](./00_WORKOS_TARGET_ARCHITECTURE_OVERVIEW.md) · [23_WORKOS_CONTROLLED_IMPLEMENTATION_TODO_BACKLOG.md](./23_WORKOS_CONTROLLED_IMPLEMENTATION_TODO_BACKLOG.md)

---

## 1. Purpose

This document translates the target roadmap and implementation route into a **practical start-to-finish execution plan** for aligning the current application with the realignment documentation exported from Desktop.

It answers three questions:

1. What is already true in the app today?
2. What is still out of alignment versus the documented target?
3. In what exact order should implementation proceed so downstream systems are not built on false upstream truth?

This document is intentionally stricter than a roadmap. It defines **execution order, gates, deliverables, forbidden shortcuts, and completion criteria**.

---

## 2. Current truth snapshot

The current application is **not blank** and **not fully aligned**. The V2 spine already exists, but it stops before safe operational execution.

### 2.1 What is already real

| Area | Current state |
| ---- | ------------- |
| Intake V6 | Real and routable |
| ProductDefinition | Real, read-only compile path exists |
| ProductAggregate | Real, including `task_contract.task_rules` |
| CommercialPriceProposal (7G) | Preview implemented |
| EstimatedInternalCost (7H) | Preview implemented |
| Quote Snapshot V2 | Freeze/accept/convert validated with guards |
| Order Snapshot V2 | Real, frozen in `orders.snapshot_v2_json` |
| ExecutionPlan V2 preview | Validated |
| ExecutionPlan V2 persist draft | Validated with guards |
| Materialization audit GET | Implemented read-only |
| Profitability MVP | Implemented read-only |

### 2.2 What is still blocked or partial

| Area | Current state |
| ---- | ------------- |
| `operational_tasks[]` materialization | Blocked pending owner GO |
| Sessions / actual execution truth | Not started on V2 operational path |
| Workcenter truth on planned tasks | Missing / partial |
| Estimated minutes truth on planned tasks | Missing / partial |
| Employee eligibility / assignment graph | Partial foundation only |
| UI labeling policy (Step 11) | Incomplete |
| Pricing Registry separation (7I) | Not started |
| Legacy `/price` path removal | Not started |
| Dead pieces cleanup | Frozen |
| Employee Mobile as canonical V2 consumer | Forbidden for now |

---

## 3. Roadmap coherence review

The roadmap from Desktop is **coherent as sequence**, but **not fully synchronized as status**.

### 3.1 Coherent parts

These are correct and should remain unchanged:

1. Step 8 must precede Step 9 on the canonical path.
2. Step 9 must mature before Step 10 full post-job truth.
3. Step 11 labeling must happen before declaring the flow official.
4. Step 12 cleanup must stay last.
5. Employee Mobile must stay after materialization, eligibility, and sessions.

### 3.2 Out-of-date parts

These need to be read carefully when using the roadmap operationally:

1. `7G NOT STARTED` is no longer accurate if referring to preview implementation.
2. `7H` is also beyond `NOT STARTED` if referring to preview implementation.
3. Step 9 must be split mentally into:
   - preview validated
   - persist draft validated with guards
   - materialization blocked
   - sessions not started
4. README / roadmap status lags behind newer Step 9 and Step 10 worklogs.

### 3.3 Operational reading rule

For execution decisions, the roadmap must be read together with:

1. [21_WORKOS_IMPLEMENTATION_ROUTE.md](./21_WORKOS_IMPLEMENTATION_ROUTE.md)
2. Step 9 semantic audits in `docs/worklog/realignment/`
3. Full flow alignment audit

If roadmap and later worklog disagree, the **later audited worklog wins**.

---

## 4. Mandatory execution principles

1. Downstream must consume **frozen upstream truth**, never reconstruct it from live mutable sources.
2. No implementation may bypass unresolved owner decisions by inventing local defaults.
3. No commercial V2 path may depend on `/price`, QuoteOrchestrator, or hourly commercial pricing.
4. No execution runtime may start before the task graph is semantically clean enough to materialize.
5. No Employee Mobile expansion may begin before operational task truth exists.

---

## 5. Full execution plan

## Phase 0 — Documentation truth sync

**Goal:** make documentation and code status tell the same story.

**Actions:**

1. Mark 7G and 7H as `IMPLEMENTED_PREVIEW_ONLY` rather than `NOT STARTED`.
2. Mark Step 9 as four separate states: preview, persist draft, materialization, sessions.
3. Mark Step 10 as MVP read-only rather than complete profitability truth.
4. Explicitly mark `/price` as legacy / non-canonical for V2.

**Deliverables:**

1. synced status wording in realignment docs
2. no ambiguous status language in roadmap-facing docs

**Exit criteria:**

All realignment docs describe the same current state.

**Owner GO required:** No

---

## Phase 1 — Owner decision closure

**Goal:** close the semantic blockers that prevent safe operational task materialization.

**Required decisions:**

1. `DEC-003` canonical RETURN operation path
2. `DEC-004` canonical PAINTING path
3. `DEC-005` workcenter source policy
4. `DEC-006` estimated minutes source policy
5. `DEC-007` dependency / DAG policy
6. `DEC-009` materialization GO

**Deliverables:**

1. written owner answers
2. updated decision table
3. explicit green/red gate for materialization

**Exit criteria:**

Minimum decisions for materialization are answered: `DEC-003`, `DEC-004`, `DEC-005`, `DEC-007`, `DEC-009`.

**Owner GO required:** Yes

---

## Phase 2 — Step 9B UI truth layer

**Goal:** expose the current execution truth read-only before adding any new writes.

**Actions:**

1. Show `planned_tasks[]` and `planned_operations[]` clearly.
2. Show orphan operations.
3. Show badges for null workcenters, null estimated minutes, duplicate lateral operations, audit-only mode.
4. Remove misleading labels that imply preview data is production-ready.

**Deliverables:**

1. read-only Execution UI visibility for plan truth
2. explicit gap badges
3. zero hidden blockers on the Step 9 surface

**Exit criteria:**

Operator can see the actual V2 draft plan state without any write action.

**Owner GO required:** Yes, scoped to UI read-only changes

---

## Phase 3 — Upstream task contract enrichment

**Goal:** improve the quality of new V2 snapshots before any task materialization.

**Actions:**

1. Canonicalize parent vs module duplicate operations.
2. Keep module duplicates as aggregate aliases only when owner confirms.
3. Populate workcenter metadata according to the chosen policy.
4. Populate estimated minutes according to the chosen policy, or preserve null with explicit warning.
5. Replace naive linear dependencies with the approved DAG model.

**Deliverables:**

1. cleaner aggregate/task contract for new quotes/orders
2. better `ExecutionPlan V2` preview on new fixture orders

**Exit criteria:**

New fixture order no longer exhibits unresolved duplicate semantics on the materialization path.

**Owner GO required:** Yes

---

## Phase 4 — Controlled V2 fixture regeneration

**Goal:** validate the improved upstream chain on fresh data instead of mutating old evidence.

**Actions:**

1. create or refresh controlled V2 fixture
2. freeze Quote Snapshot V2
3. accept and convert to Order Snapshot V2
4. preview ExecutionPlan V2
5. persist draft plan
6. run materialization audit GET

**Deliverables:**

1. fresh fixture order with traceable V2 chain
2. validated evidence that enrichment reached the frozen order snapshot

**Exit criteria:**

Fresh fixture confirms the chain end-to-end without relying on stale historical data.

**Owner GO required:** Yes

---

## Phase 5 — Materialization GO

**Goal:** safely generate `operational_tasks[]` for a controlled fixture order.

**Actions:**

1. execute `POST .../materialize-tasks/{order_id}` on approved fixture
2. verify idempotency
3. verify no duplicate task materialization
4. verify readiness state flips correctly

**Deliverables:**

1. operational task truth exists in the plan envelope
2. materialization audit and POST behavior agree

**Exit criteria:**

`operational_tasks[]` are present and semantically correct on a controlled order.

**Owner GO required:** Yes

---

## Phase 6 — Workcenter and utilaj alignment

**Goal:** connect operational tasks to actual execution locations and machine context.

**Actions:**

1. map operational tasks to authoritative workcenters
2. connect workcenters to utilaje / machine capacity metadata
3. preserve boundary that capacity is operational only, not commercial pricing

**Deliverables:**

1. workcenter truth on operational tasks
2. machine context suitable for scheduling and operator views

**Exit criteria:**

Each materialized task can be placed into a correct operational context.

**Owner GO required:** Yes

---

## Phase 7 — Employee eligibility and assignment readiness

**Goal:** determine who can execute which task before runtime start/stop.

**Actions:**

1. connect employee roles and skills to operational tasks
2. define eligibility model by workcenter / skill / operation family
3. only then expose assignment logic

**Deliverables:**

1. eligibility truth for materialized operational tasks
2. safe basis for assignment workflows

**Exit criteria:**

Assignment no longer depends on guesswork or missing task metadata.

**Owner GO required:** Yes

---

## Phase 8 — Sessions and execution actuals

**Goal:** begin recording real execution data on the V2 path.

**Actions:**

1. start-task / end-task on materialized tasks
2. persist execution reality and session truth
3. keep hard guards when the order is not materialized or not ready

**Deliverables:**

1. real actual minutes on V2 orders
2. usable divergence data

**Exit criteria:**

Execution reality is recorded from the canonical V2 operational task graph.

**Owner GO required:** Yes

---

## Phase 9 — Full profitability truth

**Goal:** complete the profitability loop after real execution exists.

**Actions:**

1. keep accepted revenue frozen
2. keep estimated internal cost frozen
3. compute actual labor/material cost from real operational truth
4. expose actual margin without write-back into quote/order pricing

**Deliverables:**

1. non-null actual margin on closed orders
2. true post-job profitability analysis

**Exit criteria:**

Profitability reflects actual execution, not only estimated pre-job data.

**Owner GO required:** Yes

---

## Phase 10 — Pricing Registry separation and legacy path deprecation

**Goal:** reduce legacy pricing confusion once V2 path is stable enough.

**Actions:**

1. separate commercial rules, internal cost, capacity, analytics in registry UI
2. demote `/price` to explicit legacy path
3. block new V2 business from depending on unified legacy pricing shortcuts

**Deliverables:**

1. clearer registry boundaries
2. lower risk of returning to cost-plus shortcuts

**Exit criteria:**

New V2 flows are not operationally dependent on legacy pricing entry points.

**Owner GO required:** Yes

---

## Phase 11 — UI labeling completion

**Goal:** finish Step 11 so no surface lies about truth level.

**Actions:**

1. label preview vs official vs internal vs audit-only vs legacy
2. ensure no page treats preview data as production truth
3. remove misleading execution/product/pricing wording

**Deliverables:**

1. labeling policy implemented across major routes
2. no remaining `MISLEADING_UI` class issues on core V2 surfaces

**Exit criteria:**

Users can distinguish clearly between frozen truth, preview, audit-only, and legacy data.

**Owner GO required:** Yes

---

## Phase 12 — Dead pieces cleanup

**Goal:** remove or archive truly dead legacy pieces only after the canonical path is stable.

**Actions:**

1. classify each candidate as active, legacy compatibility, misleading, or dead
2. remove per piece with evidence
3. never bulk-delete based on assumptions

**Deliverables:**

1. safer codebase with fewer dead branches
2. preserved audit trail for removed legacy pieces

**Exit criteria:**

Cleanup no longer risks breaking the still-stabilizing canonical path.

**Owner GO required:** Yes, per piece

---

## Phase 13 — Employee Mobile final rollout

**Goal:** use Employee Mobile only when the operational graph is truly ready.

**Preconditions:**

1. materialized operational tasks exist
2. workcenter truth exists
3. employee eligibility exists
4. sessions are real and stable
5. UI labels are clear

**Deliverables:**

1. mobile consumes real operational truth instead of placeholders
2. V2 execution can extend safely to mobile surfaces

**Exit criteria:**

Employee Mobile becomes a consumer of stable operational truth, not a substitute for missing backend maturity.

**Owner GO required:** Yes

---

## 6. Immediate next action

If execution starts now, the correct first implementation slice is:

1. **Phase 0** documentation truth sync
2. **Phase 1** owner decision closure
3. **Phase 2** Step 9B UI read-only truth layer

This is the highest-value sequence because it improves correctness immediately without prematurely opening blocked write paths.

---

## 7. Forbidden shortcuts

1. Do not use `/price` to "complete" the V2 path.
2. Do not materialize tasks before owner decisions are closed.
3. Do not start sessions before operational task truth exists.
4. Do not revive hourly commercial pricing to fill planning gaps.
5. Do not expand Employee Mobile before Phases 5 to 8 are complete.
6. Do not run cleanup before the canonical path is proven.

---

## 8. Completion definition

The application is aligned with the Desktop documentation only when all of the following are true:

1. new quotes/orders follow the canonical V2 path by default
2. execution tasks materialize from frozen order snapshot truth
3. workcenter / employee eligibility / sessions are real
4. profitability uses actual post-job data
5. legacy pricing shortcuts are demoted
6. UI labeling no longer misrepresents preview as official
7. cleanup is performed only after the new path is stable

Until then, the correct status remains:

`ALIGNED_MAP_COMPLETE_WITH_GAPS`