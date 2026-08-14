# Wave 5 — reports

| Surface | Purpose | Class |
|---------|---------|--------|
| `/reports` | Management KPIs | **PROJECTION** / decision dashboard; money = live order totals; OTIF/util simplified |
| `/reports/operational` | Completeness audit | **AUDIT_ONLY**; no money; plan vs actual at task grain |

**REPORTS_PURPOSE = PARTIAL / TECHNICAL** — useful projections, not a third commercial/execution SoT. Operational reports hidden in DEV nav.

**REPORTS_MONEY_MODEL = LIVE_OPERATIONAL_PROJECTION** — `Orders.total_amount` live aggregation. Frozen snapshot = NO. Live pricing registry = NO. Live company commercial settings = NO. Do not promote `/reports` into commercial pricing truth.
