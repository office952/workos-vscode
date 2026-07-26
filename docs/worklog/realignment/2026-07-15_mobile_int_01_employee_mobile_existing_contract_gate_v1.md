# MOBILE-INT-01 — Employee Mobile Existing Contract and Final Scope Gate V1

**Date:** 2026-07-15  
**Task:** MOBILE-INT-01  
**Starting HEAD:** `090997e`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Verdict:** `MOBILE_INT_01_PASS_WITH_BACKEND_PREREQUISITE`

## Objective

Audit Employee Mobile frontend/backend against frozen-spine desktop contracts. Gate only — no mobile UI implementation.

## Repository safety

- **Code changed:** NO (application code untouched)
- **Gate artifacts:** runtime proof script, screenshot script, evidence JSON, screenshots, worklog, canonical status updates

## Runtime ownership

| Surface | URL | Notes |
|---------|-----|-------|
| Trusted backend | `http://127.0.0.1:8001` | Restarted for gate (`uvicorn` reload) |
| Frontend | `http://127.0.0.1:3000` | Vite dev, `BACKEND_PORT=8001` |
| Gate employee | Putaru Sandu (`employee_id=4`) | Linked to `dev-admin-user-00000000` for dev-bypass probes |

## Primary questions (explicit)

| # | Question | Answer |
|---|----------|--------|
| 1 | Active Employee Mobile frontend routes? | **v2:** `/employee-app-v2/*` (home, tasks, task detail, pipeline, documents, blockers, upcoming, personal/*). **v1:** `/employee-app/*` parallel legacy shell still mounted. |
| 2 | Placeholders / legacy / dead? | v2 surfaces **ACTIVE_CANONICAL_SURFACE** (wired to API). v1 **ACTIVE_LEGACY_SURFACE** (parallel, not removed). Personal sub-routes partially **PLACEHOLDER** (attendance/requests reuse v1 patterns). |
| 3 | Backend endpoints serving mobile tasks? | `GET /api/v1/employee-mobile/tasks`, `/tasks/available`, `/orders/{id}/tasks/{task_id}`, `/orders/{id}/my-blueprint` |
| 4 | Start endpoint? | `PATCH /api/v1/employee-mobile/tasks/{task_id}/start` and `POST .../start-from-available` |
| 5 | Stop/complete? | `PATCH .../complete`, `PATCH .../pause`, `PATCH .../resume` (no separate “stop”; complete ends session) |
| 6 | Same task ID as ExecutionPlanV2? | **Yes** when operational tasks materialized — IDs are deterministic `task_key` strings (e.g. `node:root_product:...:vector_prep`). |
| 7 | Frozen task identity on mobile DTO? | **No** — mobile does not expose `frozen_task_identity/v1` fields. |
| 8 | Component labels? | **No** on mobile DTO; desktop `operator_task_truth/v1` has `component_label`. |
| 9 | Backend-derived startability? | **Yes** — `is_startable` from `task_readiness_service` via `employee_safe_readiness_payload`. |
| 10 | Production-release blockers? | **Start path guarded** (`assert_task_startable` → production release). Mobile read model does not surface production-release summary fields. |
| 11 | Operational readiness blockers? | **Yes** — `readiness_reasons`, `blocking_task_ids`, `blocking_tasks`, `dependency_warning`. |
| 12 | Bypass W5 production guard? | **No** — pytest `test_employee_mobile_start_route_guarded` → 409 `production_release_blocked`. |
| 13 | Direct task status writes? | **No** on start/complete (ExecutionRealityService). Pause/block/unblock patch `tasks_json` (same pattern as operator task-action). |
| 14 | ExecutionReality canonical writes? | **Start/complete: YES** (`source: employee_mobile`). Block/pause: direct JSON annotation (operator parity). |
| 15 | Assignment representation? | Plan `assigned_employee_id` + reality `employee_id` sessions; claim assigns via `assign_plan_task`. |
| 16 | Unassigned tasks visible? | **Yes** — `/tasks/available` pool (preview_only / claimable flags). |
| 17 | Start another employee's task? | **Blocked** — ownership checks → 403 `task_owned_by_other_employee`. |
| 18 | Role/permission enforcement? | `require_employee_self_user`: roles `employee_mobile|manager|admin` + linked active employee. |
| 19 | Manager owner-decision resolution in mobile? | **No** |
| 20 | Manager resolution desktop-only? | **Yes** (default policy) |
| 21 | Internal cost / commercial price exposed? | **No** in mobile DTO or v2 UI grep. |
| 22 | File/material/predecessor blockers visible? | **Partial** — readiness_reasons include material/predecessor codes; no manager notes. |
| 23 | Offline implemented? | **No** — shell copy states online-only; no service worker queue. |
| 24 | Optimistic status survives rejection? | **No** — actions await API then `onActionComplete()` reload. |
| 25 | Smallest final mobile spine? | See **Mobile implementation spine** below. |

## Critical gate finding — V2 plan loader gap

`employee_mobile_tasks_service._parse_json` accepts **legacy list** `tasks_json` only. Frozen-spine orders (`23099`, `23150`) store **V2 envelope** with `operational_tasks[]` (13 + 2 tasks materialized). Parser probe:

- `operational_tasks_count`: 13 / 2
- `legacy_list_visible_to_mobile_loader`: 0
- `mobile_loader_gap`: **true**

Runtime mobile API returns **0 tasks** despite assignments — honest empty UI in screenshots. This blocks implementation until **MOBILE-T01** adapter lands.

## Classifications

| Area | Classification |
|------|----------------|
| Task identity | `PARTIAL_IDENTITY_NEEDS_ADAPTER` |
| Mobile read model | `REDUCED_PROJECTION_FROM_CANONICAL_TRUTH` |
| Readiness | `FULL_SHARED_GATE` |
| Production release | `FULL_SHARED_GATE_PYTEST` |
| Assignment | `EMPLOYEE_SELF_CLAIM_ALLOWED` |
| Owner decisions | `MOBILE_READONLY_BLOCKERS_DESKTOP_RESOLUTION` |
| Offline | `ONLINE_ONLY_EXPLICIT` |
| Frontend authority | **NO** (`is_startable` display-only) |
| Auth mapping | `AUTH_EMPLOYEE_MAPPING_CANONICAL` (code); dev DB needs employee `user_id` link for runtime |

## Backend route inventory (summary)

| Route | Class |
|-------|-------|
| GET tasks / available / detail / blueprint | `READ_ONLY` (legacy parser gap on V2) |
| PATCH start, POST start-from-available | `CANONICAL_MOBILE_ADAPTER` + shared start gate |
| POST claim | `CANONICAL_MOBILE_ADAPTER` |
| PATCH complete | `CANONICAL_MOBILE_ADAPTER` (ExecutionRealityService) |
| PATCH pause/resume/block/unblock | `CANONICAL_MOBILE_ADAPTER` (operator-parity JSON annotation) |
| Clarification requests | `READ_ONLY` / employee-safe create |

No `ACTIVE_PARALLEL_AUTHORITY` on start/readiness — start uses shared `task_start_gate_service`.

## Tests

| Category | Passed | Failed | Skipped | Collection errors |
|----------|--------|--------|---------|-------------------|
| Backend mobile focused | 44 | 2 | 0 | 0 |
| Frontend mobile focused | 38 | 0 | 0 | 0 |
| **Total** | **82** | **2** | **0** | **0** |

Failures: `test_start_assigned_task`, `test_employee_mobile_start_flow_still_works` → `order_not_found` (**PREEXISTING_FIXTURE_DEBT**, isolated test DB).

Production guard: `test_employee_mobile_start_route_guarded` **PASS**.

## UI screenshots (9)

Path: `docs/qa/product-system-active-path-isolation-v1/mobile_int_01_screenshots/`

| File | URL | Viewport | Result |
|------|-----|----------|--------|
| 01_mobile_home_nav.png | `/employee-app-v2` | 390×844 | Home + 6 module tiles — **ACTIVE** |
| 02_assigned_task_list.png | `/employee-app-v2/tasks` | 390×844 | Empty assigned list (loader gap) |
| 03_task_detail.png | tasks (no row) | 390×844 | Same empty state |
| 04_pipeline.png | `/employee-app-v2/pipeline` | 390×844 | Pipeline shell active, no tasks |
| 05_blockers.png | `/employee-app-v2/blockers` | 390×844 | Blockers page mounted |
| 06_upcoming.png | `/employee-app-v2/upcoming` | 390×844 | Upcoming/waiting shell |
| 07_personal.png | `/employee-app-v2/personal` | 390×844 | Personal hub links |
| 08_empty_or_error.png | `/employee-app-v2/documents` | 390×844 | Documents empty state |
| 11_tasks_refresh_state.png | `/employee-app-v2/tasks` | 390×844 | Confirms empty after refresh |

## Owner visual verification

| Field | Value |
|-------|-------|
| URL | `http://127.0.0.1:3000/employee-app-v2/tasks` |
| Employee | Dev bypass → Sandu (`employee_id=4`) after gate link |
| Fixture order | `23099` (13 operational tasks assigned in DB) |
| Expected label | e.g. `Vector Prep` with component badge |
| Expected component | `root_product` (from frozen identity) |
| Expected Start | `is_startable=true` when readiness allows |
| Actual | **Empty list** — mobile loader gap |
| Backend source | `GET /api/v1/employee-mobile/tasks` → `[]` |
| Defect | `CURRENT_MOBILE_CONTRACT_DEFECT` (V2 envelope not consumed) |

## Implementation authorization

**`READY_WITH_BACKEND_ADAPTER_PREREQUISITE`**

**First allowed task:** `MOBILE-T01_CANONICAL_MOBILE_TASK_READ_MODEL`

## Mobile implementation spine (serialized)

1. **MOBILE-T01** — Adopt `parse_tasks_json_raw` + reduced projection from canonical truth (frozen identity, component label, readiness, no cost fields).
2. **MOBILE-T02** — Assigned + available task list/detail wiring on new read model.
3. **MOBILE-T03** — Blocker/readiness visibility (employee-safe payloads).
4. **MOBILE-T04** — Start / start-from-available (existing endpoints; verify on V2 IDs).
5. **MOBILE-T05** — In-progress session display; pause/complete only where canonical.
6. **MOBILE-T06** — Assignment/self-claim policy confirmation + audit.
7. **MOBILE-INT-02** — Final mobile integration gate.

Manager resolution stays **desktop-only**.

## Temporary debt (mobile relevance)

| Item | Classification |
|------|----------------|
| V2 plan loader gap | **BLOCKS_MOBILE** |
| OperatorView manual refresh | OUTSIDE_MOBILE_FINAL_PHASE |
| ShopFloor projection | MOBILE_FUTURE_ENHANCEMENT |
| Logo full identity | MOBILE_FUTURE_ENHANCEMENT (nonblocking) |
| Offline / push | NOT_IMPLEMENTED |
| Ghost port 8000 | OUTSIDE_MOBILE_FINAL_PHASE |
| Sandu dev fixture intake dependency | LEGACY_ISOLATED |

## Commands

```powershell
cd backend
$env:APP_ENV='development'
$env:ENVIRONMENT='development'
$env:DATABASE_URL='sqlite+aiosqlite:///./dev.db'
$env:JWT_SECRET_KEY='local-dev-secret-not-for-production'
.\.venv\Scripts\python.exe scripts\mobile_int_01_runtime_gate_proof.py --setup
cd ..\frontend
node ..\backend\scripts\mobile_int_01_capture_screenshots.cjs
.\.venv\Scripts\python.exe -m pytest tests/test_employee_mobile_tasks.py tests/test_employee_mobile_order_blueprint.py tests/test_execution_owner_decision_production_release_guard.py::test_employee_mobile_start_route_guarded -q
```

## Honest opinion

Employee Mobile v2 UI is structurally ready (routes, action bars, backend-bound `is_startable`), but the **backend list loader is still legacy-shaped** while the frozen spine persists V2 plan envelopes. Implementation must not proceed on UI polish alone — **MOBILE-T01** is a hard prerequisite. Production-release and readiness gates on **mutations** are already correct; the gap is **read-model parity** with `operator_task_truth/v1`.
