# MOBILE-T03 — Employee Mobile Blocker and Readiness Visibility V1

**Task:** MOBILE-T03 — `EMPLOYEE_MOBILE_BLOCKER_AND_READINESS_VISIBILITY_V1`  
**Date:** 2026-07-15  
**Starting HEAD:** `9d31d7f`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Verdict:** `MOBILE_BLOCKER_READINESS_PASS_COMMITTED`

## Objective

Make mobile readiness and production blockers understandable and actionable for employees — visibility and guidance only. No manager resolution, no start/claim wiring, no frontend policy authority.

## Pre-implementation field map

| Field | Source |
|-------|--------|
| `is_startable`, `readiness_status`, `readiness_label`, `readiness_reasons`, `blocking_task_ids`, `blocking_tasks`, `material_warning`, `dependency_warning` | `task_readiness_service` → `employee_safe_readiness_payload` |
| `production_release_blocked`, `production_blocker_summary` | `evaluate_production_release` + `_production_blocker_summary` |
| `status`, `started_at`, `completed_at`, assignment flags | execution reality + truth composition |
| Primary labels (Pregătit, În lucru, …) | **DISPLAY_ONLY** projection in `employeeMobileV2BlockerPresentation.ts` |
| `can_start` / action permissions | backend guards (mobile start route unchanged) |

## Implementation

- **`employeeMobileV2BlockerPresentation.ts`** — backend-bound taxonomy: Producție, Pregătire, Materiale, Alocare, Stare task; primary readiness states; manager escalation copy; diagnostic codes (expandable).
- **`EmployeeMobileV2BlockerBadges.tsx`** — list/detail badges (readiness + production block + blocker count).
- **`EmployeeMobileV2TaskRow.tsx`** — concise card: badge, short reason, manager escalation when production-blocked.
- **`EmployeeMobileV2TaskTruthPanels.tsx`** — structured detail: Poate începe?, Producție, Pregătire, Materiale, Alocare, Diagnostic.
- **`EmployeeMobileV2WorkRoomActionBar.tsx`** — `START_DISABLED_WITH_BACKEND_REASON` when assigned but not startable.
- **`employeeMobileV2BlockerFixtures.ts`** — deterministic fixture tasks for all blocker scenarios.
- **`employeeMobileV2TaskErrors.ts`** — extended structured error messages (order/task not found, invalid state, network).

## Frontend authority audit

| Pattern | Classification |
|---------|----------------|
| `buildEmployeeMobileV2BlockerPresentation` | `DISPLAY_ONLY` |
| `isAvailableTaskStartable` / WorkRoom `canStart` | `BACKEND_BOUND_VALIDATION` (reads `task.is_startable`) |
| `employeeMobileShopFloorPresentation` status | `LEGACY_ISOLATED` (v1 / pipeline paths) |
| Local `is_startable` calculation | **NONE** in v2 blocker path |

## Boundaries preserved

| Boundary | Classification |
|----------|----------------|
| Start action wiring | `START_DISABLED_WITH_BACKEND_REASON` — disabled + backend reason; active start only when `is_startable === true` |
| Claim | `KEEP_FOR_MOBILE_T06` |
| Manager resolution | Desktop-only (`MOBILE_READONLY_BLOCKERS_DESKTOP_RESOLUTION`) |
| Pause/resume/complete | `EXISTING_START_PRESERVED_NOT_REWORKED` (unchanged action bar) |

## Runtime verification (Sandu, order 23099, :8001/:3000)

| Check | Result |
|-------|--------|
| Truth API | 12 tasks, assigned 5, available 7 |
| Production-blocked card | `node:…:vector_prep` — badge + manager escalation |
| Predecessor/file detail | `cnc_face_cut` waiting_file |
| Available not startable | 7 waiting_predecessor tasks in Disponibile |
| In-progress | vector_prep in_progress |
| Manager escalation | Desktop copy on production detail |
| No resolve controls | PASS |
| Snapshot/plan mutation | NO |

## Tests

| Category | Passed | Failed | Skipped |
|----------|--------|--------|---------|
| Focused backend (`truth` + `mobile_tasks`) | 35 | 0 | 0 |
| Extended backend (+ production guard) | 60 | 2 pre-existing | 0 |
| Focused frontend (blocker + errors + truth + app) | 38 | 0 | 0 |

Pre-existing backend failures (unchanged): `test_employee_mobile_start_route_guarded`, `test_employee_mobile_start_blocked_cnc_without_vector_prep` (422 vs 409).

## Screenshots

`docs/qa/product-system-active-path-isolation-v1/mobile_t03_screenshots/` — 13 captures @ 390×844 (live + routed fixture for material/allowed/errors).

## Owner visual verification

### Blocked task
- **URL:** `/employee-app-v2/tasks/node:root_product:TPL-VOLUMETRIC-LETTERS_v2:vector_prep?orderId=23099`
- **Expected:** Producție blocată badge, production summary, manager escalation, Start disabled

### Readiness blocker
- **Task:** `cnc_face_cut` waiting_file
- **Expected:** Pregătire section with file/predecessor reasons

### Allowed task
- **Fixture:** `fixture-ready` (mocked route for screenshot)
- **Expected:** Pregătit, no production block, Poate începe? = Da

## Next task

**MOBILE-T04-START-ACTION-WIRING**
