# BUILD: Employee Mobile My Order Blueprint

## 1. Scop

Versiune limitată de blueprint pe telefon: angajatul vede contextul comenzii unde are taskuri — progres, flux, taskuri proprii evidențiate — fără vedere managerială completă.

## 2. Diferență Operator vs Employee Blueprint

| | Operator/Admin | Employee Mobile |
|---|----------------|-----------------|
| Audiență | admin, manager, operator | employee_mobile (self) |
| Taskuri | toate, inclusiv neatribuite | flux complet, evidențiere `is_mine` |
| Angajați | nume, active workers | fără nume alți angajați |
| Editare | assign/instructions (alte panouri) | read-only |
| Endpoint | `/api/v1/operator/orders/{id}/production-blueprint` | `/api/v1/employee-mobile/orders/{id}/my-blueprint` |

## 3. Security boundary

- Acces doar dacă angajatul are cel puțin un task pe comandă (`list_my_tasks` + 403).
- Fără cost, preț, marjă, payroll, `prepared_by`, `target_user_id`.
- Fără `assigned_employee_name` / `active_worker_name` în payload employee.
- Operator role → 403 pe ruta employee-mobile.

## 4. Payload

Service: `backend/services/employee_mobile_order_blueprint_service.py`  
Reutilizează `get_order_production_blueprint()` intern, mapează la payload employee-safe.

## 5. UI

- Card compact **Comanda mea** pe pagina Taskuri (fără redesign Home/nav).
- Link **Vezi blueprint** pe lista Comenzi.
- Pagină `/employee-app/tasks/orders/:orderId/blueprint` — summary + flux taskuri.

## 6. Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_employee_mobile_tasks.py tests/test_operator_production_blueprint.py tests/test_employee_mobile_order_blueprint.py -q
```

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/employeeMobileAccess.test.ts src/lib/employeeMobileTaskSummary.test.ts src/lib/employeeMobileTaskViews.test.ts src/pages/EmployeeMobileApp.test.tsx
```

## 7. Smoke Sandu

Backend cu `WORKOS_DEV_AUTH_USER_ID='dev-sandu-employee-001'`.

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/auth/me
Invoke-RestMethod http://127.0.0.1:8000/api/v1/employee-mobile/orders/1/my-blueprint
```

Browser: `http://127.0.0.1:3000/employee-app/tasks` → card Comanda mea → blueprint.

## 8. Deferred

- Full mobile admin blueprint
- Websocket / push notifications
- Payroll / bani angajați
- Gantt / timeline complex

## Files changed

- `backend/services/employee_mobile_order_blueprint_service.py`
- `backend/routers/employee_mobile_tasks.py`
- `backend/tests/test_employee_mobile_order_blueprint.py`
- `frontend/src/api/employeeMobileOrderBlueprint.ts`
- `frontend/src/components/workos/employee-mobile/EmployeeMobileOrderBlueprintPage.tsx`
- `frontend/src/components/workos/employee-mobile/EmployeeMobileTasksPanel.tsx`
- `frontend/src/pages/EmployeeMobileApp.tsx`
- `docs/qa/BUILD_EMPLOYEE_MOBILE_MY_ORDER_BLUEPRINT.md`

## Proposed commit message

```
feat(employee): add mobile order blueprint
```
