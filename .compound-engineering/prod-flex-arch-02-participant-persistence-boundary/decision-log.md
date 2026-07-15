# PROD-FLEX-ARCH-02 — Owner Decision Log

**Task:** PROD-FLEX-ARCH-02-PARTICIPANT-PERSISTENCE-BOUNDARY  
**Date:** 2026-07-15  
**Readiness:** `READY_FOR_OWNER_DECISION_NOW`  
**Recommended boundary:** Hybrid normalized model (OPTION 5)

---

## Decision Table — Owner Action Required

| ID | Question | Recommended default | Owner answer |
|----|----------|---------------------|--------------|
| **P1** | Do we need participant persistence now? | **YES** — for collaboration write path; not for replacing sessions | _pending_ |
| **P2** | What truth requires persistence beyond sessions? | Help lifecycle; join-before-session; split pools; membership query; duplicate-join prevention | _pending_ |
| **P3** | Parent identity for persistence? | **`(order_id, task_id)`** on materialized operational task | _pending_ |
| **P4** | Persistence shape? | **Hybrid** — normalized membership (FLEX-02) + normalized help (FLEX-04) + sessions unchanged + events as audit supplement | _pending_ |
| **P5** | Principal source remains `assigned_employee_id`? | **YES** — optional principal hint only | _pending_ |
| **P6** | Sessions remain actual-work authority? | **YES** — work/time proof unchanged | _pending_ |
| **P7** | Role model needed now? | **PRINCIPAL + HELPER** at membership layer; defer UI exposure to FLEX-05 | _pending_ |
| **P8** | Join-before-session required? | **YES** — for helper pool and help-accept path | _pending_ |
| **P9** | Leave persistence required? | **YES** — `left_at` on membership row; distinct from session stop | _pending_ |
| **P10** | Migration authorized? | **NO** — not in ARCH-02; authorize at FLEX-02/FLEX-04 gates separately | _pending_ |
| **P11** | FLEX-02 implementation authorized? | **NO** — blocked until P1–P4 confirmed | _pending_ |
| **P12** | Smallest next implementation after future GO? | **FLEX-02** — normalized `execution_task_participants` table + join/leave write API (no UI); paired sequencing with FLEX-03 for D6 | _pending_ |

---

## Option Selection Matrix

| Option | Owner select? | Notes |
|--------|---------------|-------|
| 1 — Sessions-only | Only if pausing entire FLEX collaboration track | Blocks FLEX-02–05 |
| 2 — Normalized membership | **Yes** — core of recommended boundary | FLEX-02 wave |
| 3 — Help-request-first | **Yes** — as FLEX-04 companion, not alone | G6 mandates normalized help |
| 4 — Defer all | No — contradicts realignment verdict | Current blocked state |
| 5 — Hybrid | **Recommended** | B + C(help) + sessions + audit events |

---

## Rejected Shapes (owner already decided)

| Shape | Status |
|-------|--------|
| `participants_json` JSON blob | **DEFERRED / NOT CANONICAL** (OWNER-DECISION-07 G4) |
| Event-only authority without materialized membership | **Reject** — projection drift risk |
| Participation in execution_plan or Product System | **Reject** — violates authority split |
| Employee IDs in frozen snapshot | **Reject** — binding foundation |

---

## Gate Outcomes After Owner Confirmation

| If owner confirms P1–P4 as recommended | Then |
|----------------------------------------|------|
| Authorize FLEX-02 planning/build | Scoped build doc; migration gate at FLEX-02 |
| Keep FLEX-02 blocked | Remain on FLEX-01 read model only |
| Redirect to UI-TRUTH-01B or APP-AUTH-06G | Unpause alternate lane; FLEX track stays at ARCH-02 complete |

---

## Sign-off Block

```
Owner GO for persistence shape (P4):     _____________  Date: _______
FLEX-02 implementation authorized (P11): _____________  Date: _______
Migration authorized (P10):              _____________  Date: _______
```

Until sign-off: **participant writes remain NOT AUTHORIZED.**
