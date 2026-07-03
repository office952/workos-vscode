# BUILD — Personal / HR Module Alignment

## Purpose

Align sidebar PERSONAL group roles, naming, and page descriptions without building fiscal payroll or touching off-scope modules.

## Sidebar items (intended roles)

| Item | Route | Role |
|------|-------|------|
| Angajați operaționali | `/employees` | Production/operations registry, authorizations, CostEngine labour inputs |
| Evidență internă HR | `/employees-records` | Internal HR files, documents, alerts (demo data) |
| Pontaj | `/attendance` | Internal attendance / hours (demo data) |
| Plăți angajați | `/employee-payments` | Internal payment runs (demo calculations, not fiscal payroll) |
| Avansuri / Datorii | `/employee-advances` | Advances, loans, retentions (demo data) |

Legacy route `/personal` exists but is **not** in sidebar — mixed mock/API team view.

## What changed (this build)

- Sidebar label: `Plati angajati` → `Plăți angajați`
- Page subtitles aligned to governance text (registry vs HR vs internal evidence)
- `Pontaj` title (was `Pontaj intern`)
- Removed misleading “scad automat din tranșă” on advances (no auto fiscal payroll)
- Test: `personalNavigation` Plăți link

## What did NOT change

- No new backend tables or migrations
- No payroll fiscal formulas
- No SmartBill, CostEngine formulas, Quote/VAT, Inventory, Production execution logic
- HR demo pages still use `employeeRecordsData.ts` mock — no API wiring
- Operational employees still use `/api/v1/entities/employees` + operational registry

## Backend inventory (audit)

| Area | Status |
|------|--------|
| `employees` table + router | Live CRUD, CostEngine labour cost source |
| `operational_registry` (skills, authorizations) | Live, linked from Employees UI |
| Attendance / payments / advances | **No** dedicated backend tables/API in this audit |
| `execution_reality_workforce` | Production capture, not HR payroll |

## Tests

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/personalNavigation.test.ts src/pages/workforceRoutes.test.tsx
npx --yes pnpm@8.10.0 exec tsc -b --noEmit

cd backend
.\.venv\Scripts\python.exe -m pytest tests -k "employee or workforce or attendance or payment or advance or debt or hr" -q
```

## Risks / next builds

- Link HR demo employees to operational `employees.id` when backend HR module exists
- Replace `employeeRecordsData` with API incrementally (pontaj → plăți → avansuri)
- Remove or redirect orphan `/personal` route to reduce confusion
- Do not promise automatic payroll deduction until explicit workflow exists

## Boundaries

- Fiscal payroll, tax/contribution calculation: **out of scope**
- Official accounting export: **out of scope**
