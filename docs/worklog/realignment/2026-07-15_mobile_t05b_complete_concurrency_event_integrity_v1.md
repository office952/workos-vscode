# MOBILE-T05B — Employee Mobile Complete Concurrency and Event Integrity V1

**Task:** MOBILE-T05B — `EMPLOYEE_MOBILE_COMPLETE_CONCURRENCY_AND_EVENT_INTEGRITY_V1`  
**Date:** 2026-07-15  
**Starting HEAD:** `95f3b5c`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Verdict:** `MOBILE_T05B_CONCURRENCY_PASS_CLOSE_MOBILE_T05`

## Objective

Prove concurrent Complete safety: two overlapping `PATCH /api/v1/employee-mobile/tasks/{task_id}/complete` requests against one active session must close exactly one session, emit exactly one completion event, and return stable responses without duplicate mutations.

## Complete transaction trace

| Step | Layer | Authority |
|------|-------|-----------|
| 1 | Auth + `require_employee_self_user` | `resolve_employee_for_user` → employee id |
| 2 | Router `complete_task` | `TaskOrderRef.order_id` + path `task_id` |
| 3 | `complete_my_task` | `_get_task_context` (plan + reality JSON) |
| 4 | Ownership | `task_belongs_to_employee` → 403 if not assigned |
| 5 | Idempotency gate | `derive_task_status_for_employee == done` → `already_completed` |
| 6 | Active session gate | `active_session_for_employee` + started_at |
| 7 | Mutation | `ExecutionRealityService.end_task(for_update=True)` |
| 8 | Session close | `close_work_session` on `execution_reality.tasks_json` entry |
| 9 | Commit | Single transaction on `execution_reality` row |
| 10 | Response | Mobile list/truth refetch (client-side) |

**Completion event store:** `execution_reality.tasks_json` — session entry with `ended_at`, `status=completed`, `completed_by_employee_id`, `completed_by_employee_name`. No separate audit table for mobile Complete.

## Transaction / locking model

| Mechanism | Present |
|-----------|---------|
| Transaction boundary | `end_task` commit on `execution_reality` row |
| Row lock | `SELECT … FOR UPDATE` on `execution_reality` in `end_task` |
| Compare-and-set | Skip entries with existing `ended_at`; idempotent return if completed session exists for employee+task |
| Unique DB constraint on completion | No (JSON array); integrity enforced by row lock + ended_at guard |
| Sequential idempotency | `status == done` short-circuit before active-session requirement |
| Concurrent loser | `end_task` idempotent path returns committed row; HTTP 200 stable |

**SQLite vs production:** Service-level race tests prove logic; `FOR UPDATE` behavior differs on SQLite (table lock) vs Postgres (row lock) but serializes concurrent writers on the same order row in both cases.

**Desktop Complete:** Same `complete_my_task` → `ExecutionRealityService.end_task` path via employee-mobile router.

## Current behavior classification

**`CONCURRENT_COMPLETE_IDEMPOTENT`**

| Request | Live :8001 response |
|---------|---------------------|
| Winner | 200 `{ action: complete, timestamp }` |
| Loser (overlap) | 200 `{ action: complete, timestamp }` (idempotent `end_task`; no second close) |

Post-race DB: closed sessions = 1, active = 0, completion events = 1.

## Active session ID gap

**`SESSION_ID_NOT_REQUIRED_ENDPOINT_RESOLVES_CANONICALLY`**

Mobile truth omits `active_session_id`; Complete resolves the canonical active session from order + task + employee via `execution_reality.tasks_json`. Presentation-only gap; does not block mutation or event correlation for Complete.

## Idempotency matrix

| Scenario | Event count | Result |
|----------|-------------|--------|
| Sequential repeat | 1 | PASS — second returns `already_completed: true` |
| Concurrent overlap | 1 | PASS — both 200, one close |
| Retry after commit | 1 | PASS — `already_completed: true` |

## Ownership concurrency

Concurrent owner + intruder: owner 200, intruder 403/422, completion events for owner only = 1.

## Backend fix (narrow)

1. **`complete_my_task`:** Check `status == done` before requiring active session (fixes sequential/retry 422 after first complete).
2. **`ExecutionRealityService.end_task`:** `FOR UPDATE` + idempotent return when completed session already exists for employee+task.

No frontend changes.

## Tests

| Category | Passed | Failed | Skipped | Collection errors |
|----------|--------|--------|---------|-------------------|
| Focused concurrency (`test_employee_mobile_complete_concurrency.py`) | 6 | 0 | 0 | 0 |
| Mobile Complete/session/truth regressions | 49 | 0 | 0 | 0 |
| Frontend MOBILE-T02–T05 regressions | 40 | 0 | 0 | 0 |
| ExecutionReality capture (regression note) | 14 | 2 | 0 | 0 |

**ExecutionReality failures:** Pre-existing start-readiness gate tests (`409 task_not_ready` vs expected `422` duplicate start) — unrelated to Complete concurrency.

## Live HTTP runtime

| Check | Result |
|-------|--------|
| Backend | `http://127.0.0.1:8001` |
| Fixture | Isolated order `92350`, task `T-M05B-CONC-COMPLETE` |
| Overlap | ~3.6ms (barrier-synchronized) |
| Post-state | closed=1, active=0, events=1, status=done |
| Truth/list | 200 stable |
| Plan/snapshot | Unchanged |

Evidence: `docs/qa/product-system-active-path-isolation-v1/mobile_t05b_concurrency_evidence.json`  
Probe: `backend/scripts/mobile_t05b_complete_concurrency_probe.py`

## MOBILE-T05 final status

**COMPLETE** (functionality + concurrency closure)

## Next task

**MOBILE-T06-CLAIM-AND-ASSIGNMENT-POLICY**

## Commits

- Application: concurrency idempotency + locking + focused tests
- Docs/evidence: worklog, status, task graph, live probe evidence
