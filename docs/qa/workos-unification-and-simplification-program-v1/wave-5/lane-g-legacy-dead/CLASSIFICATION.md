# Lane G — legacy / placeholder (Wave 5)

| Artifact | Class | Evidence |
|----------|--------|----------|
| `/employees` | ACTIVE_REQUIRED | live CRUD API |
| `/attendance` | ACTIVE_REQUIRED | live events API |
| `/attendance/effects` | ACTIVE_REQUIRED | generate/apply pipeline |
| `/employees-records` | SPECIALIZED + PLACEHOLDER | live names + demo docs |
| `/employee-payments` | ACTIVE_REQUIRED | live payment API |
| `/employee-advances` | ACTIVE_REQUIRED | live balances API |
| `/utilaje` | ACTIVE_REQUIRED catalog; PLACEHOLDER util/maintenance | GET machines; mock maintenance |
| `/inventory` Automatizare | PLACEHOLDER | mock-only |
| `/inventory` stock | ACTIVE_REQUIRED | live materials |
| `/inventory/pricing` | ACTIVE_REQUIRED | registry API |
| Legacy pricing redirects | ACTIVE_COMPAT | App.tsx Navigate |
| `MaterialPriceRegistry.tsx` orphan | LEGACY_REFERENCED | unwired page file |
| `/settings` Cost Intern | LEGACY_REFERENCED | CostEngine not money authority |
| `/settings` Societate static profile | PLACEHOLDER | mock company |
| SmartBill | INACTIVE / PLACEHOLDER | disabled integration |
| `/documents` | PLACEHOLDER | generateMockDocuments; CTAs disabled |
| `/colaboratori` | ACTIVE_COMPAT | same suppliers as Inventory |
| `/reports` | ACTIVE_REQUIRED projection | reports-summary; simplified metrics |
| `/reports/operational` | AUDIT_ONLY | DEV nav |

**LEGACY_REMOVE_CANDIDATE_COUNT = 0** for live routes (orphan MaterialPriceRegistry = REMOVE_CANDIDATE_ONLY file, not a nav page).
