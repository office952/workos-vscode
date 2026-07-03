# WorkOS/ProdFlow — Data Model Readiness Audit

**Generated**: 2026-06-03  
**Verdict Global**: `PARTIAL_READY`  
**Scor Readiness**: **78%**

---

## Verdict Summary

The core commercial flow (Intake → Quote → Order → Execution) is fully wired to backend APIs with proper type safety and error handling. Supporting modules (HR, Documents, Tablet tasks) have UI implementations but lack backend entities and persistence.

---

## Module Verdicts

### ✅ FULLY WIRED — Backend API Active

| Module | API Client | Backend Endpoint | Verdict |
|--------|-----------|-----------------|---------|
| Pricing (Materials) | `src/api/inventoryMaterialsAdmin.ts` | `GET /api/admin/inventory-materials` | ✅ OPERATIONAL |
| Pricing (Markup) | `src/api/commercialMarkupPoliciesAdmin.ts` | `GET/POST /api/admin/commercial-markup-policies/*` | ✅ OPERATIONAL |
| Pricing (Dry-Run) | `src/api/commercialMarkupPoliciesAdmin.ts` | `POST /api/admin/commercial-markup-policies/dry-run` | ✅ OPERATIONAL |
| Pricing (Preview) | `src/api/productSystemPricingPreviewAdmin.ts` | `POST /api/admin/productsystem-pricing-preview` | ✅ OPERATIONAL |
| Execution Dashboard | `src/api/execution.ts` | `GET /api/v1/execution/dashboard` | ✅ OPERATIONAL |
| Execution Detail | `src/api/execution.ts` | `GET /api/v1/execution/plan/{id}`, `/reality/{id}`, `/divergence/{id}` | ✅ OPERATIONAL |
| Execution Plan Gate | `src/api/execution.ts` | `GET /api/v1/execution/plan/gate/{order_id}` | ✅ OPERATIONAL |
| Execution Plan Create | `src/api/execution.ts` | `POST /api/v1/execution/plan/from-order/{order_id}` | ✅ OPERATIONAL |
| Product Families | `src/api/productFamilies.ts` | `GET /api/v1/entities/product-families` | ✅ OPERATIONAL |
| Blueprint Dossier | `src/api/blueprintDossier.ts` | Entity CRUD via SDK | ✅ OPERATIONAL |
| Product Readiness | `src/api/productReadiness.ts` | Backend validation endpoint | ✅ OPERATIONAL |
| Output Blocks | `src/api/outputBlocksPreview*.ts` | Backend rendering | ✅ OPERATIONAL |
| Quote PDF | `src/api/quotePdf.ts` | Backend PDF generation | ✅ OPERATIONAL |
| Cost Engine | `src/api/costEngine.ts` | `/api/v1/cost-engine/*` | ✅ OPERATIONAL |
| Cost Simulation | `src/api/costSimulation.ts` | Backend simulation | ✅ OPERATIONAL |
| Settings | `src/api/settings.ts` | Backend settings CRUD | ✅ OPERATIONAL |
| Integrations | `src/api/integrations.ts` | Backend integration management | ✅ OPERATIONAL |

### ⚠️ PARTIALLY WIRED — DB-First with Mock Fallback

| Module | Data Source | Backend Endpoint | Gap |
|--------|------------|-----------------|-----|
| Work Intake | `useBackendData()` → `dataStore.ts` | `GET /api/v1/entities/intake_requests` | Wired via generic entity client; write actions limited |
| Quotes | `useBackendData()` → `dataStore.ts` | `GET /api/v1/entities/quotes` | Wired via generic entity client; quote creation flow partial |
| Orders | `useBackendData()` → `dataStore.ts` | `GET /api/v1/entities/orders` | Wired via generic entity client; order locking via execution |
| Inventory Materials | `useBackendData()` → `dataStore.ts` | `GET /api/v1/entities/inventory_materials` | Wired; admin actions via separate admin API |
| Suppliers | `useBackendData()` → `dataStore.ts` | `GET /api/v1/entities/suppliers` | Wired via generic entity client |
| Employees | `usePersonalData()` | `GET /api/v1/entities/employees` | List is wired; sub-features are not |
| Clients List | `useBackendData()` (derived) | `GET /api/v1/entities/clients` | Backend exists but frontend derives from other entities |
| Client Workspace | `useBackendData()` (filtered) | All entity endpoints | Works but no dedicated client API call |

### 🔴 NOT WIRED — Frontend-Only Demo Data

| Module | Data Source | Backend Support | What's Missing |
|--------|------------|----------------|----------------|
| Document Center | Hardcoded `mockDocuments` in component | ❌ No entity/router | `documents` entity, router, service, seed data |
| Tablet Mode (Tasks) | `generateDemoTasks()` in component | ✅ `/api/v1/operator/tasks` EXISTS | Frontend wiring to existing API |
| Tablet Mode (Actions) | Demo buttons | ✅ `POST /api/v1/operator/task-action` EXISTS | Frontend wiring to existing API |
| Attendance | `employeeRecordsData.ts` → `generateMonthlyAttendance()` | ❌ No entity | `employee_attendance` entity, router, service |
| Employee Payments | `employeeRecordsData.ts` → `generatePaymentRuns()` | ❌ No entity | `employee_internal_payments` entity, router, service |
| Employee Advances | `employeeRecordsData.ts` → static array | ❌ No entity | `employee_advances_debts` entity, router, service |
| Employee Profile/Docs | `employeeRecordsData.ts` → static arrays | ❌ No entity | `employee_documents` entity, router, service |
| Puncte/Bonusuri | Not implemented | ❌ No entity | Full module: entity, router, service, UI |

---

## Architecture Quality Scores

| Dimension | Score | Notes |
|-----------|-------|-------|
| API Client Architecture | 9/10 | Clean, typed, consistent pattern across all clients |
| Backend Coverage | 7/10 | Core flow covered; HR/Docs/Rewards missing |
| Data Flow Correctness | 8/10 | DB-first strategy well-implemented with proper fallback |
| Mock Isolation | 10/10 | Flag-gated via `VITE_ENABLE_MOCK_DATA`; production never sees demo data |
| Auth Integration | 8/10 | WorkOS OIDC with dev bypass; clean separation |
| Type Safety | 9/10 | Full DTO types with proper mappers in dataStore |
| Error Handling | 7/10 | Graceful degradation; some silent failures in entity client |
| Config Management | 9/10 | Centralized `getAPIBaseURL()` with same-origin strategy |

---

## Key Findings

1. **Config & Connectivity** ✅ — `getAPIBaseURL()` returns `""` (same-origin); Vite proxy forwards `/api` → `localhost:8000`
2. **Mock Data Guard** ✅ — `VITE_ENABLE_MOCK_DATA` flag absent from `.env` → mock disabled by default
3. **Client Workspace Gap** ⚠️ — Backend has full `clients` entity but frontend derives from other entities
4. **Tablet Mode Gap** ⚠️ — Backend has full operator tasks API but frontend uses static demo tasks
5. **Document Center** ❌ — No backend entity exists; entirely hardcoded
6. **Personal Sub-features** ❌ — Employee list is wired but attendance/payments/advances are static generators