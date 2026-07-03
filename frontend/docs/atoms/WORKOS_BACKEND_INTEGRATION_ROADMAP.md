# WorkOS/ProdFlow — Backend Integration Roadmap

**Generated**: 2026-06-03  
**Context**: Priority order for VS Code/backend implementation

---

## Priority P1 — Low Effort, High Impact (Frontend wiring only)

### 1. Client Workspace → Direct Client API

**Current state**: Frontend derives client list from intakes/quotes/orders via `useBackendData()`  
**Backend available**: `GET /api/v1/entities/clients` (full CRUD router exists)

**Work needed**:
- Create `src/api/clientsAdmin.ts` API client
- Wire `Clients.tsx` to `GET /api/v1/entities/clients` instead of deriving
- Wire `ClientWorkspace.tsx` to `GET /api/v1/entities/clients/{id}` for detail
- Maintain cross-links to intakes/quotes/orders via `client_id` FK

**Endpoints to use**:
```
GET    /api/v1/entities/clients          → list all clients
GET    /api/v1/entities/clients/all      → list all (no pagination)
GET    /api/v1/entities/clients/{id}     → single client detail
POST   /api/v1/entities/clients          → create client
PUT    /api/v1/entities/clients/{id}     → update client
DELETE /api/v1/entities/clients/{id}     → delete client
```

**Effort**: ~2-4 hours frontend only

---

### 2. Tablet Mode → Operator Tasks API

**Current state**: Frontend uses `generateDemoTasks()` static function  
**Backend available**: `GET /api/v1/operator/tasks` + `POST /api/v1/operator/task-action`

**Work needed**:
- Create `src/api/operatorTasks.ts` API client
- Wire `/tablet/:stationId` to `GET /api/v1/operator/tasks` filtered by station
- Wire task actions (start/pause/complete/block/resume/unblock) to `POST /api/v1/operator/task-action`
- Keep `workstationRouting.ts` as frontend routing config (valid)
- Demo tasks become fallback only when API returns empty

**Endpoints to use**:
```
GET    /api/v1/operator/tasks                → all tasks from execution plans
POST   /api/v1/operator/task-action          → start/pause/complete/block/resume/unblock
```

**Task Action Request**:
```json
{
  "order_id": 123,
  "task_id": "task-uuid",
  "action": "start|pause|complete|block|resume|unblock",
  "operator_name": "optional",
  "reason": "optional (for block)"
}
```

**Effort**: ~3-5 hours frontend only

---

### 3. Prices V2 — Active Actions

**Current state**: Read operations are live; edit cost/markup buttons are disabled  
**Backend available**: `PATCH /api/admin/inventory-materials/{code}` exists

**Work needed**:
- Wire "Edit cost" button to `PATCH /api/admin/inventory-materials/{code}`
- Wire "History" to `GET /api/admin/inventory-materials/{code}/price-history`
- Verify markup edit endpoint availability
- Keep "Edit markup" disabled if no dedicated endpoint exists

**Endpoints to use**:
```
PATCH  /api/admin/inventory-materials/{code}                → update material cost
GET    /api/admin/inventory-materials/{code}/price-history  → price change history
```

**Effort**: ~2-3 hours frontend only

---

## Priority P2 — Medium Effort (Backend entity creation needed)

### 4. Document Center Backend

**Current state**: Hardcoded `mockDocuments` array  
**Backend needed**: New entity + router + service

**Entity**: `documents`  
**Fields**: See `DOCUMENT_CENTER_BACKEND_READINESS.md`

**Endpoints to create**:
```
GET    /api/v1/entities/documents          → list with filters
GET    /api/v1/entities/documents/{id}     → single document
POST   /api/v1/entities/documents          → create/generate
PUT    /api/v1/entities/documents/{id}     → update status/metadata
DELETE /api/v1/entities/documents/{id}     → archive/delete
POST   /api/v1/documents/generate          → generate from template
POST   /api/v1/documents/{id}/send         → mark as sent
POST   /api/v1/documents/{id}/sign         → mark as signed
```

**Effort**: ~1-2 days backend + frontend wiring

---

### 5. Attendance Tracking

**Current state**: `generateMonthlyAttendance()` static generator  
**Backend needed**: New entity + router + service

**Entity**: `employee_attendance`  
**Fields**: See `PERSONAL_INTERNAL_RECORDS_BACKEND_READINESS.md`

**Endpoints to create**:
```
GET    /api/v1/entities/employee_attendance          → list (filter by employee, month)
POST   /api/v1/entities/employee_attendance          → record attendance
PUT    /api/v1/entities/employee_attendance/{id}     → update record
GET    /api/v1/attendance/monthly-summary/{employee_id}/{year}/{month}  → aggregated summary
```

**Effort**: ~1 day backend + frontend wiring

---

### 6. Employee Payments (Internal 15/30)

**Current state**: `generatePaymentRuns()` static generator  
**Backend needed**: New entity + router + service

**Entity**: `employee_internal_payments`  
**Fields**: See `PERSONAL_INTERNAL_RECORDS_BACKEND_READINESS.md`

**Endpoints to create**:
```
GET    /api/v1/entities/employee_internal_payments          → list payment runs
POST   /api/v1/entities/employee_internal_payments          → create payment run
PUT    /api/v1/entities/employee_internal_payments/{id}     → update/mark paid
GET    /api/v1/payments/run/{year}/{month}/{day}            → get run for specific date
POST   /api/v1/payments/calculate                           → calculate payment for employee
```

**Effort**: ~1-2 days backend + frontend wiring

---

## Priority P3 — Lower Priority (New modules)

### 7. Employee Advances/Debts

**Current state**: Static `ADVANCES` array  
**Backend needed**: New entity + router + service

**Entity**: `employee_advances_debts`

**Endpoints to create**:
```
GET    /api/v1/entities/employee_advances_debts          → list
POST   /api/v1/entities/employee_advances_debts          → create advance/loan
PUT    /api/v1/entities/employee_advances_debts/{id}     → update
POST   /api/v1/advances/{id}/deduct                      → record installment deduction
```

**Effort**: ~0.5-1 day backend + frontend wiring

---

### 8. Employee Documents

**Current state**: Static arrays in `employeeRecordsData.ts`  
**Backend needed**: New entity + storage integration

**Entity**: `employee_documents`

**Endpoints to create**:
```
GET    /api/v1/entities/employee_documents          → list by employee
POST   /api/v1/entities/employee_documents          → upload/attach
PUT    /api/v1/entities/employee_documents/{id}     → update metadata
DELETE /api/v1/entities/employee_documents/{id}     → remove
```

**Effort**: ~0.5-1 day backend + frontend wiring

---

### 9. Puncte / Bonusuri / Comisioane (Rewards)

**Current state**: Not implemented  
**Backend needed**: Full module (entity + router + service + UI)

**Entities**: `compensation_profiles`, `production_points`, `reward_runs`

**Endpoints to create**:
```
GET    /api/v1/entities/compensation_profiles          → list profiles
PUT    /api/v1/entities/compensation_profiles/{id}     → update profile
GET    /api/v1/rewards/points/{employee_id}/{month}    → monthly points
POST   /api/v1/rewards/calculate-run                   → calculate monthly rewards
GET    /api/v1/rewards/runs                            → list reward runs
```

**Effort**: ~2-3 days full module

---

## Timeline Estimate

| Phase | Duration | Modules |
|-------|----------|---------|
| P1 Sprint | 1-2 days | Client API, Tablet API, Prices actions |
| P2 Sprint | 3-5 days | Documents, Attendance, Payments |
| P3 Sprint | 3-4 days | Advances, Employee Docs, Rewards |
| **Total** | **~7-11 days** | All modules operational |