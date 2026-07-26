# Decision log — Post-FLEX Roadmap Reentry

**Program stamp:** **POST-FLEX ROADMAP REENTRY PLAN READY FOR OWNER REVIEW**  
**Planning HEAD:** `0cd82d9`  
**Date:** 2026-07-16  

Decisions below are **planning-time**. Implementation GO decisions (G1–G4) remain **open** until the owner authorizes `/ce-work` for `WORKOS-POST-JOB-ACTUALS-RECONCILIATION-AND-PROFITABILITY-TRUTH-V1`.

---

## Planning decisions (accepted with this plan)

| ID | Decision | Rationale |
|----|----------|-----------|
| **P-001** | Next major phase = post-job actuals + plan/reality reconciliation + profitability truth | Highest owner-visible gap after FLEX; live `23099` profitability nulls prove it |
| **P-002** | Do **not** reopen Wave 5 plan materialize as next major phase | Runtime on `23099` already `v2_operational_ready`; flow doc `08` is stale |
| **P-003** | Do **not** make Product System / Aggregate the next major phase | PS is configuration authority (D-004), not the post-FLEX customer→job bottleneck |
| **P-004** | Do **not** make workcenter/capacity the next major phase | Premature without measured post-job actuals feedback |
| **P-005** | Do **not** reopen APP-AUTH-06G / UI-TRUTH as next major phase | Owner-paused; not the FLEX closure gap |
| **P-006** | FLEX polish / `/operator` collab mirror stay deferred | Owner forbids polish lane; Phase 3 closed with nonblocking limitations |
| **P-007** | Same-scenario Intake→completed-job E2E is **follow-on proof**, not the primary build | Avoid fixture theater; first make completed jobs measurable |
| **P-008** | Prefer **no DB migration**; additive read/JSON first; STOP if schema required | Keep phase bounded; escalate to owner |
| **P-009** | No commercial hourly labor rates; no quote/order price write-back | Protect 7G commercial authority; CostEngine/7H remain internal |
| **P-010** | Planning task writes docs/STATUS only — **no** product implementation | Separate owner GO via `/ce-work` |

---

## Owner GO decisions (required before implementation)

| ID | Question | Status | Notes |
|----|----------|--------|-------|
| **G1** | Approve post-job actuals phase as next (vs Product System or APP-AUTH)? | **YES** | Owner GO 2026-07-16 — implement phase |
| **G2** | Labor money out of scope — minutes-only labor actuals OK? | **YES** | Minutes-only; no HR money; partial profitability wording required |
| **G3** | Material actuals require real stock deduction on fixture order — authorize temporary local deduction/cleanup? | **YES** | Local fixture only; real deduction path; cleanup where supported |
| **G4** | Primary surface remains `/execution/:orderId` only (no `/operator` mirror)? | **YES** | Execution only |

One-GO authorization: owner approves **the whole phase** (not per-endpoint). G1–G4 are phase-level gates only.

---

## Explicitly not decided here

- Exact API route shape (reuse task-truth vs new reconciliation route) — left to implementer under `/ce-work`
- Whether a feature flag is required for read enrichment — optional rollback tool
- Whether `23099` is too polluted for material deduction proof — runtime choice at implement time

---

## Remains paused after implementation GO

- FLEX polish; `/operator` mirror
- UI-TRUTH-01B+
- APP-AUTH-06G
- PS isolation closeout as primary
- Capacity / workcenter product
- Employee Mobile V1
- ShopFloor
- Module Chain runtime control plane
