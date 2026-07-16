# PROD-FLEX-COLLABORATION-PHASE-2 — Owner Decision Log

**Task:** PROD-FLEX-COLLABORATION-PHASE-2-RESEARCH-AND-IMPLEMENTATION-PLAN  
**Date:** 2026-07-16  
**Status:** **PHASE 2 PLAN READY FOR OWNER REVIEW**  
**Starting HEAD:** `18398c1`  
**Plan:** `.compound-engineering/prod-flex-collaboration-phase-2/plan.md`  
**Upstream:** Phase 1 `PROD_FLEX_COLLABORATION_PHASE_1_ACCEPTED_WITH_DOCUMENTED_LIMITATION`; OWNER-DECISION-08

---

## Architecture already accepted (not re-decided)

| Decision | Status |
|----------|--------|
| OPTION 5 hybrid (membership + help later + sessions) | **ACCEPTED** |
| HELPER-only membership; no PRINCIPAL row | **ACCEPTED** |
| Sessions = work/time authority | **ACCEPTED** |
| `assigned_employee_id` = optional principal | **ACCEPTED** |
| JOIN/LEAVE = membership only | **ACCEPTED** |
| `participants_json` rejected | **ACCEPTED** |
| Membership without help (`self_join`) | **ACCEPTED** (Phase 1 G9) |
| Phase 1 Mobile API surface (no UX) | **ACCEPTED WITH LIMITATION** |

---

## Plan-locked design (owner confirms via G1)

These are the plan’s technical locks. Signing G1 accepts them unless an owner rewrite is requested:

| Lock | Value |
|------|-------|
| Help model | **Broadcast OPEN** + membership-as-acceptance |
| Open multi-accept | Many helpers; request stays OPEN |
| Targeted accept | One target; request → `CLOSED` |
| Singular `accepted_by` | **Rejected** as authority |
| Acceptance child table / quota | **Deferred** (not Phase 2) |
| Help statuses | `OPEN` \| `CANCELLED` \| `DECLINED` \| `CLOSED` (no multi-helper `ACCEPTED`) |
| Cancel after accepts | Does **not** revoke memberships |
| Capability flags | Visibility ≠ claim/assign/complete |
| Help flags | `can_view_help` / `can_accept_help` / `can_start_helper_work` |
| Helper sessions | Required `employee_id`; stop ≠ complete |
| Guard | Keep `_has_active_session_by_other` on principal claim pool only |
| Migration | `s58` ← `s57`; orphan `s50` untouched; no bare `head` |

---

## Phase-level decisions required (owner GO)

| ID | Question | Plan recommendation | Owner answer |
|----|----------|---------------------|--------------|
| **G1** | Authorize Phase 2 one-GO Option C with **broadcast OPEN** multi-accept model? | **YES** | _pending_ |
| **G2** | Preserve `self_join` / `manager_add` without help request? | **YES** | _pending_ |
| **G3** | Claim remains principal-only; capability flags separate helper visibility from principal powers? | **YES** | _pending_ |
| **G4** | Keep `_has_active_session_by_other` on principal pool only (bypass for ajutor / helper start)? | **YES** | _pending_ |
| **G5** | No leave+stop combo; no acceptance child table / helper quota in Phase 2? | **YES** | _pending_ |
| **G6** | No Operator / Mobile UI in Phase 2? | **YES** | _pending_ |
| **G7** | Leave orphan Alembic `s50_execution_plan_*` untouched? | **YES** | _pending_ |
| **G8** | Extend Operator + Employee Mobile **APIs** (no UX) for help, pools, helper sessions? | **YES** | _pending_ |

**Not owner decisions:** exact column names, optional `source_help_request_id` on membership, concrete route path strings — implementer owns at `/ce-work`.

---

## Recommended GO boundary (one approval)

If owner accepts G1–G8 as recommended:

```
PHASE-2 GO GRANTED:
  Migration s58 help_requests:     YES (broadcast OPEN model)
  Help lifecycle APIs:             YES
  Accept → membership help_accept: YES
  manager_add wiring:              YES
  Split pools + capabilities:      YES
  Helper session start/stop:       YES (employee_id required)
  Guard realignment (scoped):      YES
  Collab read v1.2:                YES
  Feature flag:                    YES
  Tests + runtime proof:           YES
  Acceptance child table / quota:  NO
  Leave+stop combo:                NO
  Orphan s50 merge:                NO
  UI / Mobile UX:                  NO
  Product System / snapshots:      NO
  Auto assign / claim / complete:  NO
```

---

## Explicitly blocked until future GO

| Item | Blocked until |
|------|---------------|
| Phase 2 code / migration | G1 owner sign-off |
| Operator / Mobile collaboration UI | Phase 3 GO |
| Helper quota / acceptance child table | Future product GO |
| Leave+stop combined command | Future contract GO |
| Orphan Alembic merge | Migration hygiene GO |
| PRINCIPAL membership row | New architecture decision |
| `participants_json` | Permanent rejection |

---

## Gate outcomes

| Event | Outcome |
|-------|---------|
| Owner signs G1–G8 as recommended | May start `/ce-work` Phase 2 implementation |
| Owner rejects G1 | Phase 2 remains PLAN ONLY; no code |
| Owner wants different help model | Plan revision required before GO |
| Owner wants UI in Phase 2 | Re-scope required — contradicts plan |

---

## Sign-off block (owner)

```
PROD-FLEX-COLLABORATION-PHASE-2 OWNER REVIEW
Date: __________
Verdict: ACCEPT / REVISE / REJECT

G1 Broadcast OPEN Phase 2 GO:     YES / NO
G2 self_join / manager_add:       YES / NO
G3 Capability separation:         YES / NO
G4 Scoped session guard:          YES / NO
G5 No quota / leave+stop:         YES / NO
G6 No UI:                         YES / NO
G7 Orphan s50 untouched:          YES / NO
G8 Mobile/Operator API extend:    YES / NO

Notes:
_________________________________
```
