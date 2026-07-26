# MOBILE-T02B — Available Task Fixture Isolation and Regression Closure

**Task:** MOBILE-T02B — `AVAILABLE_TASK_FIXTURE_ISOLATION_AND_REGRESSION_CLOSURE_V1`  
**Date:** 2026-07-15  
**Starting HEAD:** `8b6ca33`  
**Verdict:** `MOBILE_T02B_TEST_BASELINE_PASS_CLOSE_MOBILE_T02`

## Failure

`test_available_tasks_visible_for_eligible_unassigned` failed when run after `test_employee_mobile_task_truth.py` in the same pytest session:

- Expected: global `len(rows) == 1`
- Actual: 2 rows — `T-AVAIL` on order `901` plus `node:root_product:...:vector_prep` on order `~23354`

## Classification

**FIXTURE_STATE_BLEED** (primary) + **STALE_LEGACY_EXPECTATION** (assertion assumed exclusive DB)

## Root cause

`db_fixture` is **session-scoped** (`conftest.py`). MOBILE-T01 truth tests commit unassigned print-eligible V2 tasks that persist for the session. Available projection correctly returns all eligible unassigned tasks workspace-wide — the legacy test asserted a global count of 1 instead of scoping to its seeded order `901`.

## Fix

1. Scope `test_available_tasks_visible_for_eligible_unassigned` assertions to `order_id == 901` (matches truth-test pattern).
2. Add `_delete_order_execution_fixture()` helper and teardown in truth tests that seed committed available-task fixtures.

## Regression

| Suite | Result |
|-------|--------|
| `test_employee_mobile_task_truth.py` + `test_employee_mobile_tasks.py` | 35 passed × 3 runs |
| Canonical mobile backend (54 tests) | PASS |
| MOBILE-T02 frontend focused | 18 passed |
| Runtime gate (:8001) | PASS |

## MOBILE-T02 status

**COMPLETE** — gate unblocked. Next: **MOBILE-T03-BLOCKER-READINESS-VISIBILITY**
