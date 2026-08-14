# Wave 5 — support-system source of truth

| Concept | CANONICAL_OWNER | CODE | UI | Duplicates |
|---------|-----------------|------|-----|------------|
| Employee master | People | entities/employees | `/employees` | records list names |
| Attendance | People | employee-attendance | `/attendance` | payments read |
| Assignment | Execution | operator tasks | `/operator` | is_assignable on employees |
| Session | Execution | task sessions | Atelier/operator | none on HR |
| Labor cost (plan) | People / CostEngine | employee fields | `/employees` | Settings Cost Intern |
| Payment | People | employee-payments | `/employee-payments` | — |
| Advance | People | employee-balances | `/employee-advances` | demo debts on HR profile |
| Machine catalog | Resources | /machines | `/utilaje` | — |
| MachineRun | Execution | machine-runs | `/execution/machine-runs` | utilaje job fields empty |
| Inventory item / stock | Inventory | inventory_materials | `/inventory` | — |
| Material cost | Pricing registry | pricing/registry | `/inventory/pricing` | inventory unit_cost |
| Commercial price | Quote/Order snapshot | snapshot V2 | `/quotes` `/orders` | pricing estimated net; reports live totals |
| Settings VAT/FX | Settings | company commercial | `/settings` | Wave 2 order stamp |
| Document | none (MOCK) | FE `generateMockDocuments` | `/documents` | live quote/order ids; no store |
| Collaborator | Inventory suppliers (one API) | `GET /api/v1/entities/suppliers/all` | `/colaboratori` + Inventory Furnizori | **SAME_TRUTH_DIFFERENT_PROJECTION** — not two registries |
| Report projection | Reports | reports-summary (`Orders.total_amount`) | `/reports` | LIVE_OPERATIONAL_PROJECTION; not snapshot / pricing / settings |
