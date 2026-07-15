# APP-AUTH-02C — External HTTP runtime and JWT environment closure

**Task:** APP-AUTH-02C — `AVAILABLE_PROJECTION_EXTERNAL_HTTP_RUNTIME_CLOSURE_V1`  
**Date:** 2026-07-15  
**Starting HEAD:** `59449bc`  
**Accepted APP-AUTH-02B:** app `328416b` · docs `59449bc`  
**Branch:** `feature/product-system-active-path-isolation-v1`

## Verdict

**`APP_AUTH_02C_EXTERNAL_HTTP_PASS_CLOSE_APP_AUTH_02B`**

External authenticated HTTP on trusted `:8001` now proves ORDER_LOCAL_FAIL_CLOSED: valid available order visible, corrupt neighbor excluded, warning logged, assigned corrupt order fails closed (422). APP-AUTH-02B is **COMPLETE**.

---

## Process on port 8001

| Field | Before (stale) | After (canonical) |
|-------|----------------|-------------------|
| PID | 23392 | 25672 (worker) / 7676 (.venv parent) |
| Executable | Global `Python312\python.exe` | `C:\w\psiso\backend\.venv\Scripts\python.exe` |
| Command | `uvicorn main:app --host 127.0.0.1 --port 8001` (no reload env) | `uvicorn main:app --host 127.0.0.1 --port 8001 --reload` |
| Startup | Manual | `scripts/dev-backend.ps1` with `BACKEND_PORT=8001` |
| Classification | **MANUALLY_STARTED_INCOMPLETE_ENV** | **CANONICAL_BACKEND_PROCESS** |

Port **8000** retains orphan listener PID **4392** — **non-authoritative ghost** (unchanged; not used for this gate).

---

## JWT / auth environment trace

| Variable | Stale :8001 | Canonical script | Probe |
|----------|-------------|------------------|-------|
| `JWT_SECRET_KEY` | present | injected | present |
| `JWT_ALGORITHM` | **missing** | **HS256** | HS256 |
| `JWT_EXPIRE_MINUTES` | **missing** | **60** | 60 |
| Dev bypass | N/A for isolated employee | available | not used |

**Root cause classification:** `BACKEND_ENVIRONMENT_MISSING` (canonical helpers omitted JWT algorithm/expiry; stale manual process inherited gap).

**Environment outcome:** `ENVIRONMENT_ONLY_CORRECTED` + `STALE_RUNTIME_PROCESS_REMOVED`

**Authentication method:** `signed_jwt_bearer` (employee_mobile role, unique synthetic `user_id` linked to fixture employee).

---

## External HTTP proof

| Check | Result |
|-------|--------|
| `GET /api/v1/employee-mobile/tasks/available` | **200** |
| Valid order `94084` / task `node:root_product:...:vector_prep` | **visible** |
| Corrupt order `95084` | **absent** |
| Global 422 / 500 | **none** |
| Warning log | **PASS** — `ORDER_SNAPSHOT_V2_CORRUPT`, `order_id=95084`, `excluded_task_count=1` |
| Assigned corrupt `96084` (`list_my_tasks`) | **422** fail-closed |

Evidence: `docs/qa/product-system-active-path-isolation-v1/app_auth_02c_external_http_evidence.json`  
Probe: `backend/scripts/app_auth_02c_external_http_runtime_closure_proof.py`

---

## Application / config changes

| File | Change |
|------|--------|
| `scripts/_workos-python.ps1` | `Set-WorkOsJwtEnv` helper |
| `scripts/dev-backend.ps1` | JWT env + `BACKEND_PORT` support |
| `scripts/start-dev.ps1` | JWT env in stack + backend job |
| `scripts/test-backend.ps1` | JWT env for pytest |
| `backend/.env.example` | Document `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES` |
| `backend/scripts/app_auth_02c_external_http_runtime_closure_proof.py` | External gate probe |

**Not changed:** projection contract, Sandu, competences, assignments, snapshots.

---

## Regression tests

| Suite | Passed | Failed |
|-------|--------|--------|
| APP-AUTH-02 combined (incl. mobile truth) | 91 | 0 |
| `test_build26_2_oidc_google_auth.py` static `.env.example` | 0 | 3 (pre-existing minimal `.env.example` debt) |

---

## APP-AUTH-02B final status

**COMPLETE** — fixture isolation + ORDER_LOCAL_FAIL_CLOSED + external HTTP gate closed.

**Next task:** `OWNER-DECISION-03-OPERATIONAL-AUTHORITY-CONFIRMATION`

---

## Delivery footer

```
Task: APP-AUTH-02C — AVAILABLE_PROJECTION_EXTERNAL_HTTP_RUNTIME_CLOSURE_V1
Starting HEAD: 59449bc
Backend port: 8001
Backend process: CANONICAL_BACKEND_PROCESS
Canonical startup: PASS
JWT environment: BACKEND_ENVIRONMENT_MISSING (corrected)
Authentication method: signed_jwt_bearer
External HTTP: PASS
HTTP status: 200
Valid order preserved: YES
Corrupt order excluded: YES
Warning log: PASS
Assigned strict behavior: PASS
Fixture cleanup: PASS
Environment outcome: ENVIRONMENT_ONLY_CORRECTED
Focused backend tests: PASS (91/91 gate suite)
Sandu changed: NO
APP-AUTH-02B: COMPLETE
Next task: OWNER-DECISION-03-OPERATIONAL-AUTHORITY-CONFIRMATION
Code changed: YES
Push: NO
PR: NO
Verdict: APP_AUTH_02C_EXTERNAL_HTTP_PASS_CLOSE_APP_AUTH_02B
```
