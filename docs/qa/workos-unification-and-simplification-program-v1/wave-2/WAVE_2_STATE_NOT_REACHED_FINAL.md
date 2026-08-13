# Wave 2 STATE_NOT_REACHED — final (mutating / protected)

These were **not** forced. Not a Wave 2 failure.

| # | State | BLOCKER | MUTATION_REQUIRED | WHY_NOT_FORCED |
|---|-------|---------|-------------------|----------------|
| 1 | `/intake` + Cerere Nouă | create request | YES | freeze / Owner truth |
| 2 | Intake status change | writes intake status | YES | freeze / Owner truth |
| 3 | Draft quote from list | creates quote | YES | freeze / Owner truth |
| 4 | V6 Schimbă fișier / Schimbă SVG | replaces analysis file | YES | Product Truth |
| 5 | V6 persist / save | writes workspace | YES | Owner truth |
| 6 | V6 layer role / confirm change | already 100% confirmed; change mutates | YES | Product Truth |
| 7 | V6 handoff Continuă către ofertă | disabled; enabling needs confirm completion | YES | freeze / Owner truth |
| 8 | V6 commercial save (adaos/discount) | writes commercial settings | YES | pricing / Owner truth |
| 9 | Orders generate plan | creates execution plan | YES | execution state |
| 10 | Client fiscal verify | writes client entity | YES | Owner truth |
| 11 | Client workspace Cerere nouă | navigates to create | YES | create request |

**STATE_NOT_REACHED_TOTAL = 11**  
**STATE_NOT_REACHED_WITH_EXPLICIT_BLOCKER = 11**

Formerly listed as gaps, now **reached** (not in this table):

- V6 Straturi
- V6 Panou / carcasă
- Client Facturi / Documente / Note / Timeline (PLACEHOLDER)
- Sales `/orders` and `/clients`
- Browser back (tested; orders back is a finding, not untested)
- Hover/focus sample
