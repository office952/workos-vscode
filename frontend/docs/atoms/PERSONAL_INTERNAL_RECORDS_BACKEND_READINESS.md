# Personal / Internal Records — Backend Readiness

**Generated**: 2026-06-03  
**Status**: ⚠️ PARTIAL — Employee list is DB-first; sub-features are static generators

---

## Current State

### What's Wired ✅

| Feature | Data Source | Backend Endpoint |
|---------|------------|-----------------|
| Employee list | `usePersonalData()` hook | `GET /api/v1/entities/employees` |
| Employee CRUD | Generic entity client | Full CRUD at `/api/v1/entities/employees` |

### What's Demo ❌

| Feature | Data Source | Backend |
|---------|------------|---------|
| Employee Profile (documents tab) | `employeeRecordsData.ts` static arrays | ❌ No entity |
| Employee Profile (medicina muncii) | `employeeRecordsData.ts` static arrays | ❌ No entity |
| Employee Profile (alerts) | `employeeRecordsData.ts` static arrays | ❌ No entity |
| Attendance (pontaj) | `generateMonthlyAttendance()` | ❌ No entity |
| Employee Payments (15/30) | `generatePaymentRuns()` | ❌ No entity |
| Employee Advances/Debts | Static `ADVANCES` array | ❌ No entity |

---

## Proposed Entities

### 1. `employee_attendance`

```json
{
  "title": "employee_attendance",
  "properties": {
    "id": { "type": "integer", "description": "PK" },
    "employee_id": { "type": "integer", "description": "FK employees.id" },
    "date": { "type": "string", "description": "YYYY-MM-DD" },
    "day_status": { "type": "string", "description": "present | absent | medical | vacation | holiday | remote | half_day" },
    "check_in": { "type": "string", "description": "HH:MM check-in time" },
    "check_out": { "type": "string", "description": "HH:MM check-out time" },
    "normal_hours": { "type": "number", "description": "Normal hours worked" },
    "overtime_hours": { "type": "number", "description": "Overtime hours" },
    "lunch_break_minutes": { "type": "integer", "description": "Lunch break duration" },
    "notes": { "type": "string", "description": "Day notes" },
    "approved_by": { "type": "string", "description": "Manager who approved" },
    "created_at": { "type": "string" },
    "updated_at": { "type": "string" }
  }
}
```

**Endpoints**:
```
GET    /api/v1/entities/employee_attendance              → list (filter: employee_id, month, year)
POST   /api/v1/entities/employee_attendance              → record day
PUT    /api/v1/entities/employee_attendance/{id}         → update record
GET    /api/v1/attendance/monthly-summary/{employee_id}/{year}/{month}  → aggregated
POST   /api/v1/attendance/bulk-record                    → record multiple days
```

---

### 2. `employee_internal_payments`

**Important**: This is INTERNAL payment tracking only. No fiscal/tax calculations. No brut/net. No official pay slips. Just internal evidence of what was paid when.

```json
{
  "title": "employee_internal_payments",
  "properties": {
    "id": { "type": "integer", "description": "PK" },
    "employee_id": { "type": "integer", "description": "FK employees.id" },
    "payment_day": { "type": "integer", "description": "15 or 30" },
    "year": { "type": "integer" },
    "month": { "type": "integer" },
    "base_amount": { "type": "number", "description": "Base slice (usually 50% of monthly)" },
    "additions": { "type": "number", "description": "Bonuses, overtime pay, rewards" },
    "deductions": { "type": "number", "description": "Advance deductions, loan installments" },
    "total_to_pay": { "type": "number", "description": "base + additions - deductions" },
    "status": { "type": "string", "description": "calculated | approved | paid | cancelled" },
    "paid_at": { "type": "string", "description": "ISO datetime when paid" },
    "paid_by": { "type": "string", "description": "Who processed payment" },
    "notes": { "type": "string" },
    "created_at": { "type": "string" },
    "updated_at": { "type": "string" }
  }
}
```

**Endpoints**:
```
GET    /api/v1/entities/employee_internal_payments              → list
POST   /api/v1/entities/employee_internal_payments              → create payment record
PUT    /api/v1/entities/employee_internal_payments/{id}         → update/mark paid
GET    /api/v1/payments/run/{year}/{month}/{day}                → get run for date
POST   /api/v1/payments/calculate/{employee_id}                 → calculate for employee
POST   /api/v1/payments/bulk-calculate/{year}/{month}/{day}     → calculate all for date
```

---

### 3. `employee_advances_debts`

```json
{
  "title": "employee_advances_debts",
  "properties": {
    "id": { "type": "integer", "description": "PK" },
    "employee_id": { "type": "integer", "description": "FK employees.id" },
    "type": { "type": "string", "description": "advance | loan | debt" },
    "reason": { "type": "string", "description": "Reason for advance/loan" },
    "amount_total": { "type": "number", "description": "Total amount" },
    "amount_paid": { "type": "number", "description": "Amount already deducted/repaid" },
    "amount_remaining": { "type": "number", "description": "Remaining balance" },
    "installment_amount": { "type": "number", "description": "Monthly deduction amount" },
    "installments_total": { "type": "integer", "description": "Total number of installments" },
    "installments_paid": { "type": "integer", "description": "Installments already paid" },
    "next_deduction_date": { "type": "string", "description": "Next scheduled deduction" },
    "status": { "type": "string", "description": "active | completed | cancelled | paused" },
    "approved_by": { "type": "string" },
    "approved_at": { "type": "string" },
    "created_at": { "type": "string" },
    "updated_at": { "type": "string" }
  }
}
```

**Endpoints**:
```
GET    /api/v1/entities/employee_advances_debts              → list (filter: employee_id, status, type)
POST   /api/v1/entities/employee_advances_debts              → create advance/loan
PUT    /api/v1/entities/employee_advances_debts/{id}         → update
POST   /api/v1/advances/{id}/deduct                          → record installment deduction
POST   /api/v1/advances/{id}/pause                           → pause deductions
POST   /api/v1/advances/{id}/cancel                          → cancel remaining
```

---

### 4. `employee_documents`

```json
{
  "title": "employee_documents",
  "properties": {
    "id": { "type": "integer", "description": "PK" },
    "employee_id": { "type": "integer", "description": "FK employees.id" },
    "document_type": { "type": "string", "description": "contract | ci_copy | medical_cert | training_cert | ssm_cert | other" },
    "title": { "type": "string", "description": "Document title" },
    "file_url": { "type": "string", "description": "Storage URL" },
    "file_name": { "type": "string", "description": "Original filename" },
    "expires_at": { "type": "string", "description": "Expiry date (for medical, SSM, etc.)" },
    "issued_at": { "type": "string", "description": "Issue date" },
    "notes": { "type": "string" },
    "is_confidential": { "type": "boolean", "description": "Restricted access" },
    "uploaded_by": { "type": "string" },
    "created_at": { "type": "string" },
    "updated_at": { "type": "string" }
  }
}
```

**Endpoints**:
```
GET    /api/v1/entities/employee_documents              → list (filter: employee_id, type)
POST   /api/v1/entities/employee_documents              → upload/create
PUT    /api/v1/entities/employee_documents/{id}         → update metadata
DELETE /api/v1/entities/employee_documents/{id}         → remove
GET    /api/v1/employee-documents/expiring              → documents expiring soon (alerts)
```

---

## Boundary Rules

- ❌ No fiscal-contabil (no tax calculations, no official brut/net)
- ❌ No fluturași oficiali (no official pay slips)
- ❌ No integration with ANAF/fiscal authorities
- ✅ Internal evidence only (what was paid, when, how much)
- ✅ Attendance tracking (hours, status, overtime)
- ✅ Advance/debt tracking (amounts, installments, status)
- ✅ Document management (upload, expiry alerts, categories)

---

## Link to Internal Payments

The payment calculation flow:
```
Attendance (hours worked)
  + Overtime hours
  + Reward points (future)
  - Advance deductions
  - Loan installments
  = Total to pay (15th or 30th)
```

This is tracked as internal evidence, not as fiscal payroll.