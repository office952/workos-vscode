# Workflow-ADV Product System overview

## Purpose
State the transferable Product System boundary and the reference finish line.

## Ownership
Workflow-ADV owns the future Platform contracts. Current WorkOS is a historical laboratory/reference and is not the target Platform architecture.

## Operating boundary
| Included | Excluded |
|---|---|
| Product Templates, composition, Form Schema, PD/PT, quantities, formulas, catalog references, EIC | Markup, offer, negotiation, order, invoicing, execution, shopfloor, mobile, Supplier Import, SVG/DWG/DXF parsing |

| Reference decision | Canonical rule |
|---|---|
| Finish line | Production Cost / EIC |
| CPP | Reconciliation evidence only; not offer authority |
| Template identity | Product Template is canonical; no parallel ComponentTemplate without proven need |
| Analyzer | External desktop I/O only; observe/propose, then operator confirms |
| Material selector | `MAT-LED-PSU-12V` has no generic price; concrete 60/100/160/200W variants are priced |
| Fixture | VL: EIC `923.2`, CPP `1061`, `critical_missing: []` |

## Invariants
- The path is Form Schema → Product Definition → operator confirm → Product Truth → quantities → formulas → EIC.
- Parent templates compose roles; children own their own technical truth. Parent does not duplicate child truth.
- Templates reference canonical catalog resources only; catalog growth is just-in-time.
- EIC includes materials, operational processes, labor, services, consumables, and packaging.

## Evidence sources
- `GET /api/v1/product-system/reference-complete`
- `GET .../reference-finish-line/contract`
- `POST .../templates/{code}/price-breakdown`
- `docs/qa/product-system-reference-complete/`

## Limitations
Form Builder, visual add-child authoring, process catalog UI, global FREEZE implementation, Supplier Import, and Platform UI are deferred. Optional consumables may remain unpriced. Logo is not a complete reference path.

## Do-not-transfer
- Badge-heavy Lab diagnostics as Platform operator UI.
- Offer/Execution as the laboratory finish line.
- Hardcoded template-specific pages as the extension model.
- Generic PSU selector pricing.

## Related docs
- [Terminology](TERMINOLOGY.md)
- [Domain model](DOMAIN_MODEL.md)
- [Template authoring](PRODUCT_TEMPLATE_AUTHORING.md)
- [Request-to-cost flow](REQUEST_TO_COST_FLOW.md)
