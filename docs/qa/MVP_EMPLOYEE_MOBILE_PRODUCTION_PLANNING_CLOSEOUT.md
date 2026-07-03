# MVP Employee Mobile + Production Planning Closeout

**Date:** 2026-06-14  
**Branch:** `local/integration-pr4-plus-svg-path`  
**Closeout HEAD:** `e895eb1` — `feat(employee): add manual procurement readiness`  
**Push:** not done

---

## 1. Scope închis

This cycle closes the **Employee Mobile + Production Planning MVP** as a testable, coherent operator/employee execution surface — without stock automation, supplier workflow, or financial employee modules.

### Active in MVP

| # | Capability | Primary surfaces |
|---|------------|------------------|
| 1 | Operator Production Blueprint | `/api/v1/operator/orders/{id}/production-blueprint` |
| 2 | Employee Mobile My Order Blueprint | `/api/v1/employee-mobile/orders/{id}/my-blueprint` |
| 3 | Employee Mobile pipeline-first | `/employee-app/tasks` |
| 4 | Shared task work sessions | `execution_reality.tasks_json` work sessions |
| 5 | Task dependencies / readiness | `task_readiness_service`, start guard |
| 6 | Material planning hints (read-only) | `material_planning_service` |
| 7 | Manual procurement readiness | `material_procurement_status_service`, operator PATCH |
| 8 | Employee-safe mobile display | filtered payloads, no commercial fields |
| 9 | Operator Blueprint planning summary | `production_planning_summary`, Control producție |

---

## 2. Commits incluse în ciclu

| Hash | Message |
|------|---------|
| `dca0eec` | feat(employee): add production blueprint and live task ownership |
| `45c7fd4` | feat(employee): add mobile order blueprint |
| `a5303c1` | feat(employee): make mobile tasks pipeline-first |
| `ff1170a` | feat(employee): add shared task work sessions foundation |
| `32da36b` | feat(employee): add task readiness dependencies |
| `e940c07` | docs(employee): audit material planning readiness |
| `94f93c3` | feat(employee): add material planning hints |
| `e895eb1` | feat(employee): add manual procurement readiness |

Supporting fixes in the same branch (taxonomy, documents, clarifications) remain prerequisites but are outside the planning/readiness core listed above.

---

## 3. Ce este activ acum

- Operator sees merged plan + reality blueprint, active workers, readiness, material hints, procurement summary, and minimal critical-material status control (PATCH).
- Employee sees pipeline-first order execution with readiness labels, dependency warnings, discrete material hints, and safe procurement labels — no commercial data.
- Start guard respects dependency priority, then manual procurement blocking (`waiting_material`).
- Procurement statuses persist without DB migration via `__workos_material_procurement__` meta record in `execution_reality.tasks_json`.
- Material hints are derived template rules — `quantity_estimate` stays null; no geometry BOM automation.

---

## 4. Deferred explicit

1. Inventory reservation  
2. Automatic inventory deduction at task start  
3. Supplier workflow  
4. Purchase orders  
5. Automatic stock check (Pricing/Inventory as availability)  
6. Strict tracking of small consumables (șuruburi, silicon, cablu, cleme)  
7. Automatic material quantity calculation from geometry  
8. Assist button / assistable task UI (complete flow)  
9. Auto-scheduling  
10. Payroll / employee financial module  
11. PWA push notifications  
12. Full procurement dashboard  

---

## 5. De ce ne oprim aici

- The current stack is **testable and coherent**: blueprint → pipeline → readiness → hints → manual procurement gate.
- Continuing with stock, supplier, assist, or auto-scheduling would **multiply coupling** (CostEngine, Inventory, commercial) before operators stabilize manual workflows.
- Owner decision: **stabilize and document** before the next cycle.

---

## 6. Boundary-uri (verified)

| Boundary | Status |
|----------|--------|
| CostEngine untouched in this cycle | ✓ |
| Pricing not used as stock availability | ✓ |
| No new inventory reservation | ✓ |
| No new inventory deduction automation | ✓ |
| Small consumables do not block tasks | ✓ |
| Employee Mobile hides cost/price/margin/payroll/supplier/internal notes | ✓ |
| Bottom nav: Acasă / Taskuri / Personal (+ Review only for privileged roles) | ✓ |
| `waiting_material` only via manual blocking procurement status | ✓ |
| Dependencies priority over materials (T-006 + missing T-005 → `waiting_predecessor`) | ✓ |

---

## 7. Known limitations

- Operator browser smoke for PATCH side-effects may be **deferred**; backend tests cover PATCH contract.
- Manual procurement status is **not** supplier workflow or PO generation.
- Material quantities are **hints**, not verified BOM calculations.
- No stock availability automation.
- No purchase orders.
- No complete assist UI.
- No auto-scheduling.
- Browser dev session may show Admin Preview while API smoke uses Sandu fixture auth — UI structure validated separately.

---

## 8. Tests finale

### Backend (cycle targeted)

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_material_procurement_status.py tests/test_material_planning_hints.py tests/test_task_readiness_dependencies.py tests/test_task_work_sessions.py tests/test_employee_mobile_tasks.py tests/test_employee_mobile_order_blueprint.py tests/test_operator_production_blueprint.py -q
```

**Result:** **81 passed**

### Frontend (cycle targeted)

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/employeeMobileAccess.test.ts src/lib/employeeMobileTaskSummary.test.ts src/lib/employeeMobileTaskViews.test.ts src/lib/employeeMobilePipelineEligibility.test.ts src/pages/EmployeeMobileApp.test.tsx
```

**Result:** **87 passed**

---

## 9. Smoke final

### Sandu API — PASS

- Auth: `dev-sandu-employee-001` / `employee_mobile`
- T-004: `in_progress` + dependency context when T-003 not done
- T-006: `waiting_predecessor` when T-005 not done
- T-007: `waiting_predecessor`
- T-008: `eligible`
- Material hints safe; `material_status_label` present; no forbidden commercial fields in payload

### Sandu / Employee browser — PASS

- `/employee-app/tasks`: pipeline-first, readiness visible, discrete material hints
- T-006 marker: „Așteaptă task anterior”
- T-004 dependency warning visible
- Bottom nav: Acasă / Taskuri / Personal
- No console errors observed during closeout snapshot

### Operator / Admin browser — **deferred**

- PATCH + procurement side-effects not forced on shared dev data during closeout.
- Covered by `test_material_procurement_status.py` and operator blueprint backend tests.

---

## 10. Next cycle candidates (no implementation now)

- Manual operator hardening / UX polish  
- Assistable task UI  
- Procurement dashboard  
- Inventory reservation  
- Supplier workflow  
- PWA notifications  
- Payroll / employee financial module  

---

## 11. Cycle stop statement

**No new features should be added in this cycle after this closeout.**

Next work item: stabilization, operator feedback, or a **new scoped cycle** chosen explicitly from deferred list above — not incremental expansion of this MVP.

---

## Related QA docs

- `docs/qa/BUILD_MATERIAL_PLANNING_HINTS_FOUNDATION.md`
- `docs/qa/BUILD_MANUAL_PROCUREMENT_READINESS_MVP.md`
- `docs/qa/BUILD_TASK_READINESS_AND_DEPENDENCIES_MVP.md`
- `docs/qa/AUDIT_MATERIAL_PLANNING_AND_PROCUREMENT_READINESS.md`
