# PROD-FLEX-COLLABORATION-PHASE-1 — Owner Decision Log

**Task:** PROD-FLEX-COLLABORATION-PHASE-1-IMPLEMENTATION-PLAN  
**Date:** 2026-07-15  
**Status:** **PLAN READY FOR OWNER REVIEW**  
**Upstream:** OWNER-DECISION-08 (architecture accepted; implementation blocked)

---

## Architecture Already Accepted (not re-decided here)

| Decision | Status |
|----------|--------|
| OPTION 5 hybrid shape | **ACCEPTED** |
| `(order_id, task_id)` parent identity | **ACCEPTED** |
| HELPER-only membership | **ACCEPTED** |
| Sessions = work authority | **ACCEPTED** |
| `assigned_employee_id` = optional principal | **ACCEPTED** |
| JOIN = membership only | **ACCEPTED** |
| LEAVE = own membership only | **ACCEPTED** |
| `participants_json` rejected | **ACCEPTED** |

---

## Phase-Level Decisions Required (owner GO)

| ID | Question | Plan recommendation | Owner answer |
|----|----------|---------------------|--------------|
| **G1** | Authorize Phase 1 implementation (membership foundation)? | **YES** — single coherent backend phase | _pending_ |
| **G2** | Authorize migration (`execution_task_participants`)? | **YES** — one `s57` revision | _pending_ |
| **G3** | Authorize join/leave membership API? | **YES** — membership only; no session side effects | _pending_ |
| **G4** | Authorize collaboration read v1.1 extension? | **YES** — additive `helper_memberships[]` | _pending_ |
| **G5** | Include help-request persistence in Phase 1? | **NO** — defer to Phase 2 | _pending_ |
| **G6** | Include pool / `_has_active_session_by_other` changes? | **NO** — defer to Phase 2 | _pending_ |
| **G7** | Include helper session start in Phase 1? | **NO** — separate verb in Phase 2 | _pending_ |
| **G8** | Include UI or Mobile consumers? | **NO** — defer to Phase 3 | _pending_ |
| **G9** | Allow direct JOIN without help invitation? | **YES** — eligible employee self-join on materialized task | _pending_ |
| **G10** | Reactivation model (same row vs new row per cycle)? | **YES** — reactivate same row; unique on `(order_id, task_id, employee_id)` | _pending_ |
| **G11** | Scope restriction to V2 materialized orders only? | **YES** — legacy T-001 out of scope | _pending_ |
| **G12** | Feature flag for write endpoints? | **YES** — `FLEX_MEMBERSHIP_API_ENABLED`; reads always on | _pending_ |

---

## Recommended GO Boundary (one approval)

If owner accepts G1–G4 and G9–G12 and rejects G5–G8:

```
PHASE-1 GO GRANTED:
  Migration:              YES
  Membership writes:      YES (HELPER-only)
  Join/leave API:         YES (membership only)
  Read v1.1:              YES
  Help table:             NO
  Pool changes:           NO
  Session start on JOIN:  NO
  UI / Mobile:            NO
  LEAVE stops session:    NO
```

---

## Explicitly Blocked Until Future GO

| Item | Blocked until |
|------|---------------|
| Phase 1 code/migration | G1+G2 owner sign-off |
| Help persistence | Phase 2 GO |
| Split pools | Phase 2 GO |
| Helper work session API | Phase 2 GO |
| Operator/Mobile UI | Phase 3 GO |
| PRINCIPAL membership row | New owner architecture decision |
| `participants_json` | Permanent rejection |

---

## Gate Outcomes

| Event | Outcome |
|-------|---------|
| This plan accepted | `PHASE-1 PLAN READY` — still no code |
| Owner grants G1–G4 | May start Phase 1 implementation |
| Owner rejects G5–G8 inclusion | Phase stays bounded; no scope creep |
| Owner wants help in Phase 1 | **Re-scope required** — plan revision before GO |
| Owner wants UI in Phase 1 | **Re-scope required** — plan revision before GO |

**Plan acceptance does not authorize implementation.**

---

## Sign-off Block (template)

```
PHASE-1 PLAN: PROD-FLEX-COLLABORATION-PHASE-1
Date: ___________
Owner: ___________

G1  Phase 1 implementation:     YES / NO
G2  Migration:                   YES / NO
G3  Join/leave API:              YES / NO
G4  Read v1.1 extension:         YES / NO
G5  Help in Phase 1:             YES / NO  (plan recommends NO)
G6  Pool changes in Phase 1:     YES / NO  (plan recommends NO)
G7  Session start in Phase 1:    YES / NO  (plan recommends NO)
G8  UI/Mobile in Phase 1:        YES / NO  (plan recommends NO)

IMPLEMENTATION AUTHORIZED:  NO (until signed)
MIGRATION AUTHORIZED:       NO (until signed)
```

Worklog: `docs/worklog/realignment/2026-07-15_prod_flex_collaboration_phase_1_plan.md`
