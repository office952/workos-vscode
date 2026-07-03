# WorkOS/ProdFlow — Atoms UI Expansion Overview

**Generated**: 2026-06-03  
**Scope**: All modules created/modified in the Atoms platform  
**Verdict**: PARTIAL_READY

---

## Module Registry

### Core Commercial Flow (LIVE / DB-FIRST)

| Module | Route | Status | Data Source |
|--------|-------|--------|-------------|
| Dashboard | `/dashboard` | LIVE | `useBackendData()` → DB entities |
| Work Intake | `/intake` | DB-FIRST | `useBackendData()` → `/api/v1/entities/intake_requests` |
| Intake Detail | `/intake/:id` | DB-FIRST | `useBackendData()` → filtered by ID |
| Quotes | `/quotes` | DB-FIRST | `useBackendData()` → `/api/v1/entities/quotes` |
| Orders | `/orders` | DB-FIRST | `useBackendData()` → `/api/v1/entities/orders` |
| Execution Dashboard | `/execution` | LIVE | `executionApi` → `/api/v1/execution/dashboard` |
| Execution Detail | `/execution/:order_id` | LIVE | `executionApi` → `/api/v1/execution/plan/{id}`, `/reality/{id}` |
| Inventory | `/inventory` | DB-FIRST | `useBackendData()` → `/api/v1/entities/inventory_materials` |

### Pricing Module (LIVE)

| Module | Route | Status | Data Source |
|--------|-------|--------|-------------|
| Pricing V2 Dashboard | `/inventory/pricing` | LIVE | `inventoryMaterialsAdmin` + `commercialMarkupPoliciesAdmin` |
| Material Price Registry | (embedded in Pricing) | LIVE | `/api/admin/inventory-materials` |
| Commercial Markup Policies | (embedded in Pricing) | LIVE | `/api/admin/commercial-markup-policies/*` |
| ProductSystem Pricing Preview | (embedded in Pricing) | LIVE | `/api/admin/productsystem-pricing-preview` |

### Product System (LIVE)

| Module | Route | Status | Data Source |
|--------|-------|--------|-------------|
| Product System | `/product-system` | LIVE | `productFamilies` → `/api/v1/entities/product-families` |
| Blueprint Dossier Studio | `/product-system/blueprint-dossier` | LIVE | `blueprintDossierApi` → entity CRUD |
| Dossier Completion | `/product-system/dossier-completion` | LIVE | `blueprintDossierApi` |
| Output Blocks Preview | `/product-system/output-blocks-preview` | LIVE | `outputBlocksPreview*` APIs |

### Client Module (PARTIAL)

| Module | Route | Status | Data Source |
|--------|-------|--------|-------------|
| Clients List | `/clients` | PARTIAL | Derived from `useBackendData()` (intakes/quotes/orders) — backend `/api/v1/entities/clients` exists but unused |
| Client Workspace | `/clients/:clientName` | PARTIAL | Filters `useBackendData()` by client name |

### Document Center (DEMO)

| Module | Route | Status | Data Source |
|--------|-------|--------|-------------|
| Document Center | `/documents` | DEMO | Hardcoded `mockDocuments` array in component |

### Operator / Tablet Mode (DEMO with backend available)

| Module | Route | Status | Data Source |
|--------|-------|--------|-------------|
| Tablet Station Selector | `/tablet` | DEMO | `workstationRouting.ts` static config |
| Tablet Station Queue | `/tablet/:stationId` | DEMO | `generateDemoTasks()` — backend `/api/v1/operator/tasks` exists |
| Tablet Task Detail | `/tablet/:stationId/:taskId` | DEMO | `generateDemoTasks()` — backend `/api/v1/operator/task-action` exists |
| Operator View | `/operator` | PARTIAL | Mixed sources |
| Shop Floor | `/shop-floor` | PARTIAL | Mixed sources |

### Personal / HR Module (PARTIAL + DEMO)

| Module | Route | Status | Data Source |
|--------|-------|--------|-------------|
| Personal (overview) | `/personal` | PARTIAL | Navigation hub |
| Employees List | `/employees` | DB-FIRST | `usePersonalData()` → `/api/v1/entities/employees` |
| Employees Records | `/employees-records` | DEMO | `employeeRecordsData.ts` static generators |
| Employee Profile | `/employees-records/:employeeId` | DEMO | `employeeRecordsData.ts` |
| Attendance | `/attendance` | DEMO | `generateMonthlyAttendance()` |
| Employee Payments | `/employee-payments` | DEMO | `generatePaymentRuns()` |
| Employee Advances | `/employee-advances` | DEMO | Static `ADVANCES` array |

### Other Modules

| Module | Route | Status | Data Source |
|--------|-------|--------|-------------|
| Colaboratori | `/colaboratori` | DEMO | Static data |
| Utilaje | `/utilaje` | DEMO | Static data |
| Reports | `/reports` | DEMO | Static/placeholder |
| Module Chain | `/modules` | LIVE | Static navigation |
| Governance | `/governance` | DEMO | Static data |
| Settings | `/settings` | LIVE | `settingsApi` → backend |

---

## Status Legend

| Status | Meaning |
|--------|---------|
| **LIVE** | Connected to real backend API, reads/writes real data |
| **DB-FIRST** | Uses `useBackendData()` hook with DB-first strategy; returns real data when backend available, empty when not |
| **PARTIAL** | Some data is real, some derived/mock; backend endpoint exists but not fully utilized |
| **DEMO** | Frontend-only with hardcoded/generated mock data; no backend persistence |
| **COMING SOON** | Module planned but not yet implemented |

---

## Coming Soon (Not Yet Built)

| Module | Description | Backend Needed |
|--------|-------------|---------------|
| Puncte / Bonusuri / Comisioane | Reward points, commissions, team bonuses | New entity + service |
| Facturi (Invoices) | Invoice generation and tracking | New entity + SmartBill integration |
| Contracte (Contracts) | Contract management | New entity + document generation |
| Rapoarte avansate | Advanced reporting/analytics | Aggregation endpoints |

---

## File Structure

```
src/pages/
├── Pricing.tsx                    # LIVE — Prices V2 dashboard
├── Clients.tsx                    # PARTIAL — Client list
├── ClientWorkspace.tsx            # PARTIAL — Client detail tabs
├── DocumentCenter.tsx             # DEMO — Document management
├── TabletMode.tsx                 # DEMO — Operator tablet
├── Employees.tsx                  # DB-FIRST — Employee list
├── EmployeesRecords.tsx           # DEMO — Employee records
├── EmployeeProfile.tsx            # DEMO — Employee detail
├── Attendance.tsx                 # DEMO — Monthly timesheet
├── EmployeePayments.tsx           # DEMO — Payment runs
├── EmployeeAdvances.tsx           # DEMO — Advances/debts
├── ExecutionDashboard.tsx         # LIVE — Execution overview
├── ExecutionDetail.tsx            # LIVE — Execution detail
├── ProductSystem.tsx              # LIVE — Product families
└── ...
```