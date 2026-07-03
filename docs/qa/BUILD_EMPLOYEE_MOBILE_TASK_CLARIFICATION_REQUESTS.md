# BUILD: Employee Mobile Task Clarification Requests

## 1. Purpose

Allow shop-floor employees to ask for **production clarifications** from task detail via **Solicit informații**, without blocking the task or mixing with HR `employee_requests`.

**Base commit:** `a4f4483` — `chore(employee): add reproducible Sandu mobile fixture`

## 2. Audit — existing mechanisms

| Mechanism | Verdict |
|-----------|---------|
| `employee_requests` | HR (concedii, avansuri) — **not suitable** |
| `execution_reality` block/pause | Changes task runtime status — **not suitable** for info-only asks |
| `execution_plan.tasks_json.instructions` | Admin/operator execution instructions — **read-only on mobile** (unchanged) |
| Audit log / output blocks `internal_note` | Journal/archive — **not an inbox** |
| Operational registry `internal_notes` | Admin HR/reporting — **not task-scoped mobile inbox** |
| Quote/intake notes | Commercial/intake scope — **not employee task channel** |

**Decision:** **Variant A** — new table `task_clarification_requests`.

## 3. Blochez vs Solicit informații

| | **Blochez** | **Solicit informații** |
|---|-------------|-------------------------|
| Initiator | Employee (execution action) | Employee (clarification ask) |
| Task status | Becomes `blocked` in reality | **Unchanged** |
| Purpose | Stop work — material/issue | Ask missing detail / unclear sketch |
| Visibility | Block reason on task | Open request for operator/admin |
| Resolve | Unblock action | Operator marks **resolved** |

## 4. Status model

| Status | Meaning |
|--------|---------|
| `open` | Waiting for operator/admin response/action |
| `resolved` | Closed by admin/operator/manager |
| `cancelled` | Reserved — not exposed in UI yet |

Duplicate control: one **open** request per `(order_id, task_id, employee_id)` — second create returns **409** `open_clarification_exists`.

## 5. Permissions

| Action | Who |
|--------|-----|
| Create request | `employee_mobile` on **own assigned tasks** |
| View open status on task | Same employee (in task list payload) |
| List requests | `admin`, `manager`, `operator` — `execution.clarification_list` |
| Resolve | `admin`, `manager`, `operator` — `execution.clarification_resolve` |
| Resolve | **Not** `employee_mobile` |

## 6. Implemented

### Backend

- Model: `backend/models/task_clarification_request.py`
- Service: `backend/services/task_clarification_request_service.py`
- Employee API: `POST /api/v1/employee-mobile/tasks/{task_id}/clarification-requests`
- Task list enrichment: `clarification_request` on open requests
- Operator API:
  - `GET /api/v1/operator/clarification-requests?status=open`
  - `PATCH /api/v1/operator/clarification-requests/{id}/resolve`
- Permissions: `execution.clarification_list`, `execution.clarification_resolve`

### Frontend

- `EmployeeMobileTaskClarificationPanel` in task detail — **Ai nevoie de detalii?** / **Solicit informații**
- `OperatorClarificationRequestsPanel` on Operator View (wired DB mode)
- **Home unchanged**

## 7. Not implemented

- Chat / reply thread
- Push notifications
- Auto-block on clarification
- Employee-side resolve/cancel UI
- Email/Slack routing

## 8. Smoke — Sandu

```powershell
$env:WORKOS_DEV_AUTH_USER_ID='dev-sandu-employee-001'
# Task detail → Solicit informații → Trimite solicitarea
# Operator View → Solicitări informații → Marchează rezolvat
```

## 9. Tests

Backend:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_task_clarification_requests.py tests/test_employee_mobile_tasks.py -q
```

Frontend:

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/EmployeeMobileApp.test.tsx
```

## Boundary

Clarification requests are production coordination signals — not HR requests, not task blocks, not commercial document exposure.
