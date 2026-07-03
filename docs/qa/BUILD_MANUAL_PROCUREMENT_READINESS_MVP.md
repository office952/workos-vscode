# BUILD: Manual Procurement Readiness MVP

## Purpose

Enable operator/admin to set **manual procurement status** for project-critical materials. Status can gate task readiness (`waiting_material`) without inventory automation, pricing-as-stock, or consumable micromanagement.

**Boundary:** manual status + readiness only. No reservation, deduction, POs, or supplier workflow.

---

## Preflight

| Check | Result |
|-------|--------|
| Branch | `local/integration-pr4-plus-svg-path` |
| Base HEAD | `94f93c3` — material planning hints foundation |
| Push | not done |
| Sandu auth | `dev-sandu-employee-001` / `employee_mobile` |

---

## Procurement statuses (MVP)

`not_checked`, `check_required`, `suggest_replenish`, `awaiting_advance`, `to_order`, `ordered`, `received`, `available`, `not_required`

### Blocking (only `project_critical` + `can_block_if_missing`)

`awaiting_advance`, `to_order`, `ordered`

### Non-blocking

`not_checked`, `check_required`, `suggest_replenish`, `received`, `available`, `not_required`, all `standard_low_cost_stock`, all `indirect_consumable`

**Policy:** `not_checked` warns only — does not block in MVP.

---

## Persistence decision

**No DB migration.** Manual statuses stored in `execution_reality.tasks_json` as operational meta record:

```json
{
  "task_id": "__workos_material_procurement__",
  "material_procurement_statuses": {
    "LED_MODULE": {
      "status": "awaiting_advance",
      "note": "Se comandă după avans.",
      "affected_task_ids": ["T-006"],
      "updated_by_user_id": "...",
      "updated_at": "..."
    }
  }
}
```

Work-session parsers filter this meta entry via `split_reality_task_entries()`.

---

## Readiness priority

`done` → `blocked_manual` → `in_progress` → `waiting_predecessor` → `waiting_material` → `eligible`

Dependencies dominate materials: T-006 with T-005 open stays `waiting_predecessor` even if LED is `awaiting_advance`. When T-005 is done, T-006 becomes `waiting_material`.

Secondary `material_warning` is included on predecessor-waiting tasks when a blocking material exists.

---

## Backend

| File | Role |
|------|------|
| `material_procurement_status_service.py` | Status apply/summary, employee-safe hints, persistence helpers |
| `task_readiness_service.py` | `waiting_material` integration, material reasons |
| `order_production_blueprint_service.py` | `production_planning_summary`, enriched items |
| `employee_mobile_order_blueprint_service.py` | Safe labels + hints |
| `employee_mobile_tasks_service.py` | Start guard respects material readiness |
| `operator_tasks.py` | `PATCH .../material-procurement/{material_code}` |

**Permission:** `execution.production_blueprint` (admin/manager/operator). Employee mobile denied.

---

## Operator Blueprint

- `production_planning_summary` — eligible / waiting predecessor / waiting material / critical not checked / awaiting advance / suggest replenish / suggested next action
- Per-task procurement fields on `material_planning_items`
- UI: **Control producție** summary + minimal critical-material status editor

---

## Employee Mobile safe boundary

Shows: `Așteaptă material`, `Așteaptă confirmare achiziție`, `Verifică material`, consumable preventive labels.

Hides: cost, price, margin, payroll, supplier, internal operator notes.

Bottom nav unchanged.

---

## Endpoint

```http
PATCH /api/v1/operator/orders/{order_id}/material-procurement/{material_code}
```

Body: `{ "status", "note?", "affected_task_ids?" }`

Note required for `awaiting_advance` and `to_order`.

---

## Tests

### Backend (74 passed — includes prior material/readiness/blueprint suites)

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_material_procurement_status.py tests/test_material_planning_hints.py tests/test_task_readiness_dependencies.py tests/test_employee_mobile_tasks.py tests/test_employee_mobile_order_blueprint.py tests/test_operator_production_blueprint.py -q
```

### Frontend (87 passed)

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/employeeMobileAccess.test.ts src/lib/employeeMobileTaskSummary.test.ts src/lib/employeeMobileTaskViews.test.ts src/lib/employeeMobilePipelineEligibility.test.ts src/pages/EmployeeMobileApp.test.tsx
```

---

## Smoke

- **Sandu API:** T-006 `waiting_predecessor` when T-005 not done; material hints safe; no commercial fields.
- **Operator browser:** deferred for PATCH side-effect on shared dev data; covered by backend PATCH tests + operator panel read path.

---

## Deferred

- Inventory reservation
- Inventory deduction at start
- Supplier workflow / purchase orders
- Automatic stock check (Pricing/Inventory as availability)
- Strict consumable tracking (șuruburi/silicon/cablu per buc)
- Automatic quantity calculation

---

## Proposed commit message (await owner)

`feat(employee): add manual procurement readiness`
