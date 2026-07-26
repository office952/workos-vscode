# APP-AUTH-02B — Available projection runtime closure

**Task:** APP-AUTH-02B — `AVAILABLE_PROJECTION_RUNTIME_CLOSURE_V1`  
**Date:** 2026-07-15  
**Starting HEAD:** `b38f6a6` (OWNER-DECISION-02)  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Sandu / reconciliation:** **NO changes**

## Verdict

**`APP_AUTH_02B_AVAILABLE_PROJECTION_PASS_COMMITTED`**

Root cause proven: **FIXTURE_STATE_BLEED** (order `24009` leaked from `test_corrupt_v2_snapshot_fail_closed`) plus **AVAILABLE_PROJECTION_GLOBAL_FAILURE_DEFECT** (one corrupt order aborted entire available pool). Both fixed: operator-truth teardown + **ORDER_LOCAL_FAIL_CLOSED** for available readiness attachment.

---

## Reproduction matrix (pre-fix)

| Context | Result | Notes |
|---------|--------|-------|
| `test_available_projection_filters_canonically` alone | **PASS** | No leaked corrupt order |
| Full `test_employee_mobile_task_truth.py` module | **PASS** | |
| After `test_corrupt_v2_snapshot_fail_closed` | **FAIL** | `HTTPException 422` `ORDER_SNAPSHOT_V2_CORRUPT` `order_id=24009` |
| Before corrupt test | **PASS** | |
| Combined APP-AUTH-02 suite (76 tests) | **FAIL** | Same 422 on 24009 |
| Reversed suite order | **FAIL** (pre-fix) / **PASS** (post-fix) | |
| Repeated combined suite ×3 | **PASS** (post-fix) | |

**Failure chain:** `list_available_tasks` → `_attach_readiness_to_tasks(..., for_available_pool=True)` → `load_order_quote_input` → `_parse_frozen_snapshot` on leaked order `24009` with `snapshot_v2_json="{not-valid-json"`.

**Corruption source:** fixture setup in `test_operator_task_truth.py` (not application mutation). Execution plan on 24009 is valid; snapshot JSON is invalid.

---

## Root cause

| Classification | Value |
|----------------|-------|
| **Primary** | `FIXTURE_STATE_BLEED` |
| **Secondary** | `AVAILABLE_PROJECTION_GLOBAL_FAILURE_DEFECT` |

`test_corrupt_v2_snapshot_fail_closed` committed order `24009` without teardown. Shared pytest SQLite DB retained the row; `list_available_tasks` loads all execution plans globally, so an eligible print task on 24009 entered the available pool and readiness attachment failed globally.

---

## Chosen corruption contract

**`ORDER_LOCAL_FAIL_CLOSED` (A)**

- Available pool: exclude tasks on orders blocked by `ORDER_SNAPSHOT_V2_CORRUPT` / `ORDER_SNAPSHOT_V2_MISSING`; valid orders remain visible.
- Assigned (`list_my_tasks`): still **fail closed per order** (no silent drop of owned work).
- Operator truth on corrupt order: unchanged **422** fail-closed.
- Diagnostics: structured **backend log** (`warning`) with `order_id`, error code, `excluded_task_count`, `projection_scope=available`. Not exposed in Employee Mobile response body.

---

## Application changes

| File | Change |
|------|--------|
| `backend/services/employee_mobile_tasks_service.py` | Order-local exclusion in `_attach_readiness_to_tasks` when `for_available_pool=True` |
| `backend/tests/test_operator_task_truth.py` | `_delete_truth_order_fixture` + teardown on corrupt snapshot test |
| `backend/tests/test_employee_mobile_task_truth.py` | Isolation tests + HTTP route test |
| `backend/scripts/app_auth_02b_available_projection_runtime_proof.py` | Live :8001 probe (see runtime note) |

**Not changed:** Sandu competences/authorizations/overrides, distribution engine, reconciliation, snapshot/plan identity writers.

---

## Test evidence (post-fix)

| Suite | Passed | Failed |
|-------|--------|--------|
| Combined APP-AUTH-02 (76) | 76 | 0 |
| Employee mobile truth + tasks + concurrency (46) | 46 | 0 |
| Snapshot adapter + operator truth (26) | 26 | 0 |
| Focused APP-AUTH-02B tests (5) | 5 | 0 |

**Original test classification:** `FIXTURE_AND_RUNTIME_CONTRACT_CORRECTED`

---

## Live HTTP runtime (:8001)

| Check | Result |
|-------|--------|
| Server reachable | YES (`/docs` 200) |
| Script probe with JWT | **BLOCKED** — running server missing `JWT_ALGORITHM` env |
| In-process HTTP route (`GET /api/v1/employee-mobile/tasks/available`) | **PASS** |
| Service-level `list_available_tasks` | **PASS** |

Runtime fixture on dev.db: isolated proof orders created and removed by script/tests only; no Sandu mutation.

---

## Task gate

| Gate | Status |
|------|--------|
| Root cause proven | YES |
| Combined suite green | YES |
| Fixture cleanup on 24009 | YES |
| Contract explicit | ORDER_LOCAL_FAIL_CLOSED |
| Employee isolation unchanged | YES |
| Sandu unchanged | YES |
| PROD-ARCH-01 / MOBILE-INT-02 | Not opened |

**Next task:** `OWNER-DECISION-03-OPERATIONAL-AUTHORITY-CONFIRMATION`

---

## Delivery footer

```
Task: APP-AUTH-02B — AVAILABLE_PROJECTION_RUNTIME_CLOSURE_V1
Starting HEAD: b38f6a6
Original test: test_available_projection_filters_canonically
Root cause: FIXTURE_STATE_BLEED + AVAILABLE_PROJECTION_GLOBAL_FAILURE_DEFECT
Test alone: PASS
Test module: PASS
Combined suite: PASS
Randomized order: NOT_RUN (pytest-randomly absent; reversed order PASS)
Repeated suite: PASS (3×)
Leaked fixture: NO (post-fix teardown)
Corrupt order: 24009
Corruption contract: ORDER_LOCAL_FAIL_CLOSED
Valid orders preserved: YES
Corrupt order excluded: YES
Structured diagnostic: YES (logs)
Employee isolation: PASS
Assignment policy changed: NO
Competence policy changed: NO
Authorization policy changed: NO
Readiness policy changed: NO
Application behavior changed: YES
Focused backend tests: PASS
Live HTTP runtime: PARTIAL (route PASS; :8001 JWT env drift)
Sandu changed: NO
Original test classification: FIXTURE_AND_RUNTIME_CONTRACT_CORRECTED
Next task: OWNER-DECISION-03-OPERATIONAL-AUTHORITY-CONFIRMATION
Code changed: YES
Push: NO
PR: NO
Verdict: APP_AUTH_02B_AVAILABLE_PROJECTION_PASS_COMMITTED
```
