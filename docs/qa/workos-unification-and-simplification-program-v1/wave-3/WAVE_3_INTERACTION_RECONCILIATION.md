# Wave 3 interaction reconciliation

| Route | Inventory | Runtime | Status |
|-------|-----------|---------|--------|
| `/shop-floor` | grid, blocked, next-step, flux | exhausted both themes; blocked-focus | RECONCILED |
| `/execution` | tiles, table, row | admin/manager/sales × L+D | RECONCILED |
| `/execution/:id` | panels, expandables, generate, start | 973024 + 21099; expand summaries; mutations SNR | PARTIAL (not every nested panel isolated) |
| `/execution/machine-runs` | scope, create, rows | list + empty detail | list RECONCILED; detail SNR |
| `/execution/ops-graph` | table, assign, fixture | captured; assign not clicked | RECONCILED read-only |
| `/execution/reality-review` | filters | captured long scroll | RECONCILED |
| `/operator` | assign, start, employee | first fold (initial) + jump-to-end (gap closure); **FINITE_STATIC PASS** | RECONCILED |
| `/tablet` | stations | selector (initial) + `/tablet/print` drill | RECONCILED |
| `/employee-app-v2` | tasks | observe shot | OBSERVE |

FULL_SCROLL_FAILURES_FINITE_SURFACES = 0 (gap-closure `/operator` bottom). Initial 4 FAIL rows superseded — see `WAVE_3_EVIDENCE_RECONCILIATION.md`.
