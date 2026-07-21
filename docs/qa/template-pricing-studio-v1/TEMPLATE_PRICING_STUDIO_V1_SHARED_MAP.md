# TEMPLATE_PRICING_STUDIO_V1 — Shared Truth Map (Compound Engineering)

All agents consume this map. No parallel recipe contracts.

| Field | Meaning |
|-------|---------|
| template_code | Canonical Product Template code |
| template_version | Template version / revision if present |
| recipe_item_id | Derived `{template}::{kind}::{stable_code}` |
| recipe_kind | material / machine_operation / labor / service / commercial_line / minimum / unknown |
| catalog_code | Reusable Pricing Registry / inventory / workcenter code |
| quantity_key | CPP quantity_paths / formula quantity key |
| formula_owner | template seed / commercial_rules / compiler / service |
| applicability | module_gate / material_gate / criticality |
| rate_source | pricing_registry / documented_commercial / missing |
| cost_or_rate | purchase_cost / reusable_rate / commercial_documented |
| unit | Canonical unit |
| current_value | Read-only resolved value when already stored |
| status | active / missing / blocked / warning |
| provenance | technical_source / rule source |
| CPP reader | commercial line_code / pricing_rule_code |
| EIC reader | internal rule code when known |
| readiness_check | technical vs commercial flags |
| editable | always false in V1 |
| blocker | exact blocker code when present |
| legacy | yes when code-derived / interim |
| confidence | high / medium / low |

## Source chain

```text
Inventory / Pricing catalogs  →  reusable rates
Product Template recipe       →  quantity + applicability + selection
CPP                           →  commercial line result
EIC                           →  provenance / internal evidence
Template Pricing Studio       →  composes + explains (no invent)
```
