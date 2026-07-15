# RUNTIME-RECOVERY-02 — Full application connectivity and route health audit

**Task:** `RUNTIME-RECOVERY-02` — `FULL_APPLICATION_RUNTIME_CONNECTIVITY_AND_ROUTE_HEALTH_AUDIT_V1`  
**Date:** 2026-07-15  
**Worktree:** `C:\w\psiso`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Starting HEAD:** `0373215`  
**Verdict:** `RUNTIME_RECOVERY_02_PASS_INTAKE_RESTORED_OTHER_GAPS_FOUND`

## Symptom (owner-reported)

- URL: `http://127.0.0.1:3000/intake`
- UI: `Source Error` — *Datele operaționale nu au putut fi încărcate din backend: Network Error*
- Intake counters all `0`; mutate actions disabled
- Global banner simultaneously: `LIVE / DB — Sursa de date: backend live`

## Scope boundary (respected)

No business logic, DB schema, migrations, Intake V6, Product System, parity, authority, refactor, or UI changes. Runtime recovery and evidence only.

---

## 1. Process inventory (pre-stop)

| Port | State | PID / notes | Classification |
|------|-------|-------------|----------------|
| 3000 | DOWN or stale | No trusted canonical listener at audit open | STALE / NOT_PROVEN |
| 8001 | UP | Multiple uvicorn PIDs (system Python + worktree `.venv`); GHOST netstat orphans | STALE + GHOST |
| 8000 | DOWN | Vite proxy default target — **no listener** | STALE (mis-point) |
| 8011 | DOWN | Parity pilot port inactive | NOT_PROVEN |
| 8021 | DOWN | Restore test backend from BACKUP-BASELINE-01B teardown | RESTORE_PROCESS (absent) |

Evidence: `docs/qa/product-system-active-path-isolation-v1/runtime_recovery_02/process_inventory.json`

---

## 2. Backend health (`:8001`)

Direct probes (all PASS on canonical backend after cleanup):

| Endpoint | Status | Auth |
|----------|--------|------|
| `/health` | 200 | no |
| `/api/v1/system/health` | 200 | no |
| `/docs` | 200 | no |
| `/api/v1/entities/intake_requests?limit=5` | 200 | yes (dev bypass) |
| `/api/v1/operational-registry/employees` | 200 | yes |
| `/api/v1/entities/orders?limit=3` | 200 | yes |

Evidence: `backend_endpoint_matrix.json`

---

## 3. Frontend configuration

| Source | Variable | Active value | Expected |
|--------|----------|--------------|----------|
| `vite.config.ts` | `BACKEND_PORT` | **must be `8001` at process start** | `8001` |
| `vite.config.ts` | proxy `/api` | `http://localhost:8001` when env set | `8001` |
| `vite.config.ts` | proxy default | `http://localhost:8000` if env unset | **root cause** |
| `config.ts` | `DEV_LOCAL_CONFIG` | `http://127.0.0.1:8001` | `8001` |
| `api.ts` | web-sdk `createClient` | same-origin `/api` (proxy path) | proxy → `8001` |
| `dev.ps1` | `VITE_API_BASE_URL` | `http://127.0.0.1:8000` if script used | conflicts with trusted `8001` |
| restore 01B leak | `BACKEND_PORT=8021` | not active on source `:3000` after restart | must not leak |

Evidence: `frontend_runtime_config.json`

---

## 4. Intake request trace

**Failing chain (pre-recovery):**

```
WorkIntake.tsx → useBackendData → dataStore.loadIntakes()
  → intakesApi.list() → @metagptx/web-sdk client.entities.intake_requests.query()
  → GET http://127.0.0.1:3000/api/v1/entities/intake_requests?...
  → Vite proxy → http://localhost:8000 (default) → connection refused → axios "Network Error"
```

**Classification (pre-recovery):** `WRONG_PROXY_TARGET` (+ stale duplicate backend processes on `8001`)

**Post-recovery:** same URL via proxy returns **200** with 4 intake rows.

Evidence: `intake_request_trace.json`

---

## 5. Banner truth check

`EnvironmentBanner.tsx` sets `LIVE / DB` when `authState === "authenticated"`. It does **not** probe operational API health.

**Classification:** `MISLEADING` — banner can remain green while `/intake` shows Network Error.

Evidence: `banner_truth_check.json`

---

## 6. Route health sweep (post-recovery, read-only)

| Route | Shell | API probe | Classification |
|-------|-------|-----------|----------------|
| `/` | 200 | — | HEALTHY |
| `/intake` | 200 | `intake_requests` 200 | HEALTHY |
| `/quotes` | 200 | `quotes` 200 | HEALTHY |
| `/orders` | 200 | `orders` 200 | HEALTHY |
| `/execution` | 200 | `execution/dashboard` 200 | HEALTHY |
| `/product-system` | 200 | `entities/product-families` 200 | HEALTHY |
| `/employees` | 200 | `operational-registry/employees` 200 | HEALTHY |
| `/utilaje` | 200 | `machines` 200 | HEALTHY |
| `/modules` | 200 | shell only | HEALTHY |
| `/governance` | 200 | shell only | HEALTHY |

**10 checked · 10 healthy · 0 failed**

Evidence: `route_health_matrix.json`

---

## 7. Database (read-only)

- Path: `C:\w\psiso\backend\dev.db`
- Integrity: `ok`
- Counts: intake_requests **4**, orders **6**, employees **8**
- Backend `DATABASE_URL` points to source DB (not restore tree `C:\w\wrt\b01`)

**Classification:** `CORRECT`

Evidence: `database_runtime_validation.json`

---

## 8. Authentication

- Dev auth enabled (`VITE_ENABLE_DEV_AUTH=true`)
- Dev bypass bearer: intake list **200**
- Unauthenticated intake probe: **401** (expected)
- Browser session may need re-login after restart; not an architecture defect

**Classification:** `PASS`

Evidence: `auth_runtime_validation.json`

---

## 9. Runtime restore actions

1. Stopped stale/ghost listeners on `8001`; cleared restore port `8021` if present  
2. Started canonical backend: `C:\w\psiso\backend\.venv` uvicorn `--port 8001` (PID 29372)  
3. Started canonical frontend: vite `--port 3000` with **`BACKEND_PORT=8001`** (PID 36492)  
4. Cleared parity env flags (ALL_FALSE)  
5. Verified `/intake` proxy chain and 9 additional routes  
6. **Business DB writes: 0**

Evidence: `restart_actions.json`

---

## 10. Parity flags

All parity observe flags unset on restarted backend process → **ALL_FALSE**.

---

## 11. Tests

Not run — intake failure was runtime connectivity, not application endpoint defect after recovery. No code repair GO.

---

## 12. Visual verification (owner)

**URL:** `http://127.0.0.1:3000/intake`

**Expected after dev login:**

- No `Source Error` / `Network Error`
- Counters reflect backend (4 intakes in DB)
- `Cerere Nouă` enabled when `canMutateIntake`
- Network tab: `GET /api/v1/entities/intake_requests` → **200** via `:3000` proxy to `:8001`

**Automated:** proxy/API **200** — browser screenshot **PARTIAL** (owner session).

Evidence: `visual_verification.json`

---

## 13. Root cause (proven)

**Primary:** Vite dev proxy defaulted to port **8000** while trusted backend listens on **8001**. Web-sdk CRUD uses same-origin `/api` (proxy), not `config.ts` direct `:8001`. Nothing on `:8000` → `Network Error` on `/intake`.

**Contributing:** Stale duplicate uvicorn processes on `:8001`; possible `BACKEND_PORT=8021` env leak from restore test if frontend restarted without clearing env.

---

## 14. Remaining gaps (non-blocking for intake)

1. **Banner truth** — `MISLEADING` (auth-only LIVE/DB)  
2. **Launcher defaults** — `dev.ps1` / `start-dev.ps1` target `:8000`; trusted stack uses `:8001`  
3. **Dual API paths** — web-sdk via proxy vs `getAPIBaseURL()` direct `:8001` (split-brain risk)

---

## 15. Repository safety

- Source `C:\w\psiso` — no tracked code changes  
- Source `frontend/node_modules` — untouched  
- Restore tree `C:\w\wrt\b01` — not used for canonical runtime  

---

## 16. Next task

**`RETURN_TO_OWNER_DECISION_04_CONFIRMATION`** — runtime connectivity restored; do not auto-continue `APP-AUTH-06C`.

Optional follow-up (separate GO): `RUNTIME-RECOVERY-02B-CODE-REPAIR-PLAN` for launcher/proxy default alignment and banner health probe.

---

## Delivery footer

```
Task: RUNTIME-RECOVERY-02
Starting HEAD: 0373215
Frontend 3000: UP
Backend 8001: UP
Frontend API target: http://127.0.0.1:3000/api → localhost:8001
Intake request: GET /api/v1/entities/intake_requests → 200 (post-recovery)
Root cause: WRONG_PROXY_TARGET (Vite BACKEND_PORT default 8000)
Intake restored: YES
Routes checked: 10
Routes healthy: 10
Routes failed: 0
Banner truth: MISLEADING
Source DB: CORRECT
Auth: PASS
Parity flags: ALL_FALSE
Business DB writes: 0
Code changed: NO
Runtime restarted: YES
Visual verification: PARTIAL
Next task: RETURN_TO_OWNER_DECISION_04_CONFIRMATION
Commit: YES (pending)
Push: NO
PR: NO
Verdict: RUNTIME_RECOVERY_02_PASS_INTAKE_RESTORED_OTHER_GAPS_FOUND
```
