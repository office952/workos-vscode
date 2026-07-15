# PROD-FLEX-COLLABORATION-PHASE-1 — Implementation Worklog

**Task:** PROD-FLEX-COLLABORATION-PHASE-1-IMPLEMENTATION  
**Date:** 2026-07-16  
**Starting HEAD:** `67a2c82`  
**Owner GO:** AUTHORIZED (membership + migration + join/leave + read v1.1)

---

## Checkpoint A — Persistence foundation

**Done:**
- Model `ExecutionTaskParticipant` (`backend/models/execution_task_participant.py`)
- Alembic `s57_create_execution_task_participants` off `s56`
- Unique `(order_id, task_id, employee_id)`; soft `order_id`; hard `employee_id` FK CASCADE
- Registered in `models/__init__.py`
- Flag module `services/flex_membership_flags.py` (`FLEX_MEMBERSHIP_API_ENABLED`, default true)

**Migration proof:** upgrade to `s57` / downgrade to `s56` / upgrade again on temp SQLite — table + unique present.  
Note: repo still has orphan alembic head `s50_execution_plan_prepared_by_clarification_target`; use explicit revision `s57_create_execution_task_participants` (not bare `head`).

---

## Checkpoint B — Membership behavior

**Done:**
- `execution_task_membership_service.py` — join / leave / list / order-by-task projection
- V2-materialized gate only (`STATUS_V2_OPERATIONAL_READY`)
- Eligibility via `OperationalRegistryService` on `process_type`
- Idempotent join/leave; reactivation same row; IntegrityError race path
- asyncio per-task lock + `SELECT FOR UPDATE`
- Routes:
  - operator join/leave/memberships
  - employee-mobile join/leave (self only)
- No session / assignment / claim side effects

---

## Checkpoint C — Read + runtime

**Done:**
- Collaboration read bumped to `execution_task_collaboration_read/v1.1`
- Additive `helper_memberships[]` + `authorized_helper_count`
- OpenAPI manifest updated with join/leave paths
- Tests: `test_execution_task_participants.py` + updated FLEX-01 version asserts

**Pytest (focused):**
- `test_execution_task_participants.py` + `test_execution_task_collaboration_read.py` → **32 passed**
- Regressions: sessions + claim concurrency + assignment → **15 passed**

**Runtime (order 23099, `:8001`):**
| Step | Result |
|------|--------|
| Baseline read | v1.1, 13 tasks, helpers=0 |
| JOIN emp=4 (Sandu) | 200, active |
| Read after join | helpers=1, workers=0 (no session created), assigned unchanged, op_completed=false |
| LEAVE | 200, inactive |
| REJOIN | 200, reactivated=true |
| Idempotent JOIN | already_joined=true |
| Cleanup LEAVE | 200 |

Task ID: `node:root_product:TPL-VOLUMETRIC-LETTERS_v2:vector_prep`

Prep note: ensured Sandu eligibility for `file_preparation` via registry upsert (local verification only).

---

## Forbidden scope confirmation

No help table, pools, `_has_active_session_by_other`, session start, UI, Mobile UX, Product System, snapshots, assignment/claim behavior changes.

---

## Independent review

**Verdict:** PASS_WITH_NOTES  
**Fixed in-scope:** missing `import json`; claim-after-membership regression coverage; IntegrityError path sets `role=HELPER`.  
**Deferred:** orphan alembic multi-head (`s50_*`); UI consumers (Phase 3).

---

## Commits

1. `feat(execution): add collaboration membership persistence`
2. `feat(execution): add helper membership join and leave`
3. `feat(execution): expose helper memberships in collaboration read`

Canonical: STATUS/TASK_GRAPH → Phase 1 COMPLETE.  
Reusable note: `docs/solutions/collaboration-membership-helper-only.md`

**Final verdict:** `PROD_FLEX_COLLABORATION_PHASE_1_COMPLETE`
