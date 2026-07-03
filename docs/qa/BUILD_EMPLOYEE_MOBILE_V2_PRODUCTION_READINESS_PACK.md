# BUILD: Employee Mobile v2 Production Readiness Pack

**Branch:** `local/integration-pr4-plus-svg-path`  
**HEAD before:** `4133a32 fix(employee): clarify in-progress task context on mobile v2`  
**Scope:** Frontend-only UX/ergonomics pass for `/employee-app-v2` — no promotion, no PWA, no backend  
**Date:** 2026-06-15  
**Status:** Complete (pending commit + physical phone test)

## 1. Purpose

Prepare Employee Mobile v2 for real-phone testing and a future promotion decision without changing default routes or PWA `start_url`. Focus: phone ergonomics, cross-screen consistency, operator microcopy, and test/QA coverage.

## 2. Boundary

| Area | Touched |
|------|---------|
| `/employee-app-v2/*` components & v2 helpers | Yes |
| `/employee-app` v1 | No |
| Backend / migrations / API / DTOs | No |
| PWA manifest / `start_url` | No |
| Mock data / HR payroll / interactive attendance / chat / upload | No |

Shared `EmployeeMobileRequestsPanel` copy updated to operator-friendly text (also improves v2 Personal/Cereri skin).

## 3. What changed

### Phone ergonomics

- Segmented tab touch targets raised to **44px** (`employeeMobileV2DesignTokens`, `EmployeeMobileV2SegmentedTabs`).
- Shell bottom scroll padding increased (`5rem` + safe area) to reduce bottom-nav overlap.
- Task detail uses v2-specific scroll pad (`emV2TaskDetailScrollPad`) for sticky action clearance.
- Pipeline timeline row density slightly reduced (`py-2.5`).
- Blockers cancel button full-width 44px tap target.

### Taskuri v2

- Single-task groups use tighter spacing (`EmployeeMobileV2TaskGroup`).
- Waiting detail deduplication on rows (`suppressDuplicateWaitingDetail` in `employeeMobileV2TaskGrouping` + `EmployeeMobileV2TaskRow`).

### Detaliu task

- Sticky action bar clearance via v2 scroll pad token (no logic/API change).

### Pipeline v2

- Timeline density tweak only; specific waiting reasons from prior build retained.

### Documente v2

- Full-row tappable document links when URL exists (`EmployeeMobileV2DocumentsPage`).

### Blocaje / Urmează / Personal

- Blockers: cancel affordance ergonomics.
- Urmează: no duplicate waiting text in status column.
- Personal: hide `Self-only` dev badge in v2 panel shell; Cereri copy remains operator-friendly.

### Microcopy

- No new dev-facing strings introduced.
- `Self-only` badge hidden in v2 Personal requests skin.

## 4. Files changed

- `frontend/src/lib/employeeMobileV2DesignTokens.ts`
- `frontend/src/lib/employeeMobileV2TaskGrouping.ts`
- `frontend/src/lib/employeeMobileV2TaskGrouping.test.ts`
- `frontend/src/components/workos/employee-mobile-v2/EmployeeMobileV2Shell.tsx`
- `frontend/src/components/workos/employee-mobile-v2/EmployeeMobileV2TaskRow.tsx`
- `frontend/src/components/workos/employee-mobile-v2/EmployeeMobileV2TaskGroup.tsx`
- `frontend/src/components/workos/employee-mobile-v2/EmployeeMobileV2TaskDetailPage.tsx`
- `frontend/src/components/workos/employee-mobile-v2/EmployeeMobileV2DocumentsPage.tsx`
- `frontend/src/components/workos/employee-mobile-v2/EmployeeMobileV2BlockersPage.tsx`
- `frontend/src/components/workos/employee-mobile-v2/EmployeeMobileV2PersonalPanelShell.tsx`
- `frontend/src/pages/EmployeeMobileV2App.test.tsx`

## 5. Screens verified (visual smoke)

Viewport: **375×667** (primary), **390×844**, **430×932**

| Screen | Result |
|--------|--------|
| Home v2 | PASS |
| Taskuri — Operație / Comandă / Prioritate | PASS |
| Detaliu T-004 | PASS |
| Pipeline | PASS |
| Documente | PASS |
| Blocaje | PASS |
| Urmează | PASS |
| Personal / Cereri / Pontaj | PASS |
| v1 `/employee-app` + `/employee-app/tasks` | PASS (unchanged) |

Checks: no `În lucru` + `Așteaptă:` contradiction; no slug-uri; no dev `employee_id` text; bottom nav OK; scope tabs ≥44px.

## 6. Tests

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run `
  src/pages/EmployeeMobileApp.test.tsx `
  src/pages/EmployeeMobileV2App.test.tsx `
  src/lib/employeeMobileV2Labels.test.ts `
  src/lib/employeeMobileV2Status.test.ts `
  src/lib/employeeMobileV2TaskGrouping.test.ts
```

**Result:** 91/91 PASS

`validate:frontend` not declared green (pre-existing TS debt).

## 7. Remaining for physical phone test

- Thumb reach on real device with gloves / shop lighting.
- Safe-area on notched iPhone / gesture bar Android.
- Document open in external viewer from PWA/browser.
- Blocker form one-handed input.
- Promotion decision (PWA `start_url`) — **out of scope; not done**.

## 8. Promotion status

**v2 NOT promoted.** `/employee-app` remains default and PWA `start_url` unchanged.

## 9. Proposed commit message

```text
fix(employee): prepare mobile v2 for production phone testing
```
