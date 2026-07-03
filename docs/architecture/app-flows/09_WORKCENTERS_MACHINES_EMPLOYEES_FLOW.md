# Workcenters, Machines, and Employees Flow

**Current status:** PARTIAL

---

## 1. Purpose

Document **operational capacity registry** (workcenters, utilaje/machines) and **HR registry** (employees, roles, skills) — what exists admin-side vs what is **not yet linked** to ExecutionPlan V2 planned/materialized tasks.

---

## 2. Current status

**PARTIAL** — foundation APIs and UI pages exist; frozen snapshot parent ops have **null workcenter**; no eligibility on planned graph; assignment requires materialized operational tasks.

---

## 3. Pages / UI surfaces

| Route/Page | Component/File | Role | Reads | Writes | Status | Risk |
| ---------- | -------------- | ---- | ----- | ------ | ------ | ---- |
| `/utilaje` | `Utilaje` | Machines/utilaje admin | utilaje API | CRUD | PARTIAL | Not on frozen ops |
| `/employees` | `Employees` | Employee list | employees API | CRUD | PARTIAL | HR only |
| `/employees-records/:id` | `EmployeeProfile` | Profile | employee row | edit | PARTIAL | — |
| `/operator`, `/tablet/*` | Operator/tablet views | Shop floor UI | operator tasks | task actions | PARTIAL | Needs materialized tasks |
| `/employee-app/*`, `/employee-app-v2/*` | Employee Mobile | Mobile tasks | mobile APIs | sessions | FROZEN | **final-final** |

---

## 4. Backend routes

| Method | Route | Router/File | Purpose | Reads | Writes | Status | Risk |
| ------ | ----- | ----------- | ------- | ----- | ------ | ------ | ---- |
| GET | `/api/v1/workcenters` | `foundation_workcenters.py` | WC registry | DB/registry | — | VALIDATED | Admin |
| GET | `/api/v1/workcenters/{code}` | same | WC detail | — | — | VALIDATED | — |
| GET | `/api/v1/roles`, `.../skills`, `.../workcenters` | `foundation_roles.py` | Role expansion | registry | — | VALIDATED | — |
| GET | `/api/v1/skills` | `foundation_skills.py` | Skills registry | — | — | VALIDATED | — |
| GET | `/api/v1/operator/tasks` | `operator_tasks.py` | Operator task list | plan operational_tasks | — | PARTIAL | Empty if not materialized |
| POST | execution plan task assignment | `execution_task_assignment_service` | Assign employee | materialized task | tasks_json | BLOCKED_NEEDS_OWNER_GO | v2_not_materialized guard |

---

## 5. Services / schemas / models

| File | Role | Input | Output | Status | Notes |
| ---- | ---- | ----- | ------ | ------ | ----- |
| `execution_task_assignment_service.py` | Assign task to employee | order_id, task_id, employee_id | updated tasks_json | BLOCKED_NEEDS_OWNER_GO | needs operational_tasks |
| `execution_plan_operational_readiness_service.py` | Readiness status | plan | v2_not_materialized | VALIDATED | guards mutations |
| `execution_reality_workforce.py` | Workforce helpers | — | — | PARTIAL | Step 11+ |
| `models/employees.py` | HR persistence | — | ORM | VALIDATED | — |

**Module duplicate ops** (aggregate only) may carry WC (e.g. `WC_FORMING`) but are **excluded** from planned tasks — cannot be used as authoritative WC source without DEC-005.

---

## 6. Data contract

**Workcenter on planned task (target):** `planned_tasks[].machine_requirement.workcenter`

**Current fixture:** all **null** — parent aggregate ops lack WC; module duplicates have WC but are alias-only.

**Role/skill expansion (foundation):** `role.workcenters[]`, `role.skills[]` — admin registry, not copied to plan envelope today.

**Assignment (when allowed):** mutates `operational_tasks[].assigned_employee_id` inside `tasks_json` — no separate `execution_tasks` table in dev.

---

## 7. Links to previous and next systems

| Previous | Link | Next | Link | Strength | Gap |
| -------- | ---- | ---- | ---- | -------- | --- |
| ProductAggregate ops | workcenter field | ExecutionPlan preview | machine_requirement | WEAK | null on parent |
| ExecutionPlan | materialized task | Assignment | employee_id | MISSING | not materialized |
| Roles/skills | foundation API | Eligibility (future) | task filter | MISSING | Faza 5 |
| Workcenters | registry | Utilaje UI | capacity | PARTIAL | Not on plan |
| Sessions | start-task | ExecutionActuals | minutes | FROZEN | Step 11 |

---

## 8. Source of truth

| Aspect | Source |
| ------ | ------ |
| WC registry (admin) | **Foundation workcenters API** |
| WC on execution task (target) | **Frozen aggregate at snapshot + enrichment policy (DEC-005)** |
| Employee master | **employees table / HR UI** |
| Who is assigned (runtime) | **operational_tasks[] in tasks_json** (future) |

---

## 9. What must not happen

- Assign employees to `planned_tasks[]` only (parser uses operational_tasks).
- Use module duplicate WC as production truth without parent canonical policy.
- Employee Mobile production on V2 orders before Faza 10.
- Commercial hourly rates from workcenter registry as client price.

---

## 10. Gaps / risks

| Gap | Severity | Evidence | Blocks what | Recommended action |
| --- | -------- | -------- | ----------- | ------------------ |
| WC null on all planned tasks | CRITICAL | semantic audit | Scheduling, assignment | DEC-005; Faza 2/4 |
| No eligibility model | HIGH | no skill on tasks | Safe assignment | Faza 5 |
| Utilaje disconnected from plan | HIGH | admin only | Capacity truth | Faza 4 |
| Employee Mobile routes exist | MEDIUM | App.tsx | Wrong expectations | Label FROZEN / final-final |

---

## 11. Owner decisions

| Decision ID | Topic | Recommended | Status |
| ----------- | ----- | ----------- | ------ |
| DEC-005 | workcenter source policy | enrich parent at compile + module alias map | PENDING_OWNER |

---

## 12. Verification checklist

```powershell
GET /api/v1/workcenters
GET /api/v1/execution/plan/88002  # inspect tasks_json workcenter fields
Select-String -Path backend\services\execution_task_assignment_service.py -Pattern "operational"
```

---

## 13. Next safe step

Do not assign or Mobile-go until materialize GO + DEC-005; admin registry maintenance only.

**When assignment becomes safe:** Faza 3 materialize + Faza 4 WC truth + Faza 5 eligibility (Doc 21).
