# Material Price Source Contract

## Purpose
Specify the source, eligibility, and provenance rules for material purchase prices used by production-cost evaluation.

## Ownership

| Concern | Owner | Rule |
|---|---|---|
| Material identity and stock | Inventory | Identifies the concrete material or variant |
| Purchase price, unit, source, review status, and freshness | Pricing | Owns price truth and its provenance |
| Quantity and applicability | Product System | Supplies the consumption basis only |
| Suggested default or anomaly signal | AI | May propose evidence; never supplies market truth |

## Invariants
- A material price must identify a concrete Inventory material or concrete variant, a price unit, currency, source/provenance, review status, and effective/freshness context.
- Pricing may normalize a source unit into a consumption unit only with an explicit, auditable conversion. Example: sheet price to square metre uses declared sheet dimensions; an already-per-square-metre price is identity-normalized.
- A missing price remains missing. There is no AI market-price fallback, synthetic default, or silently substituted comparable material.
- `OWNER_CONFIRMED` purchase evidence is authoritative for the scope and date represented; it does not imply that every future purchase has the same price.
- `MAT-LED-PSU-12V` has `raw_price = null` because it is a `VARIANT_SELECTOR`. Only 60W, 100W, 160W, and 200W concrete variants may carry a price.
- A breakdown line must preserve material code, source type, normalized unit/cost, and provenance rather than only a computed amount.
- Price freshness may guide review priority but never creates price truth.

## Evidence

| Evidence | Relevant result |
|---|---|
| `docs/qa/material-market-price-registry-v1/` | No automatic fallback; raw and normalized price provenance are exposed |
| Market commit `f67d56a7` | Registry contract and source precedence evidence |
| Critical-fill commit `7bdd9f61` | 60W/100W/160W/200W variants are concrete; selector stays unpriced |
| `docs/qa/product-price-breakdown-v1/` | VL material lines retain market provenance without a second calculator |

## Limitations
- Supplier Import is deferred; existing supplier identifiers may be sparse and landed cost may be reserved but unpopulated.
- Not every Inventory material has a confirmed purchase price. The reference contract requires visibility, not fabricated coverage.
- This contract does not define negotiated supplier terms, tax treatment, or exchange-rate policy.

## Do-not-transfer
- Do not transfer AI suggestions, historical averages, or a comparable SKU as market-price authority.
- Do not transfer the selector as a directly priced line.
- Do not treat a normalized display value as evidence when its source and conversion are absent.

## Related docs
- [Inventory and Material Contract](INVENTORY_AND_MATERIAL_CONTRACT.md)
- [AI Operational Defaults Contract](AI_OPERATIONAL_DEFAULTS_CONTRACT.md)
- [Production Cost Breakdown Contract](PRODUCTION_COST_BREAKDOWN_CONTRACT.md)
- [API Contracts](API_CONTRACTS.md)
