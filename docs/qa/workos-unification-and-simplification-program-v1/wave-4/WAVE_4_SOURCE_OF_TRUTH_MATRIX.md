# Wave 4 — source of truth matrix

| Concept | CANONICAL_OWNER | CODE_OWNER | UI_OWNER | DOC_OWNER | Duplicates |
|---------|-----------------|------------|----------|-----------|------------|
| Product Template | Product System | template JSON + usage policy | `/product-system` | architecture map | FE vs BE scope (premount) |
| Component / module | child PT + links | mini_module_registry + composition | V2 structure | modularity truth | COMP-* candidates unused |
| ProductDefinition | Product Compiler | `product_definition_builder_service` | **no dedicated page** — Intake V6 primary proxy + PS chips (`MULTIPLE_PROXIES`) | /modules verifyRoute `/intake-v6` | preview vs frozen copy |
| ProductAggregate | Product Compiler | aggregate services | PS editor / V6 spine | /modules | template-only vs workspace |
| Commercial measurement | Aggregate (Letters) | letters_commercial_measurement | V6 rail | realignment docs | V6 frontend calculator |
| Pricing key | Commercial Pricing | CPP / registry | `/inventory/pricing` | /modules | CostEngine legacy |
| Quote snapshot | Commercial freeze | quote snapshot | `/quotes` | /modules | — |
| Order snapshot | Commercial freeze | `order_snapshot_service` | `/orders` | /modules | — |
| Execution scope | Frozen graph | execution_preview_from_frozen_graph | `/execution` | Wave 3 | operator unbounded list |
| Execution task | EP / reality | operator_tasks list_all | /operator | Wave 3 | three action UIs |
| Actuals | ExecutionReality | reality JSON | reality-review | Wave 3 | — |
