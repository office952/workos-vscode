# BUILD: Order Production Blueprint + Live Task Ownership

## 1. Scop

Oferă operatorului/adminului vizibilitate read-only asupra stării execuției pe comandă: cine lucrează, ce taskuri sunt în lucru/blocate/finalizate, progres simplu, documente/instrucțiuni/clarificări — fără state paralel și fără date comerciale.

## 2. De ce contează cine lucrează la task

Planul (`execution_plan.tasks_json`) spune ce trebuie făcut; realitatea (`execution_reality.tasks_json`) spune cine a pornit, când, dacă e blocat sau finalizat. Blueprint-ul combină cele două pentru decizii operaționale rapide fără a deschide mobile-ul fiecărui angajat.

## 3. Sursa de adevăr

| Layer | Rol |
|-------|-----|
| `execution_plan.tasks_json` | Task planificat, assignee plan, instrucțiuni, documente handoff |
| `execution_reality.tasks_json` | Observații: `started_at`, `ended_at`, `employee_id`, `blocked_at`, `block_reason` |

Nu există status mobile-only sau dashboard mock.

## 4. Audit — câmpuri existente (Faza 1)

| Acțiune | Unde se salvează |
|---------|------------------|
| Start (Sandu/operator) | `ExecutionRealityService.start_task` → append în `tasks_json` cu `started_at`, `employee_id`, `employee_name` |
| Complete | `ExecutionRealityService.end_task` → `ended_at`, `completed_by_employee_id` |
| Block | update direct `tasks_json`: `blocked_at`, `block_reason` |
| Status derivat | `derive_task_status()` în `employee_mobile_tasks_service.py` |
| Operator list | `GET /api/v1/operator/tasks` — deja derivă status din reality |

**Ce lipsea:** un payload read-only per comandă cu summary + active workers + indicatori doc/instrucțiuni/clarificări pentru Operator View.

## 5. Status model (derivare)

| Blueprint status | Regulă |
|------------------|--------|
| `done` / Finalizat | `ended_at` sau status `done` |
| `blocked` / Blocat | `blocked_at` fără `unblocked_at` |
| `in_progress` / În lucru | `started_at`, nefinalizat/neblocat (include `paused`) |
| `todo` / De făcut | assignee plan, fără start |
| `unassigned` / Neatribuit | fără `assigned_employee_id` |

Helper reutilizat: `derive_task_status()` + `blueprint_status_bucket()`.

## 6. Blueprint endpoint

```
GET /api/v1/operator/orders/{order_id}/production-blueprint
```

- Permisiune: `execution.production_blueprint` (admin, manager, operator)
- Service: `backend/services/order_production_blueprint_service.py`
- Read-only strict — nu scrie plan/reality

## 7. Operator UI

- `OperatorProductionBlueprintPanel` în `OperatorView`
- Summary chips, secțiune „Lucrează acum”, listă taskuri
- Selector comandă din order IDs din taskurile operator
- Collapsible

## 8. Employee Mobile micro-display

- Banner contextual în task detail (fără redesign Home/nav):
  - În lucru de la …
  - Blocat: motiv
  - Finalizat la …
- Endpoint mobile blueprint: **deferred** (prioritate operator)

## 9. Polling / live-ish

- Fără websocket
- Panel operator: refetch la 15s când panelul e deschis + buton manual
- Nu polling global

## 10. Security boundary

- Fără cost, preț, marjă, quote PDF
- `employee_mobile` → 403 pe blueprint global
- Documente = count/metadata din plan handoff, nu commercial docs

## 11. Tests

Backend:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_operator_production_blueprint.py tests/test_employee_mobile_tasks.py tests/test_task_clarification_requests.py tests/test_volumetric_return_task_taxonomy.py tests/test_execution_plan_prepared_by.py -q
```

Frontend safety (dacă atins):

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/employeeMobileAccess.test.ts src/lib/employeeMobileTaskSummary.test.ts src/lib/employeeMobileTaskViews.test.ts src/pages/EmployeeMobileApp.test.tsx
```

## 12. Smoke

**Admin** (backend fără `WORKOS_DEV_AUTH_USER_ID`):

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/operator/orders/1/production-blueprint
```

**Sandu** (backend cu `$env:WORKOS_DEV_AUTH_USER_ID='dev-sandu-employee-001'`):

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/employee-mobile/tasks
```

## 13. Side effects dev.db

- Blueprint read-only — fără side effect la GET
- Smoke Start/Block/Complete rămâne out-of-scope dacă nu e cerut explicit

## 14. Deferred

- Websocket / push notifications
- Gantt / drag-and-drop
- Per-station queue avansat
- Payroll / bani angajați
- Advanced planning engine
- `GET /employee-mobile/orders/{id}/my-production-blueprint`

## Files changed

- `backend/services/order_production_blueprint_service.py`
- `backend/routers/operator_tasks.py`
- `backend/dependencies/permissions.py`
- `backend/tests/test_operator_production_blueprint.py`
- `frontend/src/api/operatorProductionBlueprint.ts`
- `frontend/src/components/workos/OperatorProductionBlueprintPanel.tsx`
- `frontend/src/pages/OperatorView.tsx`
- `frontend/src/components/workos/employee-mobile/EmployeeMobileTasksPanel.tsx`
- `docs/qa/BUILD_ORDER_PRODUCTION_BLUEPRINT_AND_LIVE_TASK_OWNERSHIP.md`

## Proposed commit message

```
feat(employee): add production blueprint and live task ownership
```
