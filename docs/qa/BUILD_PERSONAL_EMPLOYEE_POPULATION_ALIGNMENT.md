# BUILD — Personal Employee Population Alignment

## Problem

Personal submodule pages showed **different employee populations**:

- `/employees` — 8 live backend employees (Andrei Goghi, Calin Cimpean, …)
- HR / Pontaj / Plăți / Avansuri — static demo roster (Ion Popescu, Mihai Ionescu, …)

Operators could not link HR demo data to operational registry employees.

## Decision

**Employee population** for all Personal pages comes from the same source as `/employees`:

- API: `employeesApi.list()` → `/api/v1/entities/employees`
- Hook: `useOperationalEmployees` / `usePersonalDemoModule`

**Module-specific data** (documents, pontaj, payments, advances) remains **demo/placeholder**, generated deterministically per live `employee.id`.

UI text: *Datele modulului sunt demonstrative, dar lista de angajați vine din registry-ul operațional live.*

## What changed

- Removed static `DEMO_EMPLOYEES`, `DEMO_DOCUMENTS`, `DEMO_ADVANCES` person lists from `employeeRecordsData.ts`
- Added `operationalEmployeeRecords.ts` — map `EmployeeDTO` → `EmployeeRecord` + demo generators
- Added `useOperationalEmployees`, `usePersonalDemoModule` hooks
- Updated `EmployeesRecords`, `Attendance`, `EmployeePayments`, `EmployeeAdvances`, `EmployeeProfile`
- Extended `workforceRoutes.test.tsx` — live names, no legacy demo names

## What did NOT change

- No backend tables, routers, or migrations
- No fiscal payroll calculation
- No CostEngine, Quote/VAT, SmartBill, Inventory changes
- No DB writes from HR demo pages

## Tests

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/workforceRoutes.test.tsx
npx --yes pnpm@8.10.0 exec tsc -b --noEmit
```

- HR / Attendance / Payments / Advances render `Andrei Goghi` from mocked live API
- Legacy names (`Ion Popescu`, etc.) absent

## Runtime smoke

Compare employee names across:

- `/employees`
- `/employees-records`
- `/attendance`
- `/employee-payments`
- `/employee-advances`

All should list the same operational employees; demo badges/alerts remain.

## Boundaries

- Backend/DB/schema: untouched
- Fiscal payroll: out of scope
- Operational registry CRUD: unchanged (still on `/employees`)

## Risks / next

- Demo metadata keyed by index — stable per employee id but not persisted
- Future HR backend should use same `employees.id` foreign keys
- Empty employee list shows empty HR modules (correct fail-closed UX)
