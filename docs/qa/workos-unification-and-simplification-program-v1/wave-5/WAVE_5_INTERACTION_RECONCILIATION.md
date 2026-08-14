# Wave 5 interaction reconciliation

RT: 54 surfaces, 170 shots, scroll FAIL=0, role MATCH=100%.

| Route | Inventory | Runtime | Status |
|-------|-----------|---------|--------|
| `/employees` | list+detail | admin L+D; manager light | RECONCILED |
| `/attendance` | month + events | admin L+D; manager light | RECONCILED |
| `/attendance/effects` | tabs | admin L+D tabs | RECONCILED |
| `/employees-records` | list | admin L+D; manager light | RECONCILED list |
| `/employees-records/:id` | 4 tabs | row `<button>` + deep-link `/employees-records/7` | **RECONCILED** |
| `/employee-payments` | slots 15/30 | admin L+D tabs; manager light | RECONCILED |
| `/employee-advances` | ledger | admin L+D; manager denied | RECONCILED |
| `/utilaje` | list+detail | admin L+D; manager/operator light | RECONCILED |
| `/inventory` | tabs | admin L+D; sales/manager/operator light | RECONCILED |
| `/inventory/pricing` | views | admin L+D; others denied | RECONCILED |
| `/settings` | 4 tabs | admin L+D; others denied | RECONCILED |
| `/documents` | table | admin L+D; sales/manager light | RECONCILED |
| `/colaboratori` | list | admin L+D; manager light | RECONCILED |
| `/reports` | KPIs | admin L+D; sales/manager light | RECONCILED |
| `/reports/operational` | 5 tabs | admin L+D | RECONCILED |

Mutating CTAs not clicked (SNR with blocker).
