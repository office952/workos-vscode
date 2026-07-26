# MOBILE-T06 — Employee Mobile Claim and Assignment Policy V1

**Task:** MOBILE-T06 — `EMPLOYEE_MOBILE_CLAIM_AND_ASSIGNMENT_POLICY_V1`  
**Date:** 2026-07-15  
**Starting HEAD:** `7860daa`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Verdict:** `MOBILE_CLAIM_ASSIGNMENT_PASS_COMMITTED`

## Objective

Prove and complete the canonical assignment model for Employee Mobile: manager assign + employee self-claim, atomic claim-only and claim-and-start, concurrency safety, assignment audit metadata, failed-start rollback, and no frozen identity/snapshot mutation.

## Assignment authority trace

| Path | Entry | Service | Storage | Mobile refresh |
|------|-------|---------|---------|----------------|
| Manager assign | `PATCH /api/v1/execution/plan/{order_id}/tasks/{task_id}/assign` | `assign_plan_task(allow_reassign=True, assignment_source=manager_assign)` | `execution_plan.tasks_json[].assigned_employee_id` | Truth refetch |
| Claim-only | `POST /api/v1/employee-mobile/tasks/{task_id}/claim` | `claim_my_task` → `assign_plan_task` | same operational field | Truth refetch |
| Claim-and-start | `POST /api/v1/employee-mobile/tasks/{task_id}/start-from-available` | readiness gate → `assign_plan_task` → `start_my_task`; rollback `clear_plan_task_assignment` on HTTP failure | same | Truth refetch |

**Frozen truth unchanged:** task_id, component ownership, dependencies, quote/order snapshot — assignment mutates only operational `assigned_employee_id` (+ `assignment_source`, `assignment_updated_at`) inside `tasks_json`.

## Policy classifications

| Field | Classification |
|-------|----------------|
| Assignment policy | `MIXED_MANAGER_ASSIGNMENT_AND_EMPLOYEE_SELF_CLAIM` |
| Assignment storage | `execution_plan.tasks_json.assigned_employee_id` |
| Claimability contract | `MOBILE_ASSIGNMENT_CAPABILITY_COMPLETE` |
| Claim-only | `CLAIM_ONLY_CANONICAL_KEEP_SECONDARY` |
| Claim-and-start | `TRANSACTIONAL_ASSIGN_AND_START_ROLLBACK` |
| Failed-start assignment | `TRANSACTIONAL_ASSIGN_AND_START_ROLLBACK` |
| Reassignment | `MANAGER_REASSIGN_ALLOWED_BEFORE_START` |
| Unassignment | `NO_UNASSIGNMENT_IN_V1` |
| Assignment audit | `ASSIGNMENT_AUDIT_REFERENCE_SUFFICIENT` |
| Claim UX | `START_FROM_AVAILABLE_PRIMARY_CLAIM_SECONDARY` |
| Legacy v1 | `LEGACY_V1_SEPARATE_GUARDED` |
| ExecutionReality red tests | `START_GUARD_ORDERING_CORRECT_TEST_OUTDATED` |
| Frontend assignment authority | NO — `DISPLAY_ONLY` + `BACKEND_BOUND_VALIDATION` |

## Backend changes

1. **`execution_task_assignment_service`:** per-task asyncio lock + `FOR UPDATE`; conflict `409 task_already_assigned`; idempotent same-employee; metadata `assignment_source`, `assignment_updated_at`; latest plan row when duplicates exist.
2. **`claim_my_task`:** assignment authority delegated to `assign_plan_task`; `already_claimed` from `already_assigned`.
3. **`start-from-available`:** validate readiness → assign → start; `clear_plan_task_assignment` on start failure (existing T04 path, proven).
4. **Manager assign router:** passes `allow_reassign=True`, `assignment_source=manager_assign`.

## Frontend changes

1. Secondary **Preiau sarcina** when `can_claim` and not primary start-from-available (`employeeMobileV2ClaimAction.ts`, `useEmployeeMobileV2ClaimAction.ts`, `EmployeeMobileV2WorkRoomActionBar.tsx`).
2. Background truth/detail refresh after actions preserves success/conflict feedback (`useEmployeeMobileV2TaskTruth`, `useEmployeeMobileV2TaskDetail`, `refreshAfterAction`).

## Tests

| Suite | Result |
|-------|--------|
| `test_employee_mobile_claim_concurrency.py` | 3 passed |
| `test_employee_mobile_tasks.py` | pass (regression) |
| `test_employee_mobile_complete_concurrency.py` | pass |
| `test_execution_task_assignment.py` | 4 passed (isolated order_ids 98101+) |
| `test_execution_reality_capture.py` | pass (ordering expectations updated) |
| Frontend claim + start | 12 passed |

**Concurrent claim:** 1 winner (`200`), 1 controlled loser (`409` or `200 already_claimed`), single DB assignee, 0 sessions.  
**Concurrent start-from-available:** 1 winner session, 1 conflict.

## Runtime (:8001 / :3000)

- Probe: `backend/scripts/mobile_t06_claim_assignment_probe.py --write-evidence`
- Fixture order `92400`, task `T-M06-CLAIM-POLICY`, employee `4` (Putaru Sandu)
- Claim-only: assignee=4, active_sessions=0
- Start-from-available: assignee=4, active_sessions=1
- Evidence: `docs/qa/.../mobile_t06_claim_assignment_evidence.json`
- Screenshots: 10 @ 390×844 — `docs/qa/.../mobile_t06_screenshots/`

## Snapshot / plan immutability

Probe and tests assert frozen task identity and snapshot fields unchanged; only operational assignment fields updated.

## Temporary debt

| Item | Classification |
|------|----------------|
| Assignment history UI | `MOBILE_FUTURE_ENHANCEMENT` |
| Employee release/unclaim | `OWNER_DECISION_REQUIRED` |
| Manager reassignment mobile UI | `LEGACY_ISOLATED` (desktop only) |
| Detailed audit timeline table | `MOBILE_FUTURE_ENHANCEMENT` |
| Pause/resume/block mobile | `KEEP_FOR_MOBILE_INT_02` (deferred) |

## Task gate

**PASS** — policy explicit, concurrency safe, audit sufficient, tests green, runtime + screenshots captured.

**Next allowed task:** `MOBILE-INT-02-POST-IMPLEMENTATION-GATE`
