# Cross-Module Data Relationships — Backend Plan

**Generated**: 2026-06-03  
**Purpose**: Document all inter-module relationships for VS Code/backend implementation

---

## Relationship Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        COMMERCIAL FLOW (PRIMARY)                              │
│                                                                              │
│  Client ──→ Intake Request ──→ Quote ──→ Order ──→ Execution ──→ Document   │
│    │              │               │          │          │              │      │
│    │              │               │          │          │              │      │
│    └──────────────┴───────────────┴──────────┴──────────┴──────────────┘     │
│                            (all linked by client_id)                          │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        PRODUCTION FLOW                                        │
│                                                                              │
│  ProductSystem ──→ Operation Routing ──→ Operator Tablet ──→ Timing          │
│       │                    │                    │                │            │
│       │                    │                    │                │            │
│       ▼                    ▼                    ▼                ▼            │
│  Product Template    Workstation Config    Task Execution    Points/Rewards   │
│  + Components        + Required Skills    + Reality Data    + Commissions     │
│  + Operations        + Machine Types      + Divergence                        │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        HR / PERSONAL FLOW                                     │
│                                                                              │
│  Employee ──→ Skills ──→ Station Eligibility                                 │
│     │                                                                        │
│     ├──→ Attendance ──→ Internal Payments (15/30)                            │
│     │                         ▲                                              │
│     ├──→ Advances/Debts ──────┘ (deductions)                                │
│     │                         ▲                                              │
│     └──→ Points/Rewards ──────┘ (additions)                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        PRICING FLOW                                           │
│                                                                              │
│  Prices (Materials) ──→ ProductSystem (component costs)                      │
│       │                        │                                             │
│       ▼                        ▼                                             │
│  Commercial Markup ──→ Quote Pricing (line items)                            │
│                                │                                             │
│                                ▼                                             │
│                         Order Total ──→ Invoice Amount                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Relationships

### 1. Client → Request → Quote → Order → Execution → Document

| From | To | FK/Link | Backend Status |
|------|-----|---------|---------------|
| Client | Intake Request | `intake_requests.client_id → clients.id` | ✅ EXISTS |
| Client | Quote | `quotes.client_id → clients.id` | ✅ EXISTS |
| Client | Order | `orders.client_id → clients.id` | ✅ EXISTS |
| Intake Request | Quote | `quotes.intake_id → intake_requests.id` | ✅ EXISTS |
| Quote | Order | `orders.quote_id → quotes.id` | ✅ EXISTS |
| Order | Execution Plan | `execution_plan.order_id → orders.id` | ✅ EXISTS |
| Order | Execution Reality | `execution_reality.order_id → orders.id` | ✅ EXISTS |
| Order | Document | `documents.linked_entity_id → orders.id` | ❌ NEEDS CREATION |
| Quote | Document | `documents.linked_entity_id → quotes.id` | ❌ NEEDS CREATION |

**Implementation note**: The `documents` entity uses polymorphic linking via `linked_entity_type` + `linked_entity_id` to reference quotes, orders, or contracts.

---

### 2. ProductSystem → Operation Routing → Operator Tablet

| From | To | FK/Link | Backend Status |
|------|-----|---------|---------------|
| Product Template | Operations | `product_templates.operations_json` | ✅ EXISTS |
| Operation | Workstation | `operation.workstation` field | ✅ EXISTS (in template) |
| Operation | Required Skill | `operation.required_skill` field | ✅ EXISTS (in template) |
| Execution Plan | Tasks | `execution_plan.tasks_json` | ✅ EXISTS |
| Task | Station | `task.machine_type` → station mapping | ✅ Frontend config |
| Task | Reality | `execution_reality.tasks_json[task_id]` | ✅ EXISTS |

**Implementation note**: `workstationRouting.ts` maps `process_type` → station. This is correctly frontend config. The backend stores operations in product templates and generates execution plan tasks from them.

---

### 3. Operator Tablet → Timing → Points/Rewards

| From | To | FK/Link | Backend Status |
|------|-----|---------|---------------|
| Task Start | Reality timestamp | `reality.tasks_json[].started_at` | ✅ EXISTS |
| Task End | Reality timestamp | `reality.tasks_json[].ended_at` | ✅ EXISTS |
| Task Duration | Calculated | `ended_at - started_at` | ✅ Backend calculates |
| Task Completion | Production Points | `points.task_id` | ❌ NEEDS CREATION |
| Points | Reward Run | `reward_runs.employee_id + month` | ❌ NEEDS CREATION |
| Reward Run | Payment Addition | `payments.additions` | ❌ NEEDS CREATION |

**Implementation note**: The timing data exists in execution reality. The link to rewards/points is the missing piece — completed tasks should generate point entries that feed into monthly reward calculations.

---

### 4. Employee → Skills → Station Eligibility

| From | To | FK/Link | Backend Status |
|------|-----|---------|---------------|
| Employee | Skills | `employees.skills` or separate entity | ⚠️ PARTIAL (field exists, no dedicated entity) |
| Skill | Station | `workstationRouting.ts` required_skill mapping | ✅ Frontend config |
| Employee | Station Assignment | Derived from skills match | ⚠️ Frontend-only logic |

**Implementation note**: Currently, station eligibility is determined by matching employee skills (stored as a field on the employee entity) against station required_skills in `workstationRouting.ts`. A dedicated `employee_skills` entity would allow more granular management (skill levels, certifications, expiry dates).

---

### 5. Employee → Attendance → Internal Payments

| From | To | FK/Link | Backend Status |
|------|-----|---------|---------------|
| Employee | Attendance Records | `attendance.employee_id → employees.id` | ❌ NEEDS CREATION |
| Attendance | Hours Worked | `attendance.normal_hours + overtime_hours` | ❌ NEEDS CREATION |
| Hours Worked | Payment Base | Calculation: hours × rate | ❌ NEEDS CREATION |
| Payment Base | Payment Line | `payments.base_amount` | ❌ NEEDS CREATION |

---

### 6. Employee → Advances/Debts → Internal Payments

| From | To | FK/Link | Backend Status |
|------|-----|---------|---------------|
| Employee | Advance | `advances.employee_id → employees.id` | ❌ NEEDS CREATION |
| Advance | Installment | `advances.installment_amount` | ❌ NEEDS CREATION |
| Installment | Payment Deduction | `payments.deductions` | ❌ NEEDS CREATION |
| Payment Run | Advance Update | `advances.amount_paid += installment` | ❌ NEEDS CREATION |

---

### 7. Prices → ProductSystem / Quote Pricing

| From | To | FK/Link | Backend Status |
|------|-----|---------|---------------|
| Material | Unit Cost | `inventory_materials.unit_cost` | ✅ EXISTS |
| Material | Product Component | `product_template.components[].material_code` | ✅ EXISTS |
| Component Cost | Product Cost | Sum of component costs | ✅ CostEngine calculates |
| Product Cost | Quote Line Item | `quote.line_items[].unit_price` | ✅ EXISTS |
| Markup Policy | Commercial Price | Applied by dry-run | ✅ EXISTS |
| Commercial Price | Quote Total | `quote.grand_total` | ✅ EXISTS |
| Quote Total | Order Total | `order.total_amount` | ✅ EXISTS |

---

## Dependency Graph for Implementation

```
Level 0 (EXISTS):
  clients, employees, intake_requests, quotes, orders,
  execution_plan, execution_reality, inventory_materials,
  product_templates, product_families, suppliers

Level 1 (P1 - Wire existing):
  operator_tasks (API exists, wire frontend)
  clients direct (API exists, wire frontend)

Level 2 (P2 - Create entities):
  documents (new entity)
  employee_attendance (new entity)
  employee_internal_payments (new entity)

Level 3 (P3 - Create entities + logic):
  employee_advances_debts (new entity)
  employee_documents (new entity)
  compensation_profiles (new entity)
  production_points (new entity)
  reward_runs (new entity)
```

---

## Cross-Module Queries (Future)

| Query | Modules Involved | Purpose |
|-------|-----------------|---------|
| Client full history | Clients + Intakes + Quotes + Orders + Documents | Client workspace overview |
| Order complete status | Orders + Execution + Documents + Payments | Order lifecycle tracking |
| Employee monthly summary | Attendance + Points + Advances + Payments | Payment calculation |
| Station productivity | Operator Tasks + Reality + Employees | Station KPIs |
| Product profitability | Prices + Markup + Quotes + Orders | Business intelligence |