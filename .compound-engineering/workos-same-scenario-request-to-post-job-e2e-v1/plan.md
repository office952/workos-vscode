# WORKOS Same-Scenario Request → Post-Job E2E Truth V1 — Plan

**Verdict (planning):** `WORKOS_SAME_SCENARIO_REQUEST_TO_POST_JOB_E2E_PLAN_READY`  
**Status stamp:** **SAME-SCENARIO E2E PLAN READY FOR OWNER REVIEW**  
**Date:** 2026-07-16  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Prerequisite:** Post-job V1 **ACCEPT_WITH_NONBLOCKING_LIMITATIONS** (closure worklog)  
**Implementation:** **NOT STARTED** — separate owner GO via `/ce-work`

---

## 1. Why this phase

Post-job truth V1 is accepted. Commercial spine, plan materialization, FLEX, and post-job reads work in pieces. The open risk is **stage-stitched demos** rather than one continuous lineage.

Wave 7 used controlled stage fixtures: quote/`QSN2` commercial path and order `23099` execution path are **not the same continuous Intake→order chain**. Order `23099` is too polluted for this proof.

**Goal:** Prove one real product scenario travels Request → Intake V6 → … → Post-job truth without parallel truth, mock state, or hidden repair.

---

## 2. Selected scenario

| Field | Choice |
|-------|--------|
| Product | Illuminated volumetric letters |
| Template | `TPL-VOLUMETRIC-LETTERS_v2` |
| Shape | Acceptance-style: SVG (e.g. gradi-curat) + linked `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` when composition requires |
| Why | Only fully wired V6→snapshot→order→plan→reality→post-job spine; ACM-as-root out of bounds |

**Not selected:** Order `23099` (stitched + polluted). Bare `TPL-VOLUMETRIC-LETTERS` without `_v2`. Product System catalog polish as the phase itself.

---

## 3. Active path (exclusive)

```text
/intake (New request)
  → ensure Intake V6 workspace (keep intake_request_code)
  → /intake-v6/:workspaceId/operator
  → 7G CommercialPriceProposal + 7H EstimatedInternalCost (dry-run)
  → Quote Snapshot V2 freeze
  → handoff-to-offer / accept
  → convert-to-order (Order Snapshot V2)
  → /execution/:orderId
  → Plan V2 preview/persist/materialize
  → reality start/complete sessions
  → inventory deduction (explicit operator action)
  → Post-job truth + profitability coverage
```

**Reject for this proof:** legacy `/price`, QuoteOrchestrator as commercial authority, WorkIntake V1/V2 as primary, legacy `POST /execution/plan/from-order` as V2 substitute, frontend-calculated cost, SQL repair, stage-stitch of unrelated quote→order IDs.

---

## 4. Handoff matrix (summary)

| # | Handoff | Status | Same continuous lineage today |
|---|---------|--------|-------------------------------|
| 1 | Request → Intake V6 | operational | Stage-proven; not continuous to post-job |
| 2 | Intake V6 → Product Definition | partial (compile preview) | Not continuous |
| 3 | PD → Aggregate | operational (W2 debt) | Not continuous |
| 4 | Aggregate → Cost (7G/7H) | operational adapters | Dry-run/snapshot stage |
| 5 | Cost → Offer (Snapshot V2) | operational | Fixture QSN2 ≠ order 23099 |
| 6 | Offer accept → Order | operational | Stitched in Wave 7 |
| 7 | Order → frozen snapshot | operational | Stage order only |
| 8 | Snapshot → Execution Plan V2 | operational | Proven on 23099 |
| 9 | Plan → materialized tasks | operational | Proven on 23099 |
| 10 | Tasks → sessions | operational | Proven (noisy) on 23099 |
| 11 | Deduction → material actuals | operational | Temp proof + reverse |
| 12 | Sessions → labor minutes | operational | Minutes-only |
| 13 | Reality → reconciliation | operational | Honest gaps |
| 14 | Reconciliation → profitability | partial (no labor $) | PARTIAL max by design |

Full field detail (keys, APIs, UI) lives in research notes; implementer re-verifies against HEAD before `/ce-work`.

---

## 5. Phase outcome

Owner can walk **one** new local scenario end-to-end and see the **same IDs** on every surface, ending in Post-job truth with:

- planned vs actual separate  
- real material deduction (optional reverse cleanup)  
- real closed sessions → minutes  
- coverage PARTIAL/INCOMPLETE with labor money excluded  
- frozen commercial total unchanged  

---

## 6. Exact scope (one GO)

**In**

1. Unbroken identity chain: `IR-*` → `workspace_id` → `quote_id`/`QSN2` → `order_id` → plan → sessions → post-job  
2. Real accept → convert on that quote (no stitch)  
3. Fresh startable tasks on that order  
4. ≥1 real stock deduction aligned to scenario materials (cleanup reverse if supported)  
5. Owner walkthrough evidence (URLs + captured IDs)  
6. Honest handling of null planned minutes / partial 7H if present  
7. Focused tests: identity propagation, active-path exclusivity, snapshot immutability, post-job linkage  
8. Worklog / BUILD qa doc  

**Out**

- Product System redesign / all families / ACM root activation  
- HR labor money / complete `actual_total_cost`  
- FLEX polish / `/operator` mirror  
- UI-TRUTH / APP-AUTH  
- Capacity product  
- Classic CostEngine / `/price` revival  
- Broad inventory redesign  
- Migration unless STOP+owner (prefer none)  
- Persistent canonical seed  

---

## 7. Fixture policy

**Preferred:** create a **new local scenario through real UI/API flow**.

| Decision | Value |
|----------|--------|
| Order 23099 | **Do not use** as subject |
| Persistent seed | **No** |
| Cleanup | Reverse temporary deductions where supported; document any local residue (like temp SKUs) |
| Why not seed | Avoids fixture theater and seed debt |

Capture and retain for BUILD: `intake_request_code`, `workspace_id`, `quote_id`, `snapshot_code`, `order_id`, task keys, movement ids, session ids.

---

## 8. API / UI implications

Primarily **exercise existing** routes. Thin additive projections only if a handoff identity is silently dropped.

Primary UI path:

1. `http://127.0.0.1:3000/intake`  
2. `…/intake-v6/{workspaceId}/operator`  
3. `…/quotes/{quoteId}`  
4. `…/orders/{orderId}`  
5. `…/execution/{orderId}` — Plan → sessions → Stock deduction → **Post-job truth**  

APIs: Snapshot V2 / accept / convert / plan-v2 / reality / deduction / `post-job-truth` / profitability.

---

## 9. Testing strategy

- Identity propagation across accept→convert→plan→post-job  
- Active-path exclusivity (no `/price` imports on proof path)  
- Snapshot immutability before/after post-job reads and deduction  
- Session minutes + material actual linkage on **same** order_id  
- Profitability coverage never COMPLETE without labor money  
- Frontend: no canonical margin math  
- Runtime: one continuous lineage evidence pack (not unrelated fixtures)

---

## 10. Owner-visible verification (must be in final BUILD)

| Step | Surface | Expect |
|------|---------|--------|
| 1 | `/intake` | New `IR-*` |
| 2 | `/intake-v6/:id/operator` | Same `intake_request_code`; `_v2` template |
| 3 | Commercial spine | Snapshot V2; record quote + snapshot codes |
| 4 | `/quotes/:id` | Accept + convert |
| 5 | `/orders/:id` | Frozen snapshot; commercial totals match accept |
| 6 | `/execution/:id` | Plan V2 + materialize; start/complete ≥1 task |
| 7 | Stock deduction | Real movement |
| 8 | Post-job truth | Minutes; materials; variances; PARTIAL/INCOMPLETE; commercial unchanged |

Still unavailable by design: full HR labor money; machine telemetry; PS catalog polish.

---

## 11. Data / migration

Prefer **no migration**. STOP for owner if schema required.

---

## 12. Owner decisions at implementation GO (phase-level)

1. **G1:** Approve same-scenario E2E as next phase (vs PS / APP-AUTH / HR money)?  
2. **G2:** Authorize creating a new local order via real flow (and local cleanup)?  
3. **G3:** Accept PARTIAL profitability (labor money still out) as success for this phase?  
4. **G4:** Linked ACM mounting in composition required for the scenario, or letters-only if composition allows?

---

## 13. Confidence

High that continuous lineage is the right next gate. Medium on exact friction points until first real walkthrough (PD/aggregate debt, planned minutes null, stock SKU readiness).

---

## Artifact index

| Artifact | Path |
|----------|------|
| This plan | `.compound-engineering/workos-same-scenario-request-to-post-job-e2e-v1/plan.md` |
| Decision log | `.compound-engineering/workos-same-scenario-request-to-post-job-e2e-v1/decision-log.md` |
| Worklog | `docs/worklog/realignment/2026-07-16_workos_same_scenario_e2e_plan.md` |
| Prerequisite closure | `docs/worklog/realignment/2026-07-16_workos_post_job_v1_independent_closure.md` |
