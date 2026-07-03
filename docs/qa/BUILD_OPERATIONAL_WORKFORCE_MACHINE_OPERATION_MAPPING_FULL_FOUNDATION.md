# BUILD — Operational Workforce, Machine & Operation Mapping Full Foundation

**Date:** 2026-06-10  
**Branch:** `local/integration-pr4-plus-svg-path`  
**Base HEAD:** `f89a866` — docs: lock operational resource mapping architecture  
**Status:** **PASS** (targeted tests)

---

## Scope

Single coherent foundation build covering:

| Module | Deliverable |
|--------|-------------|
| M1 | Admin UI Angajați + M2M skills/workcenters/resources |
| M2 | Utilaje registry + `capacity_metadata` edit |
| M3 | Operational catalog (skills/workcenters/resources) |
| M4 | ProductSystem operation resource mapping UI |
| M5 | Eligibility pool preview (operator, soft guard) |
| M6 | Manual seed documentation (no auto-run) |
| M7 | This QA doc |

---

## Schema / migration

**Migration required:** `s45_operation_authorization_foundation`

| Addition | Purpose |
|----------|---------|
| `operation_employee_authorizations` | Explicit multi-employee per operation |
| `operation_resource_requirements.authorization_mode` | skill \| explicit \| hybrid |
| `operation_resource_requirements.default_resource_code` | Optional default machine |
| `operation_resource_requirements.product_system_aliases` | ProductSystem ↔ registry bridge |

Local dev SQLite: tables created via `Base.metadata.create_all` when models imported; Alembic `s45` for staged environments.

---

## Backend reused / extended

| Artifact | Change |
|----------|--------|
| `models/operational_registry.py` | `OperationEmployeeAuthorization`, extended `OperationResourceRequirement` |
| `services/operational_catalog.py` | **New** — SK_* / WC_* catalog + suggested aliases |
| `services/operational_registry_service.py` | resolve mapping, eligible pool, catalog, resource upsert merge |
| `routers/operational_registry.py` | `/catalog`, `PUT /resources`, eligible-employees, resolve |
| `services/operator_employee_guard.py` | Hybrid eligibility via registry service |

**Not modified:** CostEngine, pricing, quote_orchestrator, payroll, inventory, dispatch hard rules.

---

## Frontend

| File | Role |
|------|------|
| `api/operationalRegistry.ts` | Extended types + write APIs |
| `features/operational-registry/*` | Panels + hybrid eligibility |
| `pages/Employees.tsx` | Registry authorizations panel (not HR demo) |
| `pages/Utilaje.tsx` | Registry resource editor + capacity from DB |
| `pages/ProductSystem.tsx` | Tab „Resurse operaționale” |
| `pages/OperatorView.tsx` | Eligible pool preview |
| `hooks/useMachinesData.ts` | Maps `capacity_metadata` to specs |

**HR demo unchanged:** `employeeRecordsData.ts` / Personal routes remain separate.

---

## Manual seed (Module I — not auto-run)

Script: `backend/seeds/seed_operational_workforce_registry.py`

**Run manually only:**

```powershell
$env:APP_ENV='development'
$env:ENVIRONMENT='development'
$env:DATABASE_URL='sqlite+aiosqlite:///C:/Users/offic/workos/backend/dev.db'
$env:JWT_SECRET_KEY='local-dev-secret-not-for-production'
cd backend
.\.venv\Scripts\python.exe -c "import asyncio; from seeds.seed_operational_workforce_registry import seed_operational_workforce_registry; print(asyncio.run(seed_operational_workforce_registry()))"
```

**Creates:** 8 real employees, 14 resources, 9 operation mappings (idempotent).  
**Does not:** run on dev boot; replace mock employees without operator confirmation; touch CostEngine.

**Verify:** `GET /api/v1/operational-registry/employees`, `/resources`, `/operation-mappings`.

---

## Tests run

### Backend

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_operational_resource_registry.py tests/test_operational_authorization_foundation.py tests/test_operator_employee_selection.py -q
```

### Frontend

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/features/operational-registry/operationEligibility.test.ts src/lib/operatorEmployeeEligibility.test.ts
npx --yes pnpm@8.10.0 exec tsc -b --noEmit
```

---

## Runtime smoke

| Step | Expected |
|------|----------|
| `/employees` | Select employee → edit skills/workcenters/resources → save |
| `/utilaje` | DB resource → view/edit `capacity_metadata` JSON |
| ProductSystem editor → Resurse operaționale | Map operation → save → refresh persists |
| `/operator` | Pool eligibil preview; neautorizat = warning not block |

Smoke requires stack + optional manual seed. Not run automatically in this build log.

---

## Boundaries confirmed

| Area | Status |
|------|--------|
| CostEngine formulas | ❌ Not modified |
| Salary per operation in quotes | ❌ Not introduced |
| Hard-block authorization | ❌ Not enabled |
| Seed auto-run | ❌ Not linked |
| HR demo wholesale replacement | ❌ Not done |

---

## Gaps remaining

- Full catalog admin CRUD (skills/workcenters as DB entities vs static catalog)
- Automatic activation of TPL volumetric mappings (UI only — operator configures)
- Utilaje create-new-resource UI (upsert existing codes only)
- Foundation `public.roles` SQLite wiring
- Runtime smoke evidence (environment-dependent)

---

## Next steps

1. Run manual seed in staging after owner review
2. Configure TPL-VOLUMETRIC-LETTERS mappings via ProductSystem tab
3. Build 5 — operational reports by employee/machine/work area
4. Build 6 — cost reality integration **only if owner decides**

---

## PASS criteria

| Criterion | Result |
|-----------|--------|
| Multi skills per employee | ✅ |
| capacity_metadata admin | ✅ |
| Operation mapping UI | ✅ |
| Multi authorized employees | ✅ |
| Pool preview soft | ✅ |
| CostEngine untouched | ✅ |
| No seed auto-run | ✅ |

**Overall: PASS**
