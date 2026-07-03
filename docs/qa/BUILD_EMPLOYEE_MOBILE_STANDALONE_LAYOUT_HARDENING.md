# BUILD: Employee Mobile Standalone Layout Hardening

## Meta

| Field | Value |
|-------|--------|
| **Branch** | `local/integration-pr4-plus-svg-path` |
| **HEAD before** | `45128cb` — `feat(employee): add manager team workspace` |
| **Status** | PASS |

## Problem observed

`/employee-app` (și sub-rute) era randat **în interiorul** `AppShell` din `App.tsx`, cu sidebar desktop și topbar (search, alerte). Employee Mobile apărea ca pagină ERP, nu ca experiență PWA self-contained.

## Routing/layout audit

| Item | Finding |
|------|---------|
| Router principal | `App.tsx` → `AuthGate` → `AppShell` |
| Desktop shell | `AppShell` — sidebar + topbar + `<main><Routes>` |
| Employee routes (before) | `/employee-app/*` ca rută copil în `AppShell` |
| Safest fix | Split top-level: `/employee-app/*` → standalone root; `*` → `AppShell` |

## Implementation summary

- `AuthenticatedAppRoutes` — `RuntimeProtectedOutlet` → employee standalone OR desktop shell
- `EmployeeMobileStandaloneRoot` — full-viewport wrapper fără sidebar/topbar
- `AppShell` — eliminat `/employee-app/*`; `data-testid` pe shell/sidebar/topbar
- `EmployeeMobileApp` layout — `min-h-[100dvh]`, padding responsive

## Routes standalone confirmed

- `/employee-app`
- `/employee-app/requests`
- `/employee-app/attendance`
- `/employee-app/review`
- `/employee-app/team`

## Desktop routes unaffected

- `/dashboard`, `/attendance/effects`, etc. — `AppShell` neschimbat ca structură

## PWA manifest status

| Field | Value |
|-------|--------|
| `start_url` | `/employee-app` ✓ |
| `display` | `standalone` ✓ |
| manifest link | `index.html` ✓ |
| Apple web-app meta | present ✓ |
| Service worker | not added (deferred) |

## Tests added/updated

- `frontend/src/App.test.tsx` — 7 tests (layout isolation + desktop shell)
- `frontend/src/pages/EmployeeMobileApp.test.tsx` — +1 standalone marker test

## Tests run + results

```text
App.test.tsx + EmployeeMobileApp + EmployeeManagerTeamWorkspace + EmployeeAttendanceEffects → 48 passed
Backend employee regression (5 files) → 150 passed
```

## Manual smoke

Not run — dev stack not started in this session (visual fix validated via routing tests).

## Files changed

- `frontend/src/App.tsx`
- `frontend/src/App.test.tsx`
- `frontend/src/pages/EmployeeMobileApp.tsx`
- `frontend/src/pages/EmployeeMobileApp.test.tsx`
- `docs/architecture/EMPLOYEE_MOBILE_STANDALONE_LAYOUT_DECISION.md`

## Confirmations

- [x] `/employee-app/*` no desktop sidebar
- [x] `/employee-app/*` no desktop topbar
- [x] Employee Mobile bottom nav preserved
- [x] PWA start_url `/employee-app`
- [x] Desktop WorkOS shell unaffected
- [x] `/attendance/effects` remains desktop/admin
- [x] No backend business logic changes
- [x] No DB/migration
- [x] No payroll/payment/cost
- [x] No auth rewrite
- [x] No permission relaxation
- [x] No push/offline/native app
