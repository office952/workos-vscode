# LABOR_RECIPE_CONTRACT_V1 — CP0 Freeze

| Field | Value |
|-------|--------|
| Kickoff HEAD | `212654a2` |
| Extends | Template Pricing Studio V1 |

## Ownership freeze

| Owner | Owns |
|-------|------|
| Central labor catalog (`workcenter_rates` + typed_catalog=labor) | reusable base rate, unit, status, provenance |
| Product Template | which ops, quantity formula, qty keys, minimums, applicability |
| CPP | commercial line result (unchanged formulas) |
| EIC | provenance (unchanged) |
| Studio | visibility only |

## Recipe identity

`{template_code}::labor_recipe::{operation_code}::{catalog_code}::{formula_token}`  
Optional trailing `::{component_id}` when nested.  
Registry-linked (no ops formula): `...::{catalog_code}::registry_link`.  
Commercial-line labor refs: `...::{line_code}::{catalog_code}::commercial_link`.  
Exact duplicates from ops_json + components_json are collapsed.

## Classification freeze

`LABOR_INTERNAL` · `LABOR_COMMERCIAL` · `MACHINE_OPERATION` · `INTERNAL_SERVICE` · `EXTERNAL_SERVICE` · `INSTALLATION_SERVICE` · `UNKNOWN_AMBIGUOUS` · `LEGACY` · `MISSING_RATE`

## Editability

Read-only V1. No formula builder. No new DB table.

## Schema boundary

Additive `labor_recipes[]` on existing  
`GET /api/v1/product-system/templates/{code}/pricing`  
Bump `schema_version` → `1.1.0`. No Alembic.

## No-migration / freeze

- No rate value changes
- No ACM treatment unblock
- No XOR / dual-select / publish
- No HR / payroll
