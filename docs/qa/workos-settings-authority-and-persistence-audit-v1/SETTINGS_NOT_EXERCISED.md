# SETTINGS_NOT_EXERCISED

Explicit non-runs for this audit (scope lock).

| Item | Why not exercised |
|------|-------------------|
| SmartBill `test-connection` | May hit external network; Owner lock: READ/HEALTH ONLY |
| SmartBill config PUT / token clear | Write + secret handling; not required for authority map once GET proven |
| Recurring payment create/update/delete | Demo empty list proven; CRUD persistence known from API surface; avoid unnecessary demo mutation beyond VAT/FX |
| Cost Intern config save | Read path + schema sufficient; write not needed for authority classification |
| Quote create → change Settings VAT → re-open document vs review | Code-traced; full UI OFAT deferred — classified via static proof of live `get_default_vat_pct` on review/offer |
| Order convert FX stamp e2e | Proven by code + existing pytest (`test_order_snapshot_v2_convert`); not re-run as write on business orders |
| Owner `backend/dev.db` any write | Forbidden — OWNER_DEV_DB_WRITES = 0 |
| Product code / schema / pricing / Product Truth changes | PRODUCT_CODE_CHANGES = 0 |
| Push | PUSH = NO |

These gaps do **not** block the authority verdicts above; they bound residual uncertainty.
