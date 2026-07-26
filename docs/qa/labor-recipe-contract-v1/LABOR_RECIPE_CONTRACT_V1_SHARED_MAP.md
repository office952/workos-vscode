# LABOR_RECIPE_CONTRACT_V1 — Shared Labor Map

| Field | Meaning |
|-------|---------|
| template_code | Product Template |
| labor_recipe_id | `{tpl}::labor_recipe::{op}` |
| labor_code / catalog_code | Central workcenter / pricing code |
| display_name | Operator label |
| labor_class | LABOR_INTERNAL / … / MISSING_RATE |
| recipe_role | assembly / wiring / finishing / mounting / packaging / other |
| quantity_key | Template quantity inputs |
| quantity_formula / formula_id | Template-owned formula |
| basis | hour / minute / buc / ml / mp / set / produs / unknown |
| minimum | Template or commercial min note |
| dependencies | quote_priced, module gates |
| base_rate_source | pricing_registry |
| internal_cost_rate | resolved/blocked from catalog |
| commercial_rate | resolved/blocked if commercial map exists |
| CPP / EIC reader | line / rule codes when known |
| technical_ready / commercial_ready | separated |
| editable | false V1 |

```text
Central catalogs own reusable labor rates.
Product Templates own labor recipes, quantities, applicability and minimums.
Missing labor rates block commercial readiness, not technical configuration.
```
