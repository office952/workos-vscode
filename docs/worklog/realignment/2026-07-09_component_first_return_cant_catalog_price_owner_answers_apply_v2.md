# Component-first RETURN-CANT — Catalog & RAL Price Owner Answers Apply v2

## HEAD before

`72d3686` — Add RETURN-CANT catalog and price inputs workshop

## Scope

Apply owner-confirmed Oracal/RAL catalog and price answers to readonly workshop contract. No pricing activation, no invented Oracal table, no currency conversion.

## Owner answers applied

| Area | Applied | Status |
|------|---------|--------|
| Oracal catalog target | toate codurile Oracal oficiale | partial_confirmed |
| Oracal calculation | lățime rolă × lungime = mp | owner_confirmed |
| Oracal roll widths | 100 cm · 126 cm | owner_confirmed |
| Oracal price table | owner has table — values not stored | partial_confirmed |
| RAL collection | RAL Classic (Intake V6 / ralColors.ts) | owner_confirmed |
| RAL material prices | 2.00/2.50/3.00/4.00 EUR/ml by depth | owner_confirmed |
| RAL labor | 1.00 EUR/ml all depths | owner_confirmed |
| RAL minimum | 100 lei — scope pending | partial_confirmed |
| Material-depth | Al 0.6 mm valid 30/60/80/100 | owner_confirmed |

## Still pending / partial

- Oracal catalog import/records
- Oracal price table values by code/family
- Oracal catalog shape fields
- RAL catalog shape in product system
- RAL minimum scope (lucrare/set/culoare/comanda)

## Blockers before pricing

- Oracal actual catalog data/import not stored yet
- Oracal price table values not stored yet
- RAL list data/source not materialized in product system catalog
- RAL minimum scope unresolved (100 lei confirmed)
- Pricing activation not allowed
- Product Truth live write not allowed

## What was not invented

No Oracal code records · no Oracal price values · no RAL codes · no lei→EUR conversion · no pricing formulas

## Tests

Unit: **159/159 PASS** · Playwright: **1/1 PASS**

## Screenshots

`docs/qa/component-first-return-cant-catalog-price-owner-answers-apply-v2/screenshots/` — 12 files

## Final verdict

**PASS**

## Next owner questions

1. Oracal catalog import source
2. Oracal price table values by code/family
3. RAL minimum scope
4. Oracal catalog shape confirmation
