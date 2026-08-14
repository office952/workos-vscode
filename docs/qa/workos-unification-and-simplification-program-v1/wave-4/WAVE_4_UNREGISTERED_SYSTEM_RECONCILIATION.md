# Wave 4 gap closure — unregistered reconciliation

Owner rule: `/modules` and `/governance` describe **Level-1 system reality**, not every page, class, helper, projection, or route alias.

Wave 4 initial counts (12 + 9) **over-counted** by treating action surfaces, AppShell homes, and internal registries as independent systems.

## Item-by-item

| NAME | TYPE | RUNTIME_ACTIVE | UI_VISIBLE | HAS_CONSUMER | IN_MODULES | IN_GOV | ALIAS_OF | STATUS |
|------|------|----------------|------------|--------------|------------|--------|----------|--------|
| Atelier `/shop-floor` | projection | YES | YES | YES | NO (named) | PARTIAL (Execution spine) | `execution_plan` + `execution_reality` | **ALIAS_OF_REGISTERED** |
| operator `/operator` | action UI | YES | YES (COMPAT) | YES | NO | PARTIAL | `execution_reality` | **LEGACY_COMPAT** |
| tablet `/tablet` | action UI | YES | YES (COMPAT) | YES | NO | PARTIAL | `execution_reality` | **LEGACY_COMPAT** |
| employee-app-v2 | action UI | YES | standalone | YES | NO | PARTIAL | `execution_reality` | **ALIAS_OF_REGISTERED** |
| dashboard | AppShell home | YES | YES | YES | NO | NO | management chrome over Execution | **FALSE_POSITIVE** |
| clients | page | YES | YES | YES | NO | NO | CRM page | **FALSE_POSITIVE** |
| documents | page | YES | YES | YES | NO | NO | commercial doc hub | **FALSE_POSITIVE** |
| HR cluster | page cluster | YES | YES | YES | PARTIAL (`attendance`) | PARTIAL | `attendance` + HR pages | **ALIAS_OF_REGISTERED** |
| utilaje | page | YES | YES | YES | NO | PARTIAL | `machine_run` + inventory machines | **ALIAS_OF_REGISTERED** |
| reports | page | YES | YES | YES | NO | NO | reporting chrome | **FALSE_POSITIVE** |
| settings | admin chrome | YES | YES | YES | NO | PARTIAL | config host | **FALSE_POSITIVE** |
| output-blocks-preview | lab page | YES | YES (audit) | YES | NO | NO | `product_system` | **AUDIT_ONLY** |
| `/intake-v6-app/*` | standalone alias | YES | YES | YES | NO | NO | `intake_v6` | **ALIAS_OF_REGISTERED** |
| `/execution/ops-graph` | audit page | YES | YES (AUDIT) | YES | NO | PARTIAL | `execution_plan` | **AUDIT_ONLY** |
| `/execution/reality-review` | audit page | YES | YES | YES | NO | PARTIAL | `execution_reality` / `post_job` | **AUDIT_ONLY** |
| company FX/VAT settings | config tab | YES | YES | fallback only | NO | NO | `pricing_commercial` | **INTERNAL_IMPLEMENTATION_DETAIL** |
| SmartBill | integration | config only | YES | NO (disabled) | NO | NO | — | **INACTIVE** |
| Cost Intern UI vs CostEngine card | duplicate surface | YES | YES | non-authoritative | YES (`cost_engine_legacy`) | YES | `cost_engine_legacy` | **LEGACY_COMPAT** |
| mini_module_registry | internal registry | YES | NO | YES (aggregate/CPP) | NO | NO | `product_system` / `product_aggregate` | **INTERNAL_IMPLEMENTATION_DETAIL** |
| color/RAL FE registry | FE config | YES | Intake pickers | YES (display) | NO | NO | `product_system` | **INTERNAL_IMPLEMENTATION_DETAIL** |

## Final counts

| Metric | Initial | Final |
|--------|--------:|------:|
| UNREGISTERED_SYSTEM_COUNT | 12 | **0** |
| UNREGISTERED_CAPABILITY_COUNT | 9 | **0** |
| FALSE_POSITIVES_RETRACTED | — | **5** (dashboard, clients, documents, reports, settings) |
| ALIASES_COLLAPSED | — | **6** (Atelier, employee-app-v2, HR, utilaje, intake-v6-app + Execution action UIs counted as LEGACY_COMPAT not systems) |

**TRUE_UNREGISTERED_SYSTEM = 0**  
**TRUE_UNREGISTERED_CAPABILITY = 0**

Remaining honesty gap (not a missing system): `/modules` does not **name** Atelier / operator / tablet as Execution projections. That is UNDERDOCUMENTED projection labeling, not 12 missing systems. Owner decision later — do not register in this GO.
