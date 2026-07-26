# MOBILE-T02 — Assigned / Available Task List and Detail V1

**Task:** MOBILE-T02 — `EMPLOYEE_MOBILE_ASSIGNED_AVAILABLE_TASK_LIST_AND_DETAIL_V1`  
**Date:** 2026-07-15  
**Starting HEAD:** `e9fcb86`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Verdict:** `MOBILE_TASK_LIST_DETAIL_PASS_COMMITTED`

## Objective

Wire Employee Mobile V2 list and task-detail surfaces to `employee_mobile_task_truth/v1` with backend-owned assigned/available partitioning, identity/readiness/production presentation, and distinct error vs empty states.

## Root cause (before)

V2 list/detail used separate `GET /tasks` and `GET /tasks/available` adapters. Cards showed `title || task_id` without `display_label`, `component_label`, or production-block summaries. Detail lacked structured Identitate/Stare/Pregătire/Producție sections.

## Implementation

- **Canonical source:** `EmployeeMobileV2TaskTruthProvider` + `useEmployeeMobileV2TaskTruthContext()` — single fetch of `GET /api/v1/employee-mobile/tasks/truth`, nested response mapped to flat DTO via `employeeMobileV2TaskTruth.ts`.
- **List IA:** În lucru → Sarcinile mele → Disponibile → Finalizate (backend flags only).
- **Cards:** `resolveTaskDisplayTitle`, `resolveTaskComponentLine`, order reference, production block summary from backend.
- **Detail:** `EmployeeMobileV2TaskTruthPanels` — Identitate, Stare, Pregătire, Producție, Dependențe.
- **Errors:** `employeeMobileV2TaskErrors.ts` maps `employee_link_missing`, `MOBILE_V2_*`, network.
- **Removed frontend authority:** `planSequenceOf` no longer parses `T-(\d+)` from task_id; uses `plan_sequence` only.

## Boundaries preserved

| Boundary | Classification |
|----------|----------------|
| Claim | `CLAIM_PRESENTATION_ONLY_DEFER_TO_MOBILE_T06` |
| Start | `START_VISIBILITY_ONLY` / `START_ACTION_REQUIRES_MOBILE_T04` |
| Legacy v1 | `LEGACY_V1_ISOLATED` |

## Runtime verification (Sandu, order 23099, :8001/:3000)

| Check | Result |
|-------|--------|
| Truth API | 12 tasks, assigned 5, available 7 |
| Assigned UI | Root/mounting/logo identities visible |
| Available UI | 7 backend-declared claimable tasks |
| Detail | Canonical task ID route + readiness + production block |
| Snapshot/plan mutation | NO |

## Tests

| Suite | Result |
|-------|--------|
| `test_employee_mobile_task_truth.py` | 10 passed |
| `employeeMobileV2TaskTruth.test.ts` + `EmployeeMobileV2App.test.tsx` | 18 passed |
| `test_employee_mobile_tasks.py` (full) | 34 passed, 1 pre-existing fixture bleed |

## Screenshots

`docs/qa/product-system-active-path-isolation-v1/mobile_t02_screenshots/` — 12 captures @ 390×844.

## Next task

**MOBILE-T03-BLOCKER-READINESS-VISIBILITY**
