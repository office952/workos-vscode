# Lane H — Wave 5 journeys

| FROM | CONTROL | TO | EXPECTED | ACTUAL | CONTEXT | HONESTY |
|------|---------|-----|----------|--------|---------|---------|
| `/employees` | attendance counts widget | `/attendance` | pontaj | pontaj | name may drop | GOOD_EDGE / CONTEXT_LOSS |
| `/attendance` | effects link | `/attendance/effects` | apply pipeline | apply pipeline | month | GOOD_EDGE |
| `/employees-records` | row `<button>` (not `<a>`) | `/employees-records/7` | HR file | HR file (demo) proven | YES | GOOD_EDGE |
| `/employee-payments` | missing pay-base | `/employees` | edit pay base | employees | employee | GOOD_EDGE |
| `/inventory` | honesty | `/inventory/pricing` | offer rates | registry | NO stock | GOOD_EDGE |
| `/colaboratori` | — | Inventory Furnizori | same suppliers | same API, two pages | DUPLICATE_ENTRY |
| `/utilaje` | — | `/execution/machine-runs` | MachineRun | not linked from catalog | DEAD_END / TECHNICAL_DESTINATION |
| `/reports` | banner | `/reports/operational` | real ops | DEV audit | ROLE_MISMATCH for sales |
| `/settings` | sheet quality | Inventory | sheet audit | inventory tab | GOOD_EDGE |
| `/documents` | quote/order rows | quotes/orders | open source | often disabled | DEAD_END |
| Lucrări vs Oameni | Plăți under Management | HR money | payments | IA split from Oameni | SURPRISING_DESTINATION |

**NAVIGATION_HONESTY_ISSUE_COUNT = 6**
