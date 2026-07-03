# BUILD: Shared / Assistable Task Work Sessions Foundation

**Date:** 2026-06-12  
**Status:** **PASS — uncommitted**  
**Branch:** `local/integration-pr4-plus-svg-path`  
**HEAD at start:** `45c7fd4` (+ uncommitted pipeline-first frontend from prior build)

---

## 1. Motiv

Producția reală (litere volumetrice, LED, asamblare, canturi) implică adesea mai mulți oameni pe același task. Modelul rigid `task = un singur angajat` nu reflectă realitatea.

## 2. Principiu

```text
responsabil principal + executanți activi + participanți istorici + log intrare/ieșire
```

Fără payroll/bani în acest build — modelul pregătit pentru ore viitoare.

## 3. Model work sessions (MVP)

Sursă: `execution_reality.tasks_json` — fiecare sesiune = observație separată.

Câmpuri minime:

- `session_id`
- `task_id`, `employee_id`, `employee_name`
- `role`: `primary | helper`
- `session_type`: `work | assist`
- `started_at`, `ended_at`, `duration_minutes`
- `status`: `in_progress | ended | completed | blocked`
- `source`

Service: `backend/services/task_work_session_service.py`

## 4. Comportament

| Acțiune | Regulă |
|---------|--------|
| Start (angajat propriu) | Creează sesiune `primary/work`; refuză duplicat activ același employee+task |
| Start (alt angajat, același task) | Permis — sesiune separată (helper/assist) |
| Finalize | Închide sesiunea activă a angajatului (`employee_id`); setează `duration_minutes`, `completed_by_*` |
| Block | Marchează sesiunea activă a angajatului ca `blocked` |
| Stop fără finalizare | **Deferred** — modelul suportă `ended` fără `completed_by` |

Flow mobile Start/Block/Complete rămâne compatibil.

## 5. Operator blueprint

Per task (read-only):

- `active_workers[]` (nume + rol)
- `participants_count`
- `work_sessions_count`
- `total_logged_minutes` (doar sesiuni închise)
- `last_worked_at`

## 6. Employee-safe mobile

- Fără nume ale altor angajați în blueprint employee
- `active_helper_count` pe taskurile mele (ex: `Ajutor activ: 1`)
- Non-mine rămâne `În lucru la alt post` / `Alt post`
- `can_assist` / buton **Ajută la task** — **deferred**

## 7. Eligibility foundation (deferred engine)

Câmpuri employee-safe adăugate:

- `is_eligible_for_me`
- `can_assist` (false MVP)
- `eligibility_reason`
- `active_helper_count`

Flag `assistable` pe plan tasks — **deferred** (nu inventat universal).

## 8. Tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_employee_mobile_tasks.py tests/test_operator_production_blueprint.py tests/test_employee_mobile_order_blueprint.py tests/test_task_work_sessions.py -q
```

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/employeeMobileAccess.test.ts src/lib/employeeMobileTaskSummary.test.ts src/lib/employeeMobileTaskViews.test.ts src/lib/employeeMobilePipelineEligibility.test.ts src/pages/EmployeeMobileApp.test.tsx
```

## 9. Smoke Sandu (read-only)

Backend: `WORKOS_DEV_AUTH_USER_ID='dev-sandu-employee-001'`

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/auth/me
Invoke-RestMethod http://127.0.0.1:8000/api/v1/employee-mobile/tasks
Invoke-RestMethod http://127.0.0.1:8000/api/v1/employee-mobile/orders/1/my-blueprint
```

Nu s-au pornit/oprit taskuri în smoke (fără mutații dev.db).

## 10. Smoke Operator

**Neexecutat** — necesită Dev Admin explicit; backend rămas pe Sandu.

## 11. Deferred

- `start_assist_task` / `end_assist_task` endpoints
- Buton **Ajută la task**
- Motor eligibilitate `Pot ajuta`
- Payroll / time approval / productivity scoring
- Websocket / push notifications
- Stop session fără finalizare (UI)

## 12. Side effects dev.db

Niciuna intenționată în smoke. Testele pytest folosesc DB izolat de fixture.

## Files changed

**Backend**

- `backend/services/task_work_session_service.py` (new)
- `backend/services/execution_reality_service.py`
- `backend/services/employee_mobile_tasks_service.py`
- `backend/services/order_production_blueprint_service.py`
- `backend/services/employee_mobile_order_blueprint_service.py`
- `backend/routers/employee_mobile_tasks.py`
- `backend/tests/test_task_work_sessions.py` (new)

**Frontend** (minimal, cu pipeline-first uncommitted)

- `frontend/src/api/employeeMobileOrderBlueprint.ts`
- `frontend/src/components/workos/employee-mobile/EmployeeMobileOrderPipelineView.tsx`

**Docs**

- `docs/qa/BUILD_SHARED_ASSISTABLE_TASK_WORK_SESSIONS.md`

## Proposed commit message

```
feat(employee): add shared task work sessions foundation
```
