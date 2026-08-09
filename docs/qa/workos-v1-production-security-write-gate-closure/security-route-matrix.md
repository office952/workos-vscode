# Security route matrix (V1 critical)

| Domain | Route/action | Anonymous? | Permission | IDOR safe | V1 status |
|--------|--------------|------------|------------|-----------|-----------|
| Intake V5 | `/api/v1/intake-v5/*` | N/A (404) | — | — | DEPRECATED_NOT_MOUNTED |
| Intake V6 | `/api/v1/intake-v6/*` | DENY | `get_current_user` + intake perms on writes | workspace scope | SECURED_ACTIVE |
| Intake V4 | `/api/v1/intake-v4/*` | DENY | `get_current_user` | workspace scope | SAFE_COMPATIBILITY |
| Intake V3 | `/api/v1/intake-v3/*` | N/A (404) | — | — | DEPRECATED_NOT_MOUNTED |
| Intake V2 | `/api/v1/entities/intake_requests` | DENY | auth + intake.* on mutations | entity id | SECURED_ACTIVE |
| Quote | create/update/delete/price | DENY | `quote.*` | quote id | VERIFIED |
| Order | create/update/status | DENY | `order.*` | order id | VERIFIED |
| ExecutionPlan | persist/assign/commands | DENY | `execution.*` | plan/task scope | VERIFIED (prior + auth required) |
| Assignment | assign/reassign | DENY | assign/reassign perms | task scope | VERIFIED (prior closure) |
| Session | start/end controlled | DENY | reality/execution | session/task | VERIFIED (prior closure) |
| MachineRun | manage/execute/read | DENY | `execution.machine_run.*` | run id | VERIFIED |
| Pricing registry | GET `/api/v1/pricing/registry` | DENY | `inventory.view` | n/a read | VERIFIED (read-only) |
| Inventory price writes | materials create/update | DENY | `inventory.create/update` | material id | VERIFIED |
| HR employee | GET employees list/detail | DENY | auth; HR fields need `employee.view_hr_cost` | employee id | CLOSED |
| Employee payments | situation/write | DENY | `employee_payments.read/write` | employee id | CLOSED |
| Admin/settings | settings | DENY | `settings.*` admin | n/a | VERIFIED pattern |

Threat model covered: unauthenticated mutation, unauthorized mutation, HR over-exposure, legacy V5 bypass.
