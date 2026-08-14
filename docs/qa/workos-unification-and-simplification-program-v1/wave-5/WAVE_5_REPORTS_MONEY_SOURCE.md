# Wave 5 — reports money source

Observer only. Reports page not recaptured.

```text
REPORT_ORDER_TOTAL_SOURCE = Orders.total_amount (live DB column, summed per completed day)
FROZEN_ORDER_SNAPSHOT_USED = NO
LIVE_COMPANY_SETTING_USED = NO
LIVE_PRICING_REGISTRY_USED = NO
AGGREGATED_DB_VALUE_USED = YES
REPORTS_MONEY_MODEL = LIVE_OPERATIONAL_PROJECTION
```

## Trace

Frontend: `useReportsData` → `GET /api/v1/reports-summary`.

Backend `reports_summary.py`:

- Loads `Orders`, `Quotes`, `ExecutionPlan`, `ExecutionReality`.
- Daily `revenue` = sum of `o.total_amount` where `status == completed` and `updated_at` is that day.
- No snapshot table, no company-settings VAT/FX, no pricing-registry join.
- OTIF = hardcoded `90` if any completion that day else `85`.
- `machineUtil` = reality/plan minutes when present, else default **65**.
- Response `source: "db"`.

This is **not** a second commercial compiler. It **is** a live operational rollup that can drift from Wave 2 frozen sold-work snapshots if an operator treats report revenue as official money.

W5-C5 remains ACTIVE as PRICE_DRIFT **risk**, not as a second price engine.
