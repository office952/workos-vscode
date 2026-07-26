# MOBILE-T04 — Employee Mobile Canonical Start Action V1

**Task:** MOBILE-T04 — `EMPLOYEE_MOBILE_CANONICAL_START_ACTION_V1`  
**Date:** 2026-07-15  
**Starting HEAD:** `05cb63f`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Verdict:** `MOBILE_START_ACTION_PASS_COMMITTED`

## Objective

Wire Employee Mobile V2 Start to canonical backend mutation paths (assigned PATCH start + available POST start-from-available). No pause/resume/complete expansion, no frontend mutation authority, no optimistic in-progress.

## Pre-implementation contract trace

| Path | Classification |
|------|----------------|
| Assigned | `CANONICAL_ASSIGNED_START` — `PATCH /api/v1/employee-mobile/tasks/{task_id}/start` + `{order_id}` → `require_employee_self_user` → `start_my_task` → `assert_task_startable` → `ExecutionRealityService.start_task(source=employee_mobile)` |
| Available | `CANONICAL_ATOMIC_CLAIM_AND_START` — `POST …/start-from-available` → readiness gate → `assign_plan_task` → `start_my_task` with assignment rollback on failure |

Payload: `{ order_id }` only — no `employee_id` from client.

## Implementation

### Backend
- `can_start_from_available` on `EmployeeMobileTaskReadiness` truth schema
- Projected in `employee_mobile_task_truth_service` and available rows in `employee_mobile_tasks_service`

### Frontend
- **`employeeMobileV2StartAction.ts`** — canonical client: mode resolution, `executeEmployeeMobileStart`, structured error map, labels (`Încep task`, `Preia și pornește`)
- **`useEmployeeMobileV2StartAction.ts`** — shared pending state keyed by `order_id:task_id`
- Wired: `EmployeeMobileV2WorkRoomActionBar`, `EmployeeMobileV2AvailableTasksSection`, `EmployeeMobileV2AvailablePreviewActionBar`
- **`employeeMobileV2AvailableTasks.ts`** — partition uses `can_start_from_available` / `can_start` (not raw `is_startable` alone)
- Mutation strategy: **`DETAIL_PRIMARY_CARD_SHORTCUT`** (detail primary; card shortcut optional, default off)

## Guards and ExecutionReality

| Guard | Result |
|-------|--------|
| Production release | `assert_production_release_allowed` on both paths — PASS (backend tests) |
| Readiness | Shared `assert_task_startable` / readiness service — PASS |
| ExecutionReality | `EXECUTIONREALITY_START_COMPLETE` — session/event via `ExecutionRealityService.start_task` |
| Auth employee mapping | `AUTH_EMPLOYEE_MAPPING_CANONICAL` — employee from session, not client payload |
| Legacy v1 | `LEGACY_V1_SHARED_CANONICAL_MUTATION` (same service layer; no bypass observed) |

## Frontend authority audit

| Pattern | Classification |
|---------|----------------|
| `executeEmployeeMobileStart` / hook | `BACKEND_BOUND_VALIDATION` |
| Pending state only | `DISPLAY_ONLY` |
| Optimistic in-progress / local assign | **NONE** |
| Endpoint selection | Backend `can_start` / `can_start_from_available` only |

## Previous T03 failing tests (reclassification)

| Test | Isolated | Combined suite | Classification |
|------|----------|----------------|----------------|
| `test_employee_mobile_start_route_guarded` | PASS | intermittent | `PREEXISTING_FIXTURE_DEBT_CONFIRMED` |
| `test_employee_mobile_start_blocked_cnc_without_vector_prep` | PASS | intermittent | `PREEXISTING_FIXTURE_DEBT_CONFIRMED` |

## Tests

| Category | Passed | Failed | Skipped |
|----------|--------|--------|---------|
| Focused backend (mobile tasks + truth + guards) | 37 | 0 | 0 |
| Focused frontend (start action + app integration) | 32 | 0 | 0 |

Commands:
- `pytest tests/test_employee_mobile_tasks.py tests/test_employee_mobile_task_truth.py …` — 37 passed
- `vitest run src/lib/employeeMobileV2StartAction.test.ts src/pages/EmployeeMobileV2App.test.tsx` — 32 passed

## Runtime verification (Sandu, :8001/:3000, order 23099)

| Scenario | Result |
|----------|--------|
| Live production-blocked assigned detail | Disabled start + manager escalation (`vector_prep` in progress on spine) |
| Live readiness-blocked | `cnc_face_cut` waiting_file — structured readiness panel |
| Assigned ready + start pending + success | Routed fixture (spine order fully production-blocked) |
| Available atomic start | Routed fixture — `Preia și pornește` → POST start-from-available |
| Ownership conflict error | Routed fixture — structured action error |
| Snapshot/plan mutation | NO |

## Screenshots

`docs/qa/product-system-active-path-isolation-v1/mobile_t04_screenshots/` — **14** captures @ 390×844 (live + routed fixtures per T03 pattern).

## Temporary debt

| Item | Classification |
|------|----------------|
| Pause/resume/complete | `KEEP_FOR_MOBILE_T05` |
| Claim-only / assignment audit | `KEEP_FOR_MOBILE_T06` |
| Manager resolution | Desktop-only |
| Offline mutation queue | `MOBILE_FUTURE_ENHANCEMENT` |
| Card-level start shortcut | `MOBILE_FUTURE_ENHANCEMENT` (default off) |

## Next task

**MOBILE-T05-IN-PROGRESS-SESSION-AND-COMPLETE**
