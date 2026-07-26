# OWNER-DECISION-08 — PROD-FLEX-ARCH-02 Corrected Sign-off

**Task:** OWNER-DECISION-08-PROD-FLEX-ARCH-02-CORRECTED-SIGN-OFF  
**Date:** 2026-07-15  
**Starting HEAD:** `43668f9`  
**Source review:** `PROD_FLEX_ARCH_02_OWNER_REVIEW_ACCEPT_WITH_CORRECTIONS`  
**Verdict:** `OWNER_DECISION_08_PROD_FLEX_ARCH_02_CORRECTED_SIGN_OFF_COMPLETE`

---

## Architecture verdict

**ACCEPTED WITH CORRECTIONS**

Hybrid OPTION 5 accepted. Implementation **NOT AUTHORIZED**.

---

## Owner sign-off (binding)

```
ARCHITECTURE PROD-FLEX-ARCH-02: ACCEPTED WITH CORRECTIONS

P1: YES — participant persistence required; sessions remain work authority
P2: ACCEPTED — join-before-session; help lifecycle; membership queries; duplicate-join prevention; pool separation
P3: ACCEPTED — (order_id, task_id) on materialized V2 operational task; execution_plan_id provenance only
P4: ACCEPTED — OPTION 5 HYBRID; participants_json rejected
P5: YES — assigned_employee_id sole optional principal/coordinator; not participation proof
P6: YES — sessions sole authority for actual work and individual time
P7: CORRECTED — HELPER-only membership; no persisted PRINCIPAL row
P8: CORRECTED — JOIN = HELPER membership only; no session/claim/assignee/progress/complete
P9: CORRECTED — LEAVE = own HELPER membership; own session stop only if future contract includes it
P10: NO — migration not authorized by architecture sign-off
P11: NO — FLEX-02 not authorized; architecture acceptance ≠ implementation GO
P12: ACCEPTED WITH CORRECTION — bounded FLEX-02 slice only when separate GO granted

IMPLEMENTATION AUTHORIZED: NO
MIGRATION AUTHORIZED: NO
PARTICIPANT WRITES AUTHORIZED: NO
JOIN/LEAVE API AUTHORIZED: NO
UI AUTHORIZED: NO
FLEX-02: BLOCKED UNTIL SEPARATE OWNER GO
```

---

## Corrected semantics (summary)

| Topic | Binding truth |
|-------|---------------|
| Membership role | **HELPER only** at FLEX-02 |
| Principal | `assigned_employee_id` only — no PRINCIPAL membership row |
| JOIN | Membership create/reactivate only |
| LEAVE | Own membership close only |
| Work proof | Sessions unchanged |

---

## Files updated

- `.compound-engineering/prod-flex-arch-02-participant-persistence-boundary/decision-log.md`
- `.compound-engineering/prod-flex-arch-02-participant-persistence-boundary/plan.md`
- `.compound-engineering/prod-flex-arch-02-participant-persistence-boundary/risk-register.md`
- `docs/worklog/realignment/2026-07-15_prod_flex_arch_02_participant_persistence_boundary.md`
- `docs/master/workos-e2e/WORKOS_E2E_STATUS.md`
- `docs/master/workos-e2e/WORKOS_E2E_TASK_GRAPH.md`

---

## What remains blocked

- FLEX-02 implementation
- Migration
- Participant writes
- Join/leave API
- Help persistence (FLEX-04)
- UI / Mobile
- Pool / `_has_active_session_by_other` changes
- Session / assignment / claim changes

---

## Next safe step

**None for implementation.** Await explicit owner GO for FLEX-02 kickoff (separate P11=YES + P10=YES). Alternate: unpause UI-TRUTH-01B or APP-AUTH-06G.

---

## DELIVERY FOOTER

```
Task: OWNER-DECISION-08-PROD-FLEX-ARCH-02-CORRECTED-SIGN-OFF
Starting HEAD: 43668f9
Architecture: ACCEPTED_WITH_CORRECTIONS
P7: HELPER_ONLY
P8: JOIN_MEMBERSHIP_ONLY
P9: LEAVE_OWN_MEMBERSHIP_ONLY
P10 migration: NO
P11 FLEX-02: NO
Participant writes: NOT_AUTHORIZED
UI: NO
DB: NO
FLEX-02 started: NO
Push: NO
PR: NO
Verdict: OWNER_DECISION_08_PROD_FLEX_ARCH_02_CORRECTED_SIGN_OFF_COMPLETE
```
