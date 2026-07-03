# BUILD — Operational Resource Mapping Architecture Lock

**Date:** 2026-06-10  
**Type:** Documentation only  
**Runtime:** Not touched  
**Status:** **PASS**

---

## Branch and HEAD

| Item | Value |
|------|-------|
| Branch | `local/integration-pr4-plus-svg-path` |
| HEAD | `af9dc93` — `fix(quotes): open created commercial quote from handoff` |

---

## Audit mode

**Read-only architectural audit** completed prior to this build. No runtime logic, migrations, seeds, CostEngine, payroll, ProductSystem runtime, production dispatch, or inventory changes.

Audit conclusion: WorkOS already has an **Operational Workforce & Resource Registry** foundation (s43). Gaps are UI admin, ProductSystem↔registry bridge, explicit multi-employee authorization, extended mappings, HR demo separation, and Utilaje `capacity_metadata` exposure.

---

## Scope

Lock architectural decisions in official documentation **before any implementation**:

1. Persist audit findings as architecture reference.
2. Document three operation code namespaces and critical bridge gap.
3. Lock **HYBRID** authorization model (skill rule + explicit override + runtime pool).
4. Lock salary / CostEngine boundary (aggregate only — no per-operation individual salary in quotes).
5. Capture proposed real employee and machine mappings (reference only — seed not run).

---

## Documents created

| Path | Action | Purpose |
|------|--------|---------|
| `docs/architecture/OPERATIONAL_RESOURCE_MAPPING_ARCHITECTURE.md` | **Created** | Canonical architecture lock — current state, boundaries, gaps, model, mappings, roadmap |
| `docs/qa/BUILD_OPERATIONAL_RESOURCE_MAPPING_ARCHITECTURE.md` | **Created** | This QA record |

**Allowed files modified:** docs only (see above).  
**No other files modified.**

---

## Zones / files inspected (read-only audit)

### Backend

| Zone | Paths inspected |
|------|-----------------|
| Employee model & CRUD | `backend/models/employees.py`, `backend/routers/employees.py`, `backend/services/employees.py` |
| Operational registry | `backend/models/operational_registry.py`, `backend/services/operational_registry_service.py`, `backend/routers/operational_registry.py` |
| Migration | `backend/alembic/versions/s43_operational_resource_registry_foundation.py` |
| Operator / execution | `backend/services/operator_employee_guard.py`, `backend/routers/operator_tasks.py`, `backend/services/execution_reality_workforce.py`, `backend/services/order_execution_snapshot_mapper.py` |
| CostEngine config | `backend/services/cost_engine_config.py` (boundary verification only) |
| Machines read | `backend/routers/machines.py`, `backend/services/machines_read_service.py` |
| Manual seed | `backend/seeds/seed_operational_workforce_registry.py` |
| Mock boot data | `backend/mock_data/employees.json`, `backend/services/mock_data.py` |
| Volumetric dossier | `backend/seeds/seed_tpl_volumetric_letters_dossier.py` |
| Tests | `backend/tests/test_operational_resource_registry.py`, `test_operator_employee_selection.py`, `test_execution_reality_workforce_capture.py`, `test_field_installation_team_allocation.py`, `test_operational_reports.py` |

### Frontend

| Zone | Paths inspected |
|------|-----------------|
| Registry client | `frontend/src/api/operationalRegistry.ts` |
| Operator / tablet | `frontend/src/lib/operatorEmployeeEligibility.ts`, `frontend/src/lib/tabletLiveBridge.ts`, `frontend/src/lib/workstationRouting.ts`, `frontend/src/hooks/useTabletStationData.ts`, `frontend/src/pages/TabletMode.tsx`, `frontend/src/pages/OperatorView.tsx` |
| Utilaje | `frontend/src/pages/Utilaje.tsx`, `frontend/src/hooks/useMachinesData.ts` |
| HR demo | `frontend/src/lib/employeeRecordsData.ts`, `frontend/src/pages/EmployeesRecords.tsx`, `Attendance.tsx`, `EmployeePayments.tsx` |
| CostEngine employees UI | `frontend/src/pages/Employees.tsx` |
| Field teams | `frontend/src/components/workos/FieldInstallationTeamPanel.tsx` |
| Reports / review | `frontend/src/pages/OperationalReports.tsx`, `OperationalRealityReview.tsx` |
| Readiness doc | `frontend/docs/atoms/PERSONAL_INTERNAL_RECORDS_BACKEND_READINESS.md` |

### Prior QA builds referenced

- `docs/qa/BUILD_OPERATIONAL_WORKFORCE_RESOURCE_REGISTRY_FOUNDATION.md`
- `docs/qa/BUILD_OPERATOR_EMPLOYEE_SELECTION_AUTHORIZATION_GUARD.md`
- `docs/qa/BUILD_TABLET_LIVE_WIRING_STATION_EMPLOYEE.md`
- `docs/qa/BUILD_FIELD_INSTALLATION_TEAM_ALLOCATION.md`
- `docs/qa/BUILD_EXECUTION_REALITY_WORKFORCE_CAPTURE.md`
- `docs/qa/BUILD_OPERATIONAL_REPORTS_FOUNDATION.md`

---

## Short conclusion

WorkOS **already implements** the operational workforce registry foundation: employees with M2M skill/workcenter/resource authorizations, unified `machines` registry (machine/tool/work_area), `operation_resource_requirements`, registry API, soft operator guard, tablet bridge, field installation teams, execution reality workforce capture, and operational reports.

**Missing for the owner’s full vision:** admin UI, canonical ProductSystem↔registry bridge, explicit per-operation multi-employee authorization table/field, extended operation mappings (laminare, cutter, prepress), clear HR-demo vs registry separation, and Utilaje display of `capacity_metadata`.

This build **locks decisions** in documentation only — no code changes.

---

## Gaps documented (not fixed in this build)

| Gap | Severity | Target build |
|-----|----------|--------------|
| ProductSystem dossier codes ≠ registry codes | Critical | Build 3 |
| No `operation ↔ employee` direct authorization | Medium | Build 3 / 4 |
| Registry has 9 mappings vs ~50 frontend routing entries | High | Build 3 |
| Missing registry ops: laminare, cutter_plotter, prepress | Medium | Build 3 |
| Utilaje UI ignores DB `capacity_metadata` | Low | Build 2 |
| HR Personal (pontaj/plăți) is frontend demo only | Medium | Separate HR build |
| Manual seed not auto-run; mock employees on dev boot | Medium | Build 2 procedure |
| Foundation `public.roles/skills` not in local SQLite | Low | Build 2 catalog wiring |

---

## Boundaries preserved

| Area | Status |
|------|--------|
| CostEngine | ❌ Not modified |
| Pricing / quote_orchestrator | ❌ Not modified |
| Payroll / pontaj | ❌ Not modified |
| ProductSystem runtime | ❌ Not modified |
| Production dispatch | ❌ Not modified |
| Inventory | ❌ Not modified |
| DB schema / migrations | ❌ Not modified |
| Seeds (create / run) | ❌ Not modified |
| Runtime code | ❌ Not modified |

### Salary boundary (locked in architecture doc)

- `cost_lunar_firma` on `employees` — HR / aggregate CostEngine input ✅
- Aggregate `cost_ora_manopera_default` in CostEngine config — exists today ✅
- Individual salary as operation quote price — ❌ forbidden until Build 6 + owner decision

### Authorization boundary (locked)

- **HYBRID:** skill-based rule + explicit employee override + runtime pool selection
- **Soft guard** on mismatch — no hard-block yet

---

## Locked architectural decisions

1. Reuse s43 registry (`employees`, M2M authorizations, `machines`, `operation_resource_requirements`).
2. Work areas = `machines` with `resource_kind=work_area` (no separate table initially).
3. Three operation code namespaces documented; **bridge is mandatory** — never in CostEngine.
4. Explicit multi-employee authorization via future junction table **or** `authorized_employee_ids[]`.
5. Real employee/machine tables in architecture doc are **proposed reference** aligned to manual seed script — not auto-run.
6. TPL-VOLUMETRIC-LETTERS conceptual mapping table guides Build 3 only.

---

## Commands run

```powershell
git status --short
git diff --stat
```

No `tsc`, `pytest`, or `validate:frontend` — docs-only build.

---

## Next recommended build

**Build 2 — Employee Skills & Machine Registry Foundation UI**

- Admin CRUD for registry employees, skills, resources
- Utilaje reads `capacity_metadata` from DB
- Document procedure for manual seed vs mock employees
- Do not touch CostEngine or ProductSystem runtime

---

## PASS / FAIL criteria

| Criterion | Result |
|-----------|--------|
| Only docs modified | ✅ PASS |
| Hybrid authorization documented | ✅ PASS |
| Salary boundary (HR / aggregate CostEngine) documented | ✅ PASS |
| ProductSystem ↔ registry bridge marked critical gap | ✅ PASS |
| No runtime code changes | ✅ PASS |
| No seed / migration | ✅ PASS |
| CostEngine untouched | ✅ PASS |
| No hardcoded runtime mappings | ✅ PASS |
| Individual salary as quote price | ✅ Not introduced |

**Overall: PASS**

---

## Recommended commit message

```
docs: lock operational resource mapping architecture
```

---

*End of QA record.*
