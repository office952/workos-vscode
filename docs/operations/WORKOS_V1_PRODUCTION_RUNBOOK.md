# WorkOS V1 — Production Runbook (single-tenant local)

**Scope:** V1 single-workstation / internal laboratory operation.  
**Not:** cloud HA, Kubernetes, Postgres rollout, public internet deploy.

---

## 1. Requirements

| Component | Notes |
|-----------|--------|
| OS | Windows 10/11 (canonical local) |
| Python | 3.12+ with `backend/.venv` |
| Node | via `npx pnpm@8.10.0` (global pnpm not required) |
| DB | SQLite file `backend/dev.db` (DEC-DATABASE-01) |

---

## 2. Runtime topology

| Service | URL / path |
|---------|------------|
| Backend | `http://127.0.0.1:8000` |
| Frontend | `http://127.0.0.1:3000` |
| Health | `GET /health` |
| System health | `GET /api/v1/system/health` |
| DB health | `GET /database/health` |
| Logs | `.workos-dev-logs/` |

---

## 3. Canonical start / stop

**ONE_CANONICAL_START_COMMAND (agent / operator helper):**

```powershell
cd C:\w\psiso
.\scripts\dev-detached.ps1
```

**Stop (only after Owner stop GO):**

```powershell
.\scripts\stop-dev.ps1
```

Owner uses browser only. Agents start/stop when asked in chat.

Do **not** use foreground `.\scripts\dev.ps1` in agent shells (teardown on shell end).

---

## 4. Required environment (names only)

| Key | Class |
|-----|--------|
| `DATABASE_URL` | REQUIRED |
| `APP_ENV` / `ENVIRONMENT` | REQUIRED |
| `JWT_SECRET_KEY` | REQUIRED · SECRET |
| `ALLOWED_ORIGINS` | OPTIONAL |
| `VITE_ENABLE_DEV_AUTH` | DEV_ONLY |
| `VITE_DEV_GUARD_BYPASS` | DEV_ONLY · PRODUCTION_BLOCKER if left on for real deploy |

Helpers inject local placeholders. Plain uvicorn does **not** auto-load `backend/.env`.

Production-like: set a strong `JWT_SECRET_KEY`; disable Vite/dev auth bypass.

---

## 5. Database

```text
DB_ENGINE = SQLite (aiosqlite)
ALEMBIC_HEAD = s67_machine_run_execution_status
```

Migrations (disposable / update path):

```powershell
cd C:\w\psiso\backend
$env:APP_ENV='development'
$env:DATABASE_URL='sqlite+aiosqlite:///C:/w/psiso/backend/dev.db'
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Startup scripts do **not** auto-migrate or seed.

---

## 6. Backup / restore (SQLite)

1. Stop the stack (`stop-dev.ps1`).  
2. Copy `backend/dev.db` to a dated backup path.  
3. Verify copy opens (`sqlite3` / Python `sqlite3`).  
4. To restore: stop stack, replace `dev.db` with backup, start stack, hit `/health` + `/database/health`.

No backup service. File copy while writers stopped is the V1 procedure.

---

## 7. Update procedure

1. Stop app  
2. Backup DB  
3. Update code  
4. `alembic upgrade head`  
5. `cd frontend && pnpm run build` (release artifact)  
6. Start with `dev-detached.ps1` (or production process manager of choice)  
7. Smoke: `/health`, `/modules`, `/quotes`, `/execution`, Profitability on a known order  

---

## 8. Rollback

- Restore previous app revision **and** DB backup if migrations are not downgraded.  
- Alembic downgrade is **not** claimed for V1.

---

## 9. Seeds

All `backend/scripts/seed_*.py` are **DEV_ONLY**. Never run casually against a DB you care about. Some reset fixture orders.

---

## 10. Known V1 limitations

- Machine monetary cost = `N_A_FOR_V1`  
- Other direct = `N_A_FOR_V1`  
- Capacity Stage 1 = `IMPLEMENTED_INACTIVE`  
- Phase E / PAUSE/RESUME = deferred  
- ACM/Logo sold-root expansion = LATER  
- Postgres / multi-node = LATER  
- Cloud production rollout = NOT_AUTHORIZED under DEC-DATABASE-01  
- Formal V1 finalize status: technical exit PASS; Owner product-set ack may still be pending — see `docs/architecture/realignment/WORKOS_V1_EXIT_RECORD.md`

---

## 11. V1 smoke sequence

```powershell
# 1) startup contract
cd C:\w\psiso
npm run test:startup-contract

# 2) frontend production build
cd frontend
npx --yes pnpm@8.10.0 run build

# 3) backend CI + profitability readiness subset
cd ..\backend
$env:APP_ENV='test'; $env:ENVIRONMENT='test'
.\.venv\Scripts\python.exe -m pytest -q `
  tests/test_profitability_monetary_composition_v1.py `
  tests/test_profitability_currency_policy_a_wiring.py `
  tests/test_dashboard_kpi_metrics.py `
  tests/test_operational_data_gaps.py `
  tests/test_pricing_registry.py `
  tests/test_cost_engine_config.py `
  --ignore=tests/manual

# 4) live stack health (stack running)
Invoke-WebRequest http://127.0.0.1:8000/health
Invoke-WebRequest http://127.0.0.1:3000/
```

---

## 12. Common failures

| Symptom | Check |
|---------|--------|
| Port occupied unhealthy | Report blocker; Owner GO before `stop-dev.ps1` |
| `/health` down | `.workos-dev-logs/backend-*.err.log` |
| Auth loop | Dev auth flags / JWT secret mismatch |
| Migration error | Backup first; run upgrade on copy |
| Mixed currency KPI `—` | Expected when quote currencies differ |
