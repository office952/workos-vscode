# Lane E — Resources / Admin / Reporting page cards

Read-only. No FINAL. E owns these cards.

## `/utilaje`

| Field | Value |
|-------|--------|
| PURPOSE | Machine catalog + capacity diagnostic (not client price, not MachineRun) |
| PRIMARY USER | operator / manager / admin |
| OWNS | catalog read |
| PROJECTS | WC util% from dashboard; maintenance mock |
| Disposition | KEEP + honesty (capacity IMPLEMENTED_INACTIVE) |

## `/inventory`

| Field | Value |
|-------|--------|
| PURPOSE | Stock, suppliers, consumption, sheet-quality — not offer authority |
| PRIMARY USER | operator / sales / manager / admin |
| OWNS | stock + material catalog + sheet-quality |
| PROJECTS | unit_cost as operational purchase ref |
| PLACEHOLDER | Automatizare tab mock-only |

## `/inventory/pricing`

| Field | Value |
|-------|--------|
| PURPOSE | Internal pricing registry (material / rates / markup) — not official offer |
| PRIMARY USER | **admin only** |
| OWNS | registry + markup policies + WC/service rates |
| ELSEWHERE | FX/VAT defaults in Settings; official money = Quote/Order snapshot |

## `/settings`

| Field | Value |
|-------|--------|
| PURPOSE | Company VAT/FX, recurring costs, CostEngine intern, SmartBill |
| PRIMARY USER | **admin only** |
| Tabs | Societate · Plăți repetitive · Cost Intern · Integrări |

## `/documents`

| Field | Value |
|-------|--------|
| PURPOSE | Commercial document hub UI |
| Class | **PLACEHOLDER** / synthetic projection from quotes/orders |
| Mutations | generate/upload/PDF all disabled |

## `/colaboratori`

| Field | Value |
|-------|--------|
| PURPOSE | External partners (suppliers/subcontractors) — not Clients, not HR |
| SOURCE_OF_TRUTH | same `suppliers` API as Inventory Furnizori |
| Class | **DUPLICATE** display of inventory suppliers + extra UX mapping |

## `/reports`

| Field | Value |
|-------|--------|
| PURPOSE | Management KPI dashboard |
| Class | **PROJECTION** — live `orders.total_amount`, simplified OTIF/util |
| Audience | sales / manager / admin |

## `/reports/operational`

| Field | Value |
|-------|--------|
| PURPOSE | Execution/workforce completeness audit wall (no money) |
| Nav | DEV tooling / AUDIT |
| Class | **AUDIT_ONLY** |
