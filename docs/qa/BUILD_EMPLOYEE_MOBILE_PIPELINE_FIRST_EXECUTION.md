# BUILD: Employee Mobile Pipeline-First Execution

**Date:** 2026-06-12  
**Status:** **PASS — uncommitted**  
**Branch:** `local/integration-pr4-plus-svg-path` @ `45c7fd4`  
**Prerequisite:** `45c7fd4 feat(employee): add mobile order blueprint`

---

## 1. Motiv

Employee Mobile avea două experiențe paralele: listă plată de taskuri (`/employee-app/tasks`) și blueprint separat (`/tasks/orders/:id/blueprint`). Owner decision: **pipeline / blueprint devine experiența principală**; taskul rămâne unitatea de lucru, dar UI-ul o afișează în contextul comenzii.

## 2. Task vs Pipeline

| Concept | Rol |
|---------|-----|
| **Task** | Unitate de lucru (start / block / complete) |
| **Pipeline** | Experiența principală de execuție |
| **Filtre** | Moduri de a vedea taskurile (Pipeline default, Ale mele, De făcut, …) |

## 3. Eligibilitate simplă (frontend)

- Task `in_progress` al angajatului → **Acum**
- Primul task al angajatului nefinalizat/neblocat → **Acum**
- Restul taskurilor alocate nefinalizate → **Urmează**
- Task blocat → **Blocat** (nu eligibil)
- Task finalizat → **Finalizat**
- Non-mine → **Alt post** / **Neatribuit** / **În lucru la alt post** (fără nume angajați)

## 4. Security boundary

- Fără modificări backend — payload `my-blueprint` existent suficient
- Fără nume alți angajați, cost, preț, marjă, payroll
- Acțiuni doar pe taskurile proprii

## 5. UI changes

| Area | Change |
|------|--------|
| `/employee-app/tasks` | Default **Pipeline** — card comandă activă + pipeline numerotat |
| Filtre | `Pipeline` (default), `Ale mele`, filtre existente păstrate |
| Scrollbar filtre | Ascuns vizual (scroll păstrat) |
| Blueprint page | Refolosește `EmployeeMobileOrderPipelineView` |
| Home nav „Taskurile mele azi” | Link la pipeline default |
| Bottom nav | Neschimbat |

## 6. Componentă shared

`EmployeeMobileOrderPipelineView` — folosită în Tasks panel și Blueprint page.

Eligibilitate: `frontend/src/lib/employeeMobilePipelineEligibility.ts`

## 7. Acțiuni pipeline

- Task **Acum** + status `assigned` → `Încep task` inline (EmployeeMobileTaskActionBar)
- Task **Acum** + `in_progress` / `blocked` → **Deschide task** (detail cu Blochez/Finalizez)
- Task **Urmează** → **Vezi detalii**

## 8. Tests

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/employeeMobileAccess.test.ts src/lib/employeeMobileTaskSummary.test.ts src/lib/employeeMobileTaskViews.test.ts src/lib/employeeMobilePipelineEligibility.test.ts src/pages/EmployeeMobileApp.test.tsx
```

Backend: **unchanged** — no pytest required.

## 9. Smoke Sandu

Backend: `WORKOS_DEV_AUTH_USER_ID='dev-sandu-employee-001'`

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/auth/me
Invoke-RestMethod http://127.0.0.1:8000/api/v1/employee-mobile/orders/1/my-blueprint
Invoke-RestMethod http://127.0.0.1:8000/api/v1/employee-mobile/tasks
```

Browser: `/employee-app/tasks` (pipeline), `/employee-app/tasks/orders/1/blueprint`

## 10. Deferred

- Dependency engine real între taskuri
- Per-station eligibility
- Websocket / push notifications
- Task sequencing admin editor
- Payroll / bani
- Full mobile admin blueprint
- Gantt / drag-and-drop

## Files changed

- `frontend/src/lib/employeeMobilePipelineEligibility.ts` (new)
- `frontend/src/lib/employeeMobilePipelineEligibility.test.ts` (new)
- `frontend/src/lib/employeeMobileTaskViews.ts`
- `frontend/src/lib/employeeMobileTaskViews.test.ts`
- `frontend/src/components/workos/employee-mobile/EmployeeMobileOrderPipelineView.tsx` (new)
- `frontend/src/components/workos/employee-mobile/EmployeeMobileOrderBlueprintPage.tsx`
- `frontend/src/components/workos/employee-mobile/EmployeeMobileTasksPanel.tsx`
- `frontend/src/components/workos/employee-mobile/EmployeeMobileHomeDashboard.tsx`
- `frontend/src/pages/EmployeeMobileApp.test.tsx`
- `docs/qa/BUILD_EMPLOYEE_MOBILE_PIPELINE_FIRST_EXECUTION.md`

## Proposed commit message

```
feat(employee): make mobile tasks pipeline-first
```
