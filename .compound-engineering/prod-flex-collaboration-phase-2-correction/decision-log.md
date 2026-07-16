# PROD-FLEX-COLLABORATION-PHASE-2-CORRECTION — Decision Log

**Date:** 2026-07-16  
**Upstream:** Phase 2 closure audit at HEAD `17af5f6`  
**Status:** AWAITING OWNER GO

## Owner gates

| Gate | Decision | Status |
|------|----------|--------|
| G1 | Authorize correction implementation? | _pending_ |
| G2 | Requester-only cancel? | _pending_ (plan recommends YES) |
| G3 | Operator override cancel now? | _pending_ (plan recommends NO / defer) |
| G4 | Lock reality row on helper/employee session start? | _pending_ (plan recommends YES) |
| G5 | Block Phase 3 until correction re-closes? | _pending_ (plan recommends YES) |

## Locked product corrections (plan)

1. Cancel actor must equal `requested_by_employee_id` (unless G3 later adds override).  
2. Completing an operation must close remaining OPEN help; retries must not skip closer.  
3. Memberships never revoked by cancel/close/completion.  
4. Helper cannot hold two active sessions on the same task across workers.  
5. OPEN uniqueness must exist for create_all and migrated DBs.  
6. No UI in this phase.

## Explicitly not decided here

- Phase 3 screen layout  
- Mobile vs Operator primacy for UX  
- Orphan s50 Alembic merge
