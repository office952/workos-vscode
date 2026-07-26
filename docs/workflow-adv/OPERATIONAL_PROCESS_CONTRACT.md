# Operational Process Contract

## Purpose
Define operational processes as reusable, first-class production resources. A process is not a generic price line and is not owned by an individual product template.

## Ownership

| Concern | Owner | Product System responsibility |
|---|---|---|
| Process definition, compatibility, workcenter, cost basis, and activation | Operational Processes | Reference `process_code` |
| Product applicability and production quantity | Product System | Declare the process role and quantity driver |
| Material identity | Inventory | Supply compatible material references |
| Purchase-price truth | Pricing | Remains outside process definition |

## Invariants
- The initial catalog classes are first-class: CNC mechanical, CNC laser, Print, Lamination, Edge/return forming, Painting, and Other.
- Every operational process version contains the following fields:

| Field | Meaning |
|---|---|
| `process_code` | Stable, unique process identity |
| `name` | Operator-readable name |
| `category` | One of the governed process classes |
| `machine/workcenter` | Capability or execution location |
| `compatible materials/thicknesses` | Explicit admissibility constraints |
| `input_unit` | Unit supplied by Product System |
| `cost_unit` | Unit used by the process cost basis |
| `minimum` | Minimum billable/operational charge or quantity |
| `setup` | Setup basis or charge |
| `active` | Whether the version is eligible for new use |
| `source` | Origin and provenance |
| `version` | Immutable contract revision |

- Product System supplies applicability and quantity; Operational Processes owns the definition and cost basis.
- A process quantity must use a declared `input_unit`; conversion to `cost_unit`, minimum, and setup application are process-owned and auditable.
- Compatibility must be evaluated before the process is eligible for a cost breakdown.
- An inactive process version cannot be newly selected; historical evaluations retain the version they used.
- Process changes follow draft/version/promotion governance rather than mutating an accepted version in place.

## Evidence

| Evidence | What it proves |
|---|---|
| `docs/qa/product-system-reference-complete/` | Operational-process boundary is frozen as a contract |
| `docs/qa/product-system-reference-complete/COMPOUND_ENGINEERING_SHARED_MAP.md` | Processes are catalog resources, while templates supply quantity |
| `docs/qa/product-price-breakdown-v1/` | Machine lines are projected into the breakdown without creating another calculator |
| Critical-fill commit `7bdd9f61` | Reference-complete chain accepted the process boundary |

## Limitations
- Process catalog persistence and operator UI are deferred.
- Current evidence is a contract boundary, not a complete workcenter scheduling or machine telemetry solution.
- Capability, routing, capacity planning, and execution instructions are out of scope.

## Do-not-transfer
- Do not transfer anonymous “machine” or generic adjustment lines as operational-process authority.
- Do not embed process rates, compatibility, or setup rules inside a Product System template.
- Do not infer material/thickness compatibility from an AI suggestion or a template name.

## Related docs
- [Labor and Service Recipe Contract](LABOR_AND_SERVICE_RECIPE_CONTRACT.md)
- [Production Cost Breakdown Contract](PRODUCTION_COST_BREAKDOWN_CONTRACT.md)
- [Readiness and Lifecycle](READINESS_AND_LIFECYCLE.md)
- [Terminology](TERMINOLOGY.md)
