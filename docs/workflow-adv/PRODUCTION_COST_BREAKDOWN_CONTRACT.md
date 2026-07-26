# Production Cost Breakdown Contract

## Purpose
Define the production-cost breakdown as the auditable EIC finish line. Its job is to explain production cost from governed inputs, not to create an offer or replace commercial pricing.

## Ownership

| Input or result | Owner | Breakdown role |
|---|---|---|
| Material identity/stock | Inventory | Referenced material context |
| Material purchase price | Pricing | Governed material cost evidence |
| Process definition/cost basis | Operational Processes | Governed process line basis |
| Labor/service recipe | Recipe owner | Governed recipe line basis |
| Applicability and quantities | Product System | Confirmed quantity inputs |
| EIC aggregation and provenance | Production-cost authority | Finish-line output |
| CPP | Historical commercial read model | Reconciliation evidence only |

## Invariants
- EIC equals the governed sum of materials, operational processes, labor, services, consumables, and packaging for the confirmed scope.
- Each line identifies its group, resource reference/version, quantity, unit, cost basis, amount, and provenance. Grouping may include `material`, `machine/process`, `labor`, `service`, `consumable`, `packaging`, `ai_decision`, and `adjustment`; an AI decision alone cannot add ungoverned cost.
- EIC occurs after Product Truth confirmation and declared quantity evaluation. It is before markup, profit, discount, offer, order, invoicing, execution, and shopfloor handoff.
- The breakdown is a read model over authoritative inputs; it must not introduce a second calculator.
- CPP is retained only to reconcile historical/reference evidence. It is not an offer authority, a replacement EIC total, or authorization to transfer commercial pricing behavior.
- The canonical VL reference evidence is EIC `923.20` and CPP `1061.00`, with reconciliation passing. These values are fixture evidence, not reusable market rates.
- Unpriced required material, incompatible process, unresolved selector, or incomplete recipe is exposed as a missing/blocked readiness condition rather than silently excluded.

## Evidence

| Evidence | Result |
|---|---|
| `docs/qa/product-price-breakdown-v1/` | 42 VL lines; EIC `923.20`, CPP `1061.00`, both reconcile |
| Breakdown commit `a243dd69` | Authoritative breakdown read model accepted |
| `docs/qa/product-system-reference-complete/` | EIC is `COMPLETE_AND_RECONCILED`; CPP is `RECONCILIATION_ONLY` |
| `docs/qa/material-market-price-registry-v1/` | Material provenance enriches lines without calculation authority change |
| Critical-fill commit `7bdd9f61` | Concrete PSU 100W line preserves the EIC/CPP fixture totals |

## Limitations
- The reference deliberately stops at production cost. Offer, markup, order, execution, and invoicing are outside this contract.
- Optional consumable purchase gaps may remain visible.
- ACM and Logo evidence have explicitly constrained states; they do not establish VL-equivalent EIC completeness.

## Do-not-transfer
- Do not transfer CPP as an offer-completion, quote, or pricing authority.
- Do not transfer a UI total, legacy calculator, or snapshot mutation as a substitute for governed EIC inputs.
- Do not hide incomplete inputs merely to preserve a total.

## Related docs
- [Material Price Source Contract](MATERIAL_PRICE_SOURCE_CONTRACT.md)
- [Operational Process Contract](OPERATIONAL_PROCESS_CONTRACT.md)
- [Labor and Service Recipe Contract](LABOR_AND_SERVICE_RECIPE_CONTRACT.md)
- [Test Fixtures](TEST_FIXTURES.md)
