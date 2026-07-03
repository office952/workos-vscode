# BUILD — Operator Employee Selection & Authorization Guard

**Date:** 2026-06-09  
**Status:** Implemented  
**Prerequisite:** Operational Workforce & Resource Registry Foundation (PASS)

## Scope

Connect `/operator` to the operational registry for real employee selection on task Start, with minimal backend authorization guard. No Quote/Pricing/CostEngine/tablet changes.

## Files modified

| File | Change |
|------|--------|
| `backend/services/operator_employee_guard.py` | Employee validation + soft authorization warnings |
| `backend/routers/operator_tasks.py` | Guard on start; employee fields in GET tasks + reality |
| `frontend/src/pages/OperatorView.tsx` | Employee selector from registry |
| `frontend/src/hooks/useOperatorEmployees.ts` | Load registry employees + eligibility |
| `frontend/src/hooks/useOperatorData.ts` | Map employee from API; send employee_id + operator_name |
| `frontend/src/lib/operatorEmployeeEligibility.ts` | Client-side eligibility helpers |
| `frontend/src/api/operationalRegistry.ts` | `listActiveEmployees`, salary-stripped type |
| `frontend/src/lib/mockData.ts` | Optional `employeeId` / `employeeName` on OperatorTask |

## How employees load in /operator

1. `useOperatorEmployees` calls `GET /api/v1/operational-registry/employees`
2. Filters `status === "active"`
3. Loads operation mappings for eligibility against next Start candidate
4. No salary fields rendered in UI

## Employee selection UX

- Dropdown „Angajat activ (registry)" above operator header
- Shows name, role, eligibility badge (Autorizat / Neautorizat / Neconfirmat)
- Start disabled when registry has employees but none selected
- Registry failure → legacy Start without employee (backward compatible)

## Start task payload

```json
{
  "order_id": 1,
  "task_id": "T-001",
  "action": "start",
  "employee_id": 3,
  "operator_name": "Calin Cimpean"
}
```

## execution_reality persistence

On successful start, `tasks_json` entry receives:
- `employee_id`
- `employee_name`
- `operator_name` (compat)

GET `/api/v1/operator/tasks` returns these fields for UI timeline.

## Authorization guards

| Check | Hard block? |
|-------|-------------|
| employee_id not found | ✅ 422 |
| employee not active | ✅ 422 |
| skill/workcenter/resource mismatch | ❌ warning only |
| no operation mapping | ❌ warning only |
| no employee_id (legacy) | ❌ allowed + warning |

## Boundaries

- ❌ Quote / Pricing / CostEngine untouched
- ❌ /tablet untouched
- ❌ No auto-assignment
- ❌ No salary in /operator UI
- ✅ Employee without User works

## Tests

```bash
# Backend
cd backend
.venv\Scripts\python.exe -m pytest tests/test_operator_employee_selection.py -v

# Frontend
cd frontend
npm run test -- src/lib/operatorEmployeeEligibility.test.ts src/hooks/useOperatorData.employee.test.ts
```
