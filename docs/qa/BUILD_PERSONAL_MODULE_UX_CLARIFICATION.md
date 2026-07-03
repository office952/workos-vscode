# BUILD — Personal Module UX Clarification

## Problem

Commit `a21ea274` aligned Personal/HR navigation text in code, but UI changes were too subtle (small gray subtitles, minor diacritics). Operators could not distinguish:

- live operational registry vs HR demo pages;
- internal evidence vs fiscal payroll.

## Solution (UX only)

Visible badges (`Badge` from `@/components/ui/badge`) and boundary alerts (`Alert` from `@/components/ui/alert`) on each Personal submodule page:

| Page | Badges | Alert |
|------|--------|-------|
| `/employees` | LIVE DB, OPERAȚIONAL | — |
| `/employees-records` | DEMO, HR INTERN | demo / not linked to operational registry |
| `/attendance` | DEMO, EVIDENȚĂ INTERNĂ | no automatic fiscal payroll |
| `/employee-payments` | DEMO, FĂRĂ PAYROLL FISCAL | not fiscal payslip / no accounting obligations |
| `/employee-advances` | DEMO, MANUAL | manual compensation with payments/attendance |

Subtitle text on `/employees` updated to governance wording.

## Route `/personal`

**Decision:** redirect `/personal` → `/employees` (same pattern as `/products` → `/product-system`).

Orphan `Personal.tsx` remains in repo but is no longer routed. Sidebar already lists the five submodule routes.

## Files changed

- `frontend/src/pages/Employees.tsx`
- `frontend/src/pages/EmployeesRecords.tsx`
- `frontend/src/pages/Attendance.tsx`
- `frontend/src/pages/EmployeePayments.tsx`
- `frontend/src/pages/EmployeeAdvances.tsx`
- `frontend/src/App.tsx` (redirect)
- `frontend/src/pages/workforceRoutes.test.tsx`

## Tests

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/personalNavigation.test.ts src/pages/workforceRoutes.test.tsx
npx --yes pnpm@8.10.0 exec tsc -b --noEmit
```

Coverage:

- LIVE DB + OPERAȚIONAL on `/employees`
- DEMO + HR INTERN on `/employees-records`
- DEMO + EVIDENȚĂ INTERNĂ on `/attendance`
- FĂRĂ PAYROLL FISCAL on `/employee-payments`
- MANUAL on `/employee-advances`
- `/personal` redirect to `/employees`

## Runtime smoke

Manual on `http://127.0.0.1:3000`:

- `/employees` — green LIVE DB, cyan OPERAȚIONAL
- `/employees-records` — amber DEMO, purple HR INTERN + alert
- `/attendance` — DEMO + EVIDENȚĂ INTERNĂ + alert
- `/employee-payments` — DEMO + red FĂRĂ PAYROLL FISCAL + alert
- `/employee-advances` — DEMO + MANUAL + alert
- `/personal` — lands on `/employees`

## Boundaries

- No backend, DB, or schema changes
- No CostEngine, Quote/VAT, SmartBill, Inventory
- No fiscal payroll implementation
- Sidebar structure unchanged (five Personal items)

## Risks / next

- `Personal.tsx` still exists — consider removal or dev-only route later
- Demo HR pages still use `employeeRecordsData.ts` mock
- Linking HR demo to operational `employees.id` remains a future backend build
