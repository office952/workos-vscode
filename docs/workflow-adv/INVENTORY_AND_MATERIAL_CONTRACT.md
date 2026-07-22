# Inventory and Material Contract

## Purpose
Define the boundary by which Product System templates consume material references without creating competing material identity or stock truth. This is a Workflow-ADV contract, not a prescription to copy current Lab UI or persistence.

## Ownership

| Concern | Owner | Product System responsibility |
|---|---|---|
| Material identity, code, family, unit, stock, and availability | Inventory | Reference the canonical material code only |
| Purchase-price truth | Pricing | Consume an eligible price reference; do not calculate or invent it |
| Applicability, required quantity, and material role | Product System | Declare why and how much a referenced material is needed |
| Observation/proposal | Analyzer or AI | Supply non-authoritative evidence only |

## Invariants
- A physical material used by a template has one canonical Inventory identity.
- A template stores a reference and a role; it does not become a second material catalog.
- Catalog growth is just-in-time (JIT): create a material only when a required template, recipe, or process needs it. Do not seed speculative catalog rows.
- Missing stock or material identity is visible as a readiness condition. It is not repaired by a template-local alias.
- `MAT-LED-PSU-12V` is a family selector, not a purchasable material or priced SKU. Concrete Inventory variants are `MAT-LED-PSU-12V-60W`, `-100W`, `-160W`, and `-200W`.
- A selector resolves through confirmed configuration to one concrete variant before a material-cost line can be produced.
- Inventory ownership does not transfer purchase-price authority to Inventory; it remains a reference consumer of Pricing truth.

## Evidence

| Evidence | What it proves |
|---|---|
| `docs/qa/product-system-reference-complete/` | Inventory is complete for the VL reference path and critical gaps are empty |
| `docs/qa/material-market-price-registry-v1/` | Identity remains in Inventory while purchase truth is surfaced with provenance |
| Critical-fill commit `7bdd9f61` | PSU selector is not falsely reported as an unpriced critical material |
| `docs/qa/active-template-critical-material-fill-v1/` | VL resolves the concrete 100W variant rather than pricing the selector |

## Limitations
- Supplier Import, broad stock reservation, and optional-consumable completion are deferred.
- Current evidence proves the VL reference path; it is not a claim that every catalog material has complete commercial or stock data.
- The contract does not define warehouse movements, procurement approval, or ERP synchronization.

## Do-not-transfer
- Do not transfer template-local material creation as a Platform extension mechanism.
- Do not transfer a generic price, stock row, or critical requirement to `MAT-LED-PSU-12V`.
- Do not transfer current Lab catalog screens, seeded rows, or legacy intake paths as canonical Workflow-ADV architecture.

## Related docs
- [Material Price Source Contract](MATERIAL_PRICE_SOURCE_CONTRACT.md)
- [Operational Process Contract](OPERATIONAL_PROCESS_CONTRACT.md)
- [Production Cost Breakdown Contract](PRODUCTION_COST_BREAKDOWN_CONTRACT.md)
- [Terminology](TERMINOLOGY.md)
