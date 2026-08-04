# Finalization Wave 8 — Auth Fail-Closed + Assignment Observability + Reassignment Policy

| Field | Value |
| ----- | ----- |
| Date | 2026-08-04 |
| Task | `FINALIZATION_WAVE_8_AUTH_FAIL_CLOSED_AND_ASSIGNMENT_OBSERVABILITY_POLICY` |
| Status | **`FINALIZATION_WAVE_8 = PASS`** |
| Starting HEAD | `1e3f8be4` |
| Implementation commit | (see tip / content commit) |
| Repo / worktree | `C:\w\psiso` (canonical also `C:\Users\offic\workos_app_vs`) |
| Branch | `feat/f7i-owner-rate-activation` |
| Schema / migration | **NONE** |
| QA assignment mutations | **0** |
| Reassignment / unassignment | **NOT IMPLEMENTED** |

## Verdict

```text
FINALIZATION_WAVE_8 = PASS
PRODUCTION_AUTH_FAIL_CLOSED = VERIFIED
DEBUG_PRODUCTION_BYPASS = IMPOSSIBLE
WAVE7_FAILED_TEST_ROOT_CAUSE = VERIFIED
ASSIGNMENT_OBSERVABILITY = VERIFIED_WITHIN_CURRENT_MODEL
ASSIGNMENT_AUDIT_PRIVACY = VERIFIED
REASSIGNMENT_POLICY_AUDIT = COMPLETE
REASSIGNMENT_IMPLEMENTED = NO
UNASSIGNMENT_IMPLEMENTED = NO
ADDITIONAL_QA_MUTATIONS = 0
WAVE_9 = NOT_AUTHORIZED
```

Wave 7 remains PASS; single QA assignment retained.

## Wave 7 failed test — exact root cause

| Item | Value |
| ---- | ----- |
| File | `backend/tests/test_auth_dev_impersonation.py` |
| Name | `test_production_blocks_dev_bypass_without_credentials` |
| Expected | HTTP **401** on `GET /api/v1/auth/me` with no credentials under `APP_ENV=production` |
| Actual (Wave 7) | `RuntimeError: Startup blocked by environment safety checks for production` |
| Blocking check | `DEBUG_MODE_OFF` — DEBUG mode enabled in production |
| Environment | agent shell had inherited `DEBUG=true` from detached stack helpers; test set only `APP_ENV=production` |
| Auth headers | none |
| Database | isolated TestClient / `db_fixture` (not QA `dev.db`) |
| Classification | **`TEST_FIXTURE_DRIFT`** + **`ENVIRONMENT_DEFECT`** (test isolation) — **not** `REAL_SECURITY_DEFECT` |
| Security reality | production + `DEBUG=true` correctly **blocks startup**; missing-auth bypass remains **impossible** (`dev_auth_allowed()==False`). Auth did **not** fail open. |

Reproduction:

- `DEBUG=true` + test → FAIL (startup blocked) — Wave 7 condition  
- `DEBUG=false` or unset + test → PASS (401)  
- After Wave 8 test fix: `DEBUG=true` inherited still PASS (test forces `DEBUG=false`)

## Production authentication matrix

| Scenario | Result |
| -------- | ------ |
| production missing Authorization | 401 |
| production invalid JWT | 401 |
| production expired JWT | 401 |
| production wrong signing key | 401 |
| production malformed Authorization | 401 |
| production + DEBUG=true | startup BLOCKED; bypass false |
| unknown APP_ENV typo (`prodution`) | bypass denied (Wave 8 harden) |
| development missing auth | synthetic admin (documented) |
| viewer without `execution.task_assign` | 403 |

Environment answers:

1. Missing `APP_ENV` → default `development` (local DX); bypass allowed.  
2. `DEBUG=true` + production → startup failure.  
3. Typo APP_ENV → non-auth helpers may still say development; **bypass denied**.  
4. Missing auth outside local/development/test → denied.  
5. No fail-open auth bypass in production.  
6. Startup BLOCKED on insecure production/debug combo.  
7. Tests can contaminate via inherited env — Wave 8 tests now set explicit `APP_ENV`/`DEBUG`/`JWT_*`.

## Changes (justified)

| File | Why |
| ---- | --- |
| `backend/core/environment.py` | Fail-closed `dev_auth_allowed` for unknown APP_ENV |
| `backend/dependencies/permissions.py` | Log `user_id` not email on permission deny |
| `backend/services/controlled_employee_assignment_service.py` | Safe structured assignment outcome log |
| `backend/tests/test_auth_dev_impersonation.py` | Isolate DEBUG; add production DEBUG + typo tests |
| `backend/tests/test_finalization_wave8_auth_fail_closed_and_observability.py` | Production auth matrix + privacy contracts |
| `docs/architecture/ASSIGNMENT_OBSERVABILITY_AND_REASSIGNMENT_POLICY.md` | Canonical policy/observability |
| this worklog + route / DEC pointer updates | Closure evidence |

No assignment persistence semantics changed. No schema.

## Observability

See architecture doc. Wave 7 embedded audit RO verified:

```text
task = …:led_install_letters
employee_id = 7
source = canonical_controlled_assign_v1
actor = dev-admin-user-00000000
assignment_updated_at = 2026-08-04T16:16:57.406324+00:00
```

Gaps retained: correlation IDs, append-only event table, unified denial event stream → require Owner GO if schema needed.

## Reassignment policy

Inventory + Option A (strict pre-start) vs Option B (operational transfer) documented.  
Owner decisions DEC-REASSIGN-01…08 required before any implementation.

## Tests

| Command | Result | DB | Class |
| ------- | ------ | -- | ----- |
| `pytest … test_auth_dev_impersonation.py + wave8 suite + wave6 permission deny` with `DEBUG=true` inherited | **22 passed** | isolated | NEW_REGRESSION none |
| `pytest wave6 hardening + permissions + environment_readiness` | **51 passed**, **2 failed** | isolated | fail = **PRE_EXISTING** `release.json` environment=`staging` vs tests expecting `live` |
| Live RO readiness/plan against `:8000` | evidence only | QA `dev.db` RO | no mutate |

Do **not** claim full backend green.

## Zero mutation

Before = after:

| Field | Value |
| ----- | ----- |
| tasks_json SHA | `00ee947c0b5e2da587c0d0563f1051ca89379d66cfec434e75dbe3883ccfc1f2` |
| updated_at | `2026-08-04 19:16:57.407320` |
| assigned LED emp | 7 |
| assigned count | 1 / 12 unassigned |
| DB SHA | `b67c76f0fe87cb64e2950d680e38da2fe32cb9229bf4015904ddd24cc32f8b14` |
| sessions / machines | 0 |
| scheduling | HOLD |

```text
QA_ASSIGNMENT_PATCH_REQUESTS = 0
QA_REASSIGNMENT_REQUESTS = 0
QA_UNASSIGNMENT_REQUESTS = 0
QA_SUCCESSFUL_MUTATIONS = 0
```

## Protected baselines / F7I

| Order | Reality |
| ----- | ------- |
| 880811 | present plan 22 — unchanged |
| 973019 | present plan 21 — unchanged |
| 88002 | absent — unchanged |

F7I 15 / 1.5 / 35 / 20 EUR untouched.

## Dead pieces

```text
Dead pieces discovered:
  development missing-auth bypass (dev-only)
  DEBUG startup branching (strict envs)
  public controlled=false / allow_reassign (blocked)
  direct assign service (blocked)
  Mobile claim / start_from_available (frozen)
  clear_plan_task_assignment helper (legacy Mobile rollback)
  Mobile Claim UI surfaces
Dead pieces touched: NONE removed
Dead pieces removed: NONE
Why: inventory/harden only; no general cleanup GO
Future impact: reassignment GO must not revive bypass flags
```

## Remaining risks

- No request correlation ID end-to-end.  
- Embedded audit ≠ full history for future reassignment.  
- `release.json` = staging causes two startup-safety unit tests to expect `live` (pre-existing drift).  
- Production rollout still not authorized.

## Scores

```text
Direction alignment score: 94/100
Operational completion score: 72/100
```

Operational score deliberately not inflated: reassignment, sessions, scheduling remain unimplemented.

## Next step

```text
OWNER DECISION ON CONTROLLED PRE-START REASSIGNMENT POLICY
```

Await Owner review. Do not implement reassignment automatically.
