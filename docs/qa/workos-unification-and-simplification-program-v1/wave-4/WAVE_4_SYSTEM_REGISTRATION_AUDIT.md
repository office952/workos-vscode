# Wave 4 — system registration audit

Rule: no active capability is official if absent from /modules or /governance.

Initial candidate table (historical). Counts below are **SUPERSEDED / RESOLVED_BY_GAP_CLOSURE**.

| Kind | Examples | Count (candidates) |
|------|----------|-------------------|
| UNREGISTERED_SYSTEM | Atelier, operator, tablet, employee-app-v2, dashboard, clients, documents, HR cluster, utilaje, reports, settings | 12 |
| UNREGISTERED_PAGE | `/product-system/output-blocks-preview`, `/intake-v6-app/*`, `/execution/ops-graph`, `/execution/reality-review` | 4 |
| UNREGISTERED_CAPABILITY | company FX/VAT settings, SmartBill (disabled) | 2 |
| UNREGISTERED_ENGINE | live Cost Intern UI vs CostEngine LEGACY card | 1 |
| UNREGISTERED_REGISTRY | mini_module_registry (internal), color/RAL FE registry | 2 |

**UNREGISTERED_SYSTEM_COUNT = 12** *(initial; superseded)*  
**UNREGISTERED_CAPABILITY_COUNT = 9** *(initial; superseded)*

Gap closure item-by-item: [`WAVE_4_UNREGISTERED_SYSTEM_RECONCILIATION.md`](./WAVE_4_UNREGISTERED_SYSTEM_RECONCILIATION.md).

**UNREGISTERED_SYSTEM_COUNT_FINAL = 0**  
**UNREGISTERED_CAPABILITY_COUNT_FINAL = 0**  
**FALSE_POSITIVES_RETRACTED = 5**  
**ALIASES_COLLAPSED = 6**

Do not register in this GO. `/modules` still does not *name* Atelier/operator/tablet as Execution projections (UNDERDOCUMENTED labeling, not missing systems).
