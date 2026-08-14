# Wave 5 — technical model leaks

| ROUTE | ELEMENT | INTERNAL_CONCEPT | USER_NEED | SEVERITY | DISPOSITION |
|-------|---------|------------------|-----------|----------|-------------|
| `/employees` | CostEngine / valid_for_cost_engine | engine flag | “cost intern valid” | MED | keep secondary |
| `/inventory/pricing` | pricing_kind / template codes | registry key | rate name | MED | details |
| `/utilaje` | workcenter_code | WC enum | atelier name | MED | Wave 3 same leak |
| `/reports` | OTIF / machineUtil defaults | simplified metric | decision KPI | HIGH | label as model |
| `/reports/operational` | completeness keys | audit schema | gaps | LOW | audit page |
| `/settings` | CostEngine FROZEN | engine | internal cost | MED | already labeled |
| `/colaboratori` | invented rating | FE mapper | trust | MED | hide or persist |

**TECHNICAL_MODEL_LEAK_COUNT = 7**
