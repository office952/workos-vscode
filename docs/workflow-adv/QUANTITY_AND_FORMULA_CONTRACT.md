# Quantity and Formula contract

## Purpose
Establish declared quantity keys and one-authority formula execution from confirmed truth to EIC.

## Ownership
The technical Product Template owning the fact owns its formula. The quantity/formula service is business-calculation authority. The frontend is display-only for business results.

## Contract matrix
| Artifact | Required contract |
|---|---|
| Quantity key | Stable name, unit, source PT fields, owning template, formula version, output value/status |
| Formula | Owner, declared inputs, unit rules, validation, version, target resource/line, provenance |
| Parent-child input | Parent maps confirmed input; child owns its quantity/formula result |
| Resource line | Canonical catalog reference + formula-produced quantity; catalog owns rate/compatibility |
| EIC output | Explainable materials + processes + labor + services + consumables + packaging |

## Invariants
- Every formula has exactly one business owner.
- Quantity inputs are declared Form/PT keys, never hidden UI field reads.
- Parent templates do not duplicate child quantities or return/cant formulas.
- The frontend must not recalculate business truth, totals, quantities, material selection, or EIC. It may render server/authority results and perform non-authoritative presentation validation.
- `POST .../templates/{code}/price-breakdown` is the EIC/CPP evidence path; EIC is authoritative for the reference.
- `MAT-LED-PSU-12V` must resolve to a concrete priced 60/100/160/200W variant before material-cost calculation.

## Evidence sources
- `POST .../templates/{code}/price-breakdown`
- `GET .../form-field-ownership-map`
- `docs/qa/product-system-reference-finish-line-v1/runtime/contract.json`
- VL fixture: EIC `923.2`, CPP `1061`, critical missing `[]`

## Limitations
Formula-authoring UX and generic schema rendering are deferred. Existing Lab UI can display derived values but is not a transferable calculation authority.

## Do-not-transfer
Do not transfer frontend calculators, duplicated parent/child formulas, undeclared CostEngine field consumers, or CPP as a replacement for EIC.

## Related docs
- [Child composition](CHILD_TEMPLATE_COMPOSITION.md)
- [Form Schema contract](FORM_SCHEMA_CONTRACT.md)
- [Product Truth contract](PRODUCT_TRUTH_CONTRACT.md)
- [Request-to-cost flow](REQUEST_TO_COST_FLOW.md)
