# PROD-FLEX-ARCH-02 — Owner Decision Log

**Task:** PROD-FLEX-ARCH-02-PARTICIPANT-PERSISTENCE-BOUNDARY  
**Owner decision:** OWNER-DECISION-08 (corrected sign-off)  
**Date:** 2026-07-15  
**Architecture verdict:** **ACCEPTED WITH CORRECTIONS**  
**Review verdict:** `PROD_FLEX_ARCH_02_OWNER_REVIEW_ACCEPT_WITH_CORRECTIONS`  
**Recommended boundary:** Hybrid normalized model (OPTION 5)

---

## Architecture Status

| Gate | Status |
|------|--------|
| Architecture (P1–P6, P4 shape) | **ACCEPTED WITH CORRECTIONS** |
| Implementation (FLEX-02) | **NOT AUTHORIZED** |
| Migration | **NOT AUTHORIZED** |
| Participant writes | **NOT AUTHORIZED** |
| Join/leave API | **NOT AUTHORIZED** |
| UI / Mobile | **NOT AUTHORIZED** |

**FLEX-02 remains BLOCKED until a separate owner GO explicitly sets P11=YES and P10=YES at FLEX-02 kickoff.**

Architecture acceptance does **not** authorize code, migration, or write endpoints.

---

## Decision Table — Owner Sign-off (P1–P12)

| ID | Question | Owner answer |
|----|----------|--------------|
| **P1** | Do we need participant persistence now? | **YES** — required for collaboration write path; sessions remain authority for actual work and individual time |
| **P2** | What truth requires persistence beyond sessions? | **ACCEPTED** — join-before-session authorization; future help lifecycle; membership queries; duplicate join prevention; future pool separation |
| **P3** | Parent identity for persistence? | **ACCEPTED** — `(order_id, task_id)` on materialized V2 operational task; `execution_plan_id` is provenance only |
| **P4** | Persistence shape? | **ACCEPTED** — OPTION 5 HYBRID: `execution_task_participants` (membership); `execution_task_help_requests` later in FLEX-04; sessions unchanged; audit events supplemental only; `participants_json` rejected as canonical authority |
| **P5** | Principal source remains `assigned_employee_id`? | **YES** — sole optional principal/coordinator source; not participation proof |
| **P6** | Sessions remain actual-work authority? | **YES** — sole authority for actual work and individual time |
| **P7** | Role model needed now? | **CORRECTED** — FLEX-02 membership persists **HELPER only**; no persisted PRINCIPAL membership row; principal remains `assigned_employee_id` unless a future owner decision changes this |
| **P8** | Join-before-session required? | **CORRECTED** — JOIN creates or reactivates HELPER membership only; JOIN must **not** start session, claim task, change `assigned_employee_id`, mark progress, or complete operation |
| **P9** | Leave persistence required? | **CORRECTED** — LEAVE closes actor's own HELPER membership; may stop actor's own active session only if explicitly included in a future endpoint contract; LEAVE must **not** stop another worker's session, change principal, or complete operation |
| **P10** | Migration authorized? | **NO** — not authorized by this architecture sign-off; separate migration GO required at FLEX-02 kickoff |
| **P11** | FLEX-02 implementation authorized? | **NO** — architecture acceptance does not authorize FLEX-02; separate explicit GO required |
| **P12** | Smallest next implementation after future GO? | **ACCEPTED WITH CORRECTION** — bounded FLEX-02 technical slice only: participants table; HELPER membership only; join/leave membership contract; no help table; no UI; no Mobile; no pool changes; no `_has_active_session_by_other` changes; no session, assignment, or claim behavior changes |

---

## JOIN / LEAVE Semantics (binding)

### JOIN

- Creates or reactivates **HELPER membership** on `(order_id, task_id)`.
- Must **not**: start session; claim task; modify `assigned_employee_id`; mark operation progress; complete operation.

### LEAVE

- Closes **actor's own HELPER membership** (`left_at` / inactive).
- May stop **actor's own** active session only when a future endpoint contract explicitly includes that behavior.
- Must **not**: stop another worker's session; change principal; complete operation.

---

## Option Selection Matrix

| Option | Owner decision | Notes |
|--------|----------------|-------|
| 1 — Sessions-only | **Rejected** for collaboration writes | Blocks FLEX-02–05 |
| 2 — Normalized membership | **Accepted** — HELPER-only at FLEX-02 | Core of hybrid boundary |
| 3 — Help-request-first | **Accepted** — FLEX-04 companion only | Not in FLEX-02 scope |
| 4 — Defer all | **Rejected** | Contradicts accepted architecture |
| 5 — Hybrid | **Accepted** | Membership + help (later) + sessions + audit events |

---

## Rejected Shapes (binding)

| Shape | Status |
|-------|--------|
| `participants_json` JSON blob | **REJECTED / NOT CANONICAL** (OWNER-DECISION-07 G4) |
| Persisted PRINCIPAL membership row | **REJECTED** at FLEX-02 (OWNER-DECISION-08 P7) |
| Event-only authority without materialized membership | **Reject** — projection drift risk |
| Participation in execution_plan or Product System | **Reject** — violates authority split |
| Employee IDs in frozen snapshot | **Reject** — binding foundation |

---

## Gate Outcomes (corrected — no implicit FLEX-02 GO)

| Event | Outcome |
|-------|---------|
| Architecture sign-off (this document) | Persistence **shape** accepted; **implementation remains blocked** |
| Owner sets P11=YES + P10=YES at FLEX-02 kickoff | May authorize bounded FLEX-02 technical slice per P12 |
| Owner keeps P11=NO | Remain on FLEX-01 read model only; no participant writes |
| Redirect to UI-TRUTH-01B or APP-AUTH-06G | Unpause alternate lane; FLEX-02 stays blocked |

**Confirming P1–P4 does not authorize FLEX-02 implementation.**

---

## Sign-off Block

```
ARCHITECTURE PROD-FLEX-ARCH-02: ACCEPTED WITH CORRECTIONS
Date: 2026-07-15
Owner decision: OWNER-DECISION-08

P7:  HELPER_ONLY — no persisted PRINCIPAL membership row
P8:  JOIN_MEMBERSHIP_ONLY
P9:  LEAVE_OWN_MEMBERSHIP_ONLY
P10: Migration authorized — NO
P11: FLEX-02 implementation authorized — NO

IMPLEMENTATION AUTHORIZED:     NO
MIGRATION AUTHORIZED:          NO
PARTICIPANT WRITES AUTHORIZED: NO
JOIN/LEAVE API AUTHORIZED:     NO
UI AUTHORIZED:                 NO
FLEX-02:                       BLOCKED UNTIL SEPARATE OWNER GO
```

Worklog: `docs/worklog/realignment/2026-07-15_owner_decision_08_prod_flex_arch_02_corrected_sign_off.md`
