# Compound Engineering — Shared Finish-Line Map

Canonical rows are also served by:

`GET /api/v1/product-system/reference-finish-line/contract` → `compound_engineering_map`

| axis | entity | owner | handoff_status | risk |
|------|--------|-------|----------------|------|
| modularity | ProductTemplate root/child/roles | Product System | gap | medium |
| form | Intake/Form System field contract | Form System + VL schema | gap | high |
| pd_pt | Product Definition vs Product Truth | Workflow-ADV / operator | gap | medium |
| analyzer | workflow_adv_analyzer_io_contract_v1 | Workflow-ADV Analyzer | ready | low |
| cost | EIC production cost finish line | CostEngine / breakdown | ready | low |
| materials | critical material classification | Inventory + finish-line policy | gap | medium |
| scalability | extension points without page copies | Product System + Form System | gap | high |

All agents must use this map. No independent Form System or modularity definitions.
