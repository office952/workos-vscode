# BUILD: Employee Mobile Shop-floor UX Simplification

**Branch:** `local/integration-pr4-plus-svg-path`  
**Scope:** Frontend-only UX simplification for shop-floor workers (Sandu / `employee_mobile`)  
**Backend:** unchanged  
**Date:** 2026-06-12

## 1. Audit findings (baseline)

- Mobile app functional but too dense for shop floor (11 pipeline tasks, 9 tabs, internal IDs, 10–13px text).
- Home + Tasks felt like a mini-ERP, not a work assistant.
- Pipeline was the default dominant experience; operators need **“Ce am de făcut acum”** first.
- Touch targets and typography below mobile best practice on secondary actions and tabs.

## 2. What was simplified

### Home (`EmployeeMobileHomeDashboard.tsx`)

- Replaced hero strip with **`EmployeeMobileShopFloorNowCard`**: greeting, current task, status, generic steps, single primary CTA.
- Nav cards (Azi, Comenzi, Montaje, Urmează, Blocaje) moved under collapsible **Mai multe**.
- Secondary links (Personal, Info) unchanged.

### Tasks (`EmployeeMobileTasksPanel.tsx`)

- Default view: **`Azi`** (`/employee-app/tasks`) instead of full pipeline.
- Primary tabs: **Azi · Ale mele · Tot fluxul** (+ **Mai multe** for secondary filters).
- **Azi** shows shop-floor now card + link **Vezi tot fluxul comenzii →**.
- **Tot fluxul** (`?view=pipeline`) shows simplified order flow list.

### Pipeline cards (`EmployeeMobileOrderPipelineView.tsx`)

- Compact mode (default): hides task IDs, stage labels, helper counts, multi-hint blocks on non-critical cards.
- Shows simplified status labels, one material hint when relevant, one CTA on current task.
- Full detail mode on blueprint page (`compactCards={false}`).

### Task detail

- Proces, Mașină, Estimare, Cod task collapsed under **Detalii tehnice** (`<details>`).
- Instructions, documents, actions, clarification unchanged.

### Language

| Before | After |
|--------|-------|
| Pipeline | Tot fluxul / Pașii mei (context) |
| Blueprint comandă | Tot fluxul comenzii |
| Readiness (implicit) | Status (simplified labels) |
| waiting_predecessor | Așteaptă task anterior |
| waiting_material | Așteaptă material |

## 3. Typography rules applied

| Element | Target |
|---------|--------|
| Primary task title | 20px (`text-xl`) |
| Task card title | 17–18px (`text-lg`) |
| Important body | 16px (`text-base`) |
| Secondary | 14px (`text-sm`) |
| Badges / markers | 13–14px (`text-sm`) |
| Microtext | Avoided; min 12px (`text-xs`) for non-critical only |

## 4. Touch target rules applied

| Control | Min height |
|---------|------------|
| Primary CTA | 48px |
| Secondary / tab | 44px |
| Action bar buttons | 48px, 16px label |
| Button spacing | 8–12px vertical gap |

## 5. Hidden or demoted on cards

- Task IDs (`T-006`, etc.) on pipeline cards (compact mode).
- `stage_label`, `process_id`, `machine_type`, `active_helper_count`, `can_assist`.
- Full dependency lists (single blocker line on current task only).
- Multiple material hints (max 1 discrete line).
- Full pipeline list on default Tasks tab.
- Home nav grid (under **Mai multe**).
- Secondary task filter tabs (under **Mai multe**).

## 6. Still in task detail

- Instructions, documents, start/complete/block/unblock, clarification.
- Product, started/completed timestamps, block reason.
- Technical fields under **Detalii tehnice** disclosure.

## 7. Still in full flow (`?view=pipeline` + blueprint page)

- Numbered order steps, all tasks (mine + others), markers (Acum / Urmează / Așteaptă).
- Material hints for waiting tasks, dependency warnings on current task.
- Blueprint page: summary chips, refresh, full card detail (`compactCards={false}`).

## 8. Unchanged

- Backend APIs, readiness/procurement/work sessions logic.
- Bottom nav: **Acasă / Taskuri / Personal**.
- No new endpoints, statuses, CostEngine, Inventory, or Pricing changes.
- No PWA/offline/voice/photo/assist flow changes.

## 9. Tests

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/lib/employeeMobileAccess.test.ts `
  src/lib/employeeMobileTaskSummary.test.ts `
  src/lib/employeeMobileTaskViews.test.ts `
  src/lib/employeeMobilePipelineEligibility.test.ts `
  src/pages/EmployeeMobileApp.test.tsx
```

**Result:** 88 tests passed (5 files).

Coverage highlights:

- Home shows **Ce am de făcut acum**.
- Default tasks = shop-floor card; full flow via tab/link/`?view=pipeline`.
- T-006 **Așteaptă task anterior** + discrete material hints.
- No commercial fields in pipeline UI.
- Bottom nav unchanged.

## 10. Smoke (Sandu)

**Prerequisites:** backend `:8000`, frontend `:3000`, `WORKOS_DEV_AUTH_USER_ID=dev-sandu-employee-001`.

**Routes:**

- `http://127.0.0.1:3000/employee-app`
- `http://127.0.0.1:3000/employee-app/tasks`

**Expected:** dominant now-card, large CTA, readable text, full flow secondary, bottom nav intact, no console errors.

## 11. Files changed

| File | Change |
|------|--------|
| `frontend/src/lib/employeeMobileShopFloorPresentation.ts` | **new** — status/steps/focus helpers |
| `frontend/src/components/workos/employee-mobile/EmployeeMobileShopFloorNowCard.tsx` | **new** — dominant now card |
| `frontend/src/lib/employeeMobileTaskViews.ts` | `today` default view, labels |
| `frontend/src/components/workos/employee-mobile/EmployeeMobileHomeDashboard.tsx` | shop-floor home |
| `frontend/src/components/workos/employee-mobile/EmployeeMobileTasksPanel.tsx` | tabs, today view, detail cleanup |
| `frontend/src/components/workos/employee-mobile/EmployeeMobileOrderPipelineView.tsx` | compact cards, typography |
| `frontend/src/components/workos/employee-mobile/EmployeeMobileOrderBlueprintPage.tsx` | language + full flow page |
| `frontend/src/components/workos/employee-mobile/EmployeeMobileTaskActionBar.tsx` | button sizing |
| `frontend/src/lib/employeeMobileTaskViews.test.ts` | default view paths |
| `frontend/src/pages/EmployeeMobileApp.test.tsx` | shop-floor + pipeline tests |

## 12. Deferred

- Full visual design refresh / design system pass.
- Structured instruction steps from backend (dynamic “Ce fac” list).
- Offline / PWA shop-floor mode.
- Voice / photo input on floor.
- Assist / helper flow UX.

## Boundary

Frontend-only. No commit/push without owner confirmation.

**Proposed commit message:** `feat(employee): simplify mobile shop-floor ux`
