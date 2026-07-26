# Workflow-ADV terminology

## Purpose
Define the canonical vocabulary used by the Workflow-ADV documentation package.

## Ownership
Workflow-ADV owns the future contracts. Current WorkOS is historical laboratory/reference evidence, not Workflow-ADV Platform architecture.

## Glossary
| Term | Canonical meaning |
|---|---|
| Product System | The governed set of templates, composition, schemas, confirmed truth, quantities, catalog references, formulas, and cost output. |
| Product Family | A business grouping of related Product Templates; it is not a substitute for a template or a cost owner. |
| Product Template | The canonical reusable product entity. It owns its technical scope, schema, resource references, and formulas. Do not create a parallel `ComponentTemplate` without a proven need. |
| root / child / dual-role | `root` composes product roles; `child` contributes a bounded technical module; `dual-role` can do both. |
| Form Schema | Versioned, schema-driven field contract: identity, type, unit, source, validation, visibility, destinations, quantity impact, and version. |
| Intake | Collection and presentation of inputs under a Form Schema. Intake captures data; it does not own business formulas. |
| Product Definition (PD) | Versioned configuration intent from operator input, observed data, and proposals. It is not confirmed Product Truth. |
| Product Truth (PT) | Operator-confirmed facts with provenance, revision, and hash. PT is the input authority for quantities and cost. |
| Inventory Material | Canonical catalog identity for a material. Templates reference it; templates do not invent local material authority. |
| Material Price | Canonical purchase-cost evidence for a concrete catalog material or variant. A selector has no generic price. |
| Operational Process | First-class catalog resource such as CNC, Laser, Print, Lamination, Edge-return forming, or Painting; it owns rates/compatibility, while templates supply quantities. |
| Labor Operation | Cataloged human-work resource and rate consumed by a recipe through a physical driver. |
| Service | Cataloged externally supplied or specialized work consumed by a recipe; not a locally invented template price. |
| Quantity | Named, unit-bearing output from confirmed truth through a declared formula. |
| Formula | Versioned business rule owned by exactly one technical template or cost authority. |
| EIC | Internal production cost and laboratory finish-line authority: materials + operational processes + labor + services + consumables + packaging. |
| CPP | Commercial-price read model retained only as reconciliation evidence; never offer authority in this reference. |
| Production Cost | The EIC output, before markup, profit, offer, discount, order, invoicing, execution, or shopfloor scope. |
| DEV MODE | A new draft/version for changes. It never mutates an accepted frozen operational version in place. |
| FREEZE ON | Immutable accepted operational version. Evolution is Frozen v1 → DEV v2 → validate → promote → FREEZE ON. |
| Workflow-ADV Lab | Historical/reference environment used to prove contracts and fixtures. Current WorkOS belongs here. |
| Workflow-ADV Platform | Future operator-oriented implementation built from transferred contracts, not from Lab UI chrome or legacy paths. |
| Workflow-ADV Analyzer | Separate desktop analysis application. It emits versioned observed/proposed payloads; it does not parse in WorkOS, price, or write PT. |

## Invariants
- Product Template is the canonical template entity.
- PT follows operator confirmation; Analyzer observations and proposals do not silently become PT.
- EIC is the finish line; CPP is reconciliation evidence only.
- `MAT-LED-PSU-12V` is a `VARIANT_SELECTOR`, never a generically priced SKU.

## Evidence sources
- `docs/qa/product-system-reference-complete/runtime/reference_complete.json`
- `docs/qa/product-system-reference-finish-line-v1/runtime/contract.json`
- `docs/qa/product-system-reference-finish-line-v1/runtime/analyzer_io_contract.json`

## Limitations
The glossary records frozen reference contracts; it does not establish a Form Builder, visual add-child factory, Supplier Import, or Platform implementation.

## Do-not-transfer
Do not transfer ambiguous Lab terminology as Platform authority, or relabel CPP as an offer decision.

## Related docs
- [Overview](WORKFLOW_ADV_PRODUCT_SYSTEM_OVERVIEW.md)
- [Domain model](DOMAIN_MODEL.md)
- [Product Truth contract](PRODUCT_TRUTH_CONTRACT.md)
- [Request-to-cost flow](REQUEST_TO_COST_FLOW.md)
