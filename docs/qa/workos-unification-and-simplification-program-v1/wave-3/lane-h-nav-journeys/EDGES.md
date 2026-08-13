# Lane H — operational journeys

## Followed (RT)

| FROM | CONTROL | TO | HONESTY | CONTEXT |
|------|---------|-----|---------|---------|
| `/orders/ORD-IV6-V2-1786318810-31` | Vezi execuția | `/execution/973024` | GOOD_EDGE | PARTIAL (code → numeric id) |
| `/execution` | row | `/execution/21099` | GOOD_EDGE | URL sync |
| `/execution` | Back | `/execution` | GOOD_EDGE | YES both themes |
| `/shop-floor` | (banner) Acțiune task | `/operator` | TECHNICAL_DESTINATION | canonical home → COMPAT |
| `/shop-floor` | Stații | `/tablet` | TECHNICAL_DESTINATION | same |
| `/employee-app-v2` | URL observe | `/employee-app-v2` | TECHNICAL_DESTINATION | not in shell |

## Role denials (proven)

| Role | Route | Landing |
|------|-------|---------|
| sales | `/shop-floor` | `/quotes` |
| sales | `/operator`, `/ops-graph`, `/machine-runs` | `/quotes` |
| operator | `/execution` | `/shop-floor` |

## Journey: Order → Execution → Atelier → Task → MachineRun → Actual

```text
/orders/:code --Vezi execuția--> /execution/:dbId
/execution --row--> /execution/:dbId --next-step--> /shop-floor --next-step--> /operator | /tablet
/execution/machine-runs --(empty)--> detail STATE_NOT_REACHED
/employee-app-v2  (parallel, unlinked from shell)
```

**ORDER_TO_EXECUTION = PARTIAL** (edge works; URL becomes numeric id). Atelier live job is **DIFFERENT_ACTIVE_WORK** (`ORD-92400`), not a failed projection of 973024.
