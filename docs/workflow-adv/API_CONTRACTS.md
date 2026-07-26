# API Contracts

## Purpose
Classify API surfaces by authority and transferability. This document is intentionally selective: it records the evidence endpoints needed to understand the reference and the future canonical capabilities Workflow-ADV must provide, without declaring every current endpoint a public API.

## Ownership

| Surface | Owner | Status |
|---|---|---|
| Lab reference evidence endpoints | Current Product System reference implementation | Read-only evidence, not automatically Platform API |
| Future canonical Workflow-ADV APIs | Workflow-ADV Platform architecture | Contract to design and version before implementation |
| Material price records | Pricing | Future canonical capability owner |
| Material identity and availability | Inventory | Future canonical capability owner |
| Process and recipe definitions | Operational Processes / recipe owners | Future canonical capability owner |

## Invariants
- Endpoint existence does not establish domain authority or transferability.
- Reference endpoints are evidence readers/adapters; they must not be mistaken for a universal Workflow-ADV public surface.
- Future canonical writes require explicit versioning, authorization, audit/provenance, lifecycle controls, and owner boundaries.
- No API may accept an AI-invented material price, silently convert a selector to a priced SKU, or write PT without operator confirmation.
- Every canonical cost result is scoped to contract versions and its source references; it may not be an opaque total.

## Reference evidence endpoints

| Endpoint or endpoint family | Evidence purpose | Transfer status |
|---|---|---|
| `GET /api/v1/product-system/reference-complete` | Closure matrix, readiness facts, and handoff evidence | Lab reference reader |
| `GET .../reference-finish-line/contract` | Frozen finish-line contract | Lab reference reader |
| `GET .../form-field-ownership-map` | VL field ownership evidence | Lab reference reader |
| `GET .../analyzer-io-contract` | Analyzer observed/proposed I/O boundary | Lab reference reader |
| `GET .../critical-materials` | Critical classification evidence | Lab reference reader |
| `GET /api/v1/pricing/material-market-prices` | Purchase-price registry evidence | Reference reader; Pricing ownership transfers, path does not |
| `POST .../templates/{code}/price-breakdown` | EIC/CPP reference breakdown | Reference evaluator/reader; no second calculator |

Ellipses above preserve intentionally unspecified route prefixes. They document evidence families, not a promise of exact future paths.

## Future canonical Workflow-ADV API capabilities

| Capability | Required contract shape | Owner |
|---|---|---|
| Inventory material reference | Versioned concrete material/variant identity; availability context | Inventory |
| Pricing material price evidence | Concrete material reference, source, unit, normalized conversion, review/freshness, provenance | Pricing |
| Product System configuration/PT | Versioned PD, explicit confirmation into PT, revision/hash/provenance | Product System + operator |
| Selector resolution | Selector, allowed variants, confirmed selection, resolver policy/version | Inventory/Product System |
| Operational process catalog | Fields in [Operational Process Contract](OPERATIONAL_PROCESS_CONTRACT.md), version, compatibility, active state | Operational Processes |
| Labor/service recipes | Reusable resource/version, physical driver, cost basis, applicability, provenance | Recipe owners |
| Production-cost evaluation | EIC lines, source versions, quantities, readiness findings, immutable evaluation ID | Production-cost authority |
| Lifecycle governance | Draft/validate/E2E/publish/deprecate/archive transitions with audit trail | Product System owner |

## Deprecated and do-not-transfer API patterns

| Pattern | Reason |
|---|---|
| WorkIntake V1 or parallel legacy intake routes | Parallel legacy path, not the Workflow-ADV baseline |
| Hard-coded template-code endpoint/page behavior as extension model | Does not provide governed template generality |
| Undocumented ad-hoc Lab endpoints | Endpoint presence is not a contract |
| APIs that write frozen versions in place | Break auditability and lifecycle invariants |
| Selector-priced material APIs | Violates concrete-variant price truth |
| API paths that create AI market-price fallback | Violates Pricing ownership and no-invention policy |
| APIs that treat CPP as offer authority or production-cost finish line | CPP is reconciliation evidence only |
| Analyzer/parser APIs in the central platform | Analyzer remains separate desktop observed/proposed I/O |

## Evidence

| Evidence | What it establishes |
|---|---|
| `docs/qa/product-system-reference-complete/DOCUMENTATION_HANDOFF_INPUT_PACKAGE.md` | Deliberately limited reference endpoint list |
| `docs/qa/product-system-reference-complete/` | Reference-complete evidence/readiness surface |
| `docs/qa/material-market-price-registry-v1/` | Pricing registry provenance and no fallback |
| `docs/qa/product-price-breakdown-v1/` | Breakdown evaluator shape and EIC/CPP reconciliation |
| Commits `a243dd69`, `f67d56a7`, `7bdd9f61` | Accepted breakdown, market, and selector-closure evidence |

## Limitations
- Future canonical paths, request/response JSON schemas, authorization roles, and persistence are intentionally not invented here.
- The current Lab has no global Freeze write API; this does not authorize a substitute ungoverned write endpoint.
- This document does not enumerate all current routes because route exhaustiveness would transfer accidental implementation surface.

## Do-not-transfer
- Do not copy current route names, router organization, stale environments, or Lab UI calls as Platform architecture.
- Do not expose undocumented internal adapters as public Workflow-ADV APIs.
- Do not infer a canonical write contract from a GET evidence endpoint.

## Related docs
- [Inventory and Material Contract](INVENTORY_AND_MATERIAL_CONTRACT.md)
- [Material Price Source Contract](MATERIAL_PRICE_SOURCE_CONTRACT.md)
- [Operational Process Contract](OPERATIONAL_PROCESS_CONTRACT.md)
- [Readiness and Lifecycle](READINESS_AND_LIFECYCLE.md)
