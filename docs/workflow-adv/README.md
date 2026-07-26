# Workflow-ADV canonical documentation

## Purpose

Index the 25 canonical contracts transferred from the validated WorkOS Product System laboratory into Workflow-ADV planning and implementation.

## Ownership

| System | Role |
|--------|------|
| Current WorkOS | Historical laboratory / reference evidence |
| Workflow-ADV Lab | Professional development and validation |
| Workflow-ADV Platform | Stable frozen operational implementation |
| Workflow-ADV Analyzer | Separate desktop geometry/production-file assistance |

Current WorkOS is **not** the required implementation architecture for Workflow-ADV.

## Status

**DOCUMENTATION_HANDOFF_COMPLETE — PASS** (package readiness)

**Current WorkOS: [`CURRENT_WORKOS_FROZEN_AS_REFERENCE`](../freeze/CURRENT_WORKOS_FROZEN_AS_REFERENCE.md) — PASS**

| Field | Value |
|-------|--------|
| Owner-accept Product System HEAD | `9769bbe8` |
| Documentation handoff tip | `1f2b5a43` / docs tip `e3a9dc09` |
| Evidence root | `docs/qa/product-system-reference-complete/` |
| Finish line | Production cost / EIC |
| Smart Code pre-read | [`docs/architecture/WORKFLOW_ADV_SMART_CODE_STANDARD.md`](../architecture/WORKFLOW_ADV_SMART_CODE_STANDARD.md) |
| Workflow-ADV product code | **BLOCKED** pending `WORKFLOW_ADV_SMART_CODE_ENFORCEMENT_BOOTSTRAP` |

## Audience

| Audience | Use |
|----------|-----|
| Owner / architect | validate boundaries and deferred decisions |
| Platform implementer | build from contracts, not Lab chrome |
| Operator-flow designer | preserve confirmation, provenance, EIC |
| QA / reviewer | trace claims to runtime/API/QA evidence |

## Mandatory pre-read before implementation

1. This index  
2. [`WORKFLOW_ADV_SMART_CODE_STANDARD.md`](../architecture/WORKFLOW_ADV_SMART_CODE_STANDARD.md)  
3. [`TERMINOLOGY.md`](TERMINOLOGY.md)  
4. [`DOMAIN_MODEL.md`](DOMAIN_MODEL.md)

Cursor Always Apply rule: `.cursor/rules/workflow-adv-smart-code.mdc`

## Reading order — 25 contracts

1. [Product System overview](WORKFLOW_ADV_PRODUCT_SYSTEM_OVERVIEW.md)
2. [Domain model](DOMAIN_MODEL.md)
3. Smart Code Standard *(architecture)* — see above
4. [Product Template authoring](PRODUCT_TEMPLATE_AUTHORING.md)
5. [Child Template composition](CHILD_TEMPLATE_COMPOSITION.md)
6. [Form Schema contract](FORM_SCHEMA_CONTRACT.md)
7. [Product Definition contract](PRODUCT_DEFINITION_CONTRACT.md)
8. [Product Truth contract](PRODUCT_TRUTH_CONTRACT.md)
9. [Quantity and Formula contract](QUANTITY_AND_FORMULA_CONTRACT.md)
10. [Inventory and Material contract](INVENTORY_AND_MATERIAL_CONTRACT.md)
11. [Material Price Source contract](MATERIAL_PRICE_SOURCE_CONTRACT.md)
12. [Operational Process contract](OPERATIONAL_PROCESS_CONTRACT.md)
13. [Labor and Service Recipe contract](LABOR_AND_SERVICE_RECIPE_CONTRACT.md)
14. [AI Operational Defaults contract](AI_OPERATIONAL_DEFAULTS_CONTRACT.md)
15. [Production Cost Breakdown contract](PRODUCTION_COST_BREAKDOWN_CONTRACT.md)
16. [Request-to-cost flow](REQUEST_TO_COST_FLOW.md)
17. [Analyzer Desktop Integration](ANALYZER_DESKTOP_INTEGRATION_CONTRACT.md)
18. [UI Information Architecture](UI_INFORMATION_ARCHITECTURE.md)
19. [API contracts](API_CONTRACTS.md)
20. [Readiness and Lifecycle](READINESS_AND_LIFECYCLE.md)
21. [DEV to Implementation Promotion](DEV_TO_IMPLEMENTATION_PROMOTION_CONTRACT.md)
22. [FREEZE and Version Governance](FREEZE_AND_VERSION_GOVERNANCE.md)
23. [Test fixtures](TEST_FIXTURES.md)
24. [Migration and Handoff](WORKFLOW_ADV_MIGRATION_AND_HANDOFF.md)
25. [Dead and Legacy Paths](DEAD_AND_LEGACY_PATHS.md)

Support: [Terminology](TERMINOLOGY.md) · [Template examples](TEMPLATE_EXAMPLES.md)

## Document groups

| Group | Documents |
|-------|-----------|
| Core domain | Overview, Domain, Authoring, Child, Form, PD, PT, Quantity |
| Catalogs & cost | Inventory, Material Price, Operational Process, Labor/Service, AI Defaults, Breakdown |
| Integration & UI | Analyzer, Request-to-Cost, API, UI IA, Fixtures, Examples |
| Governance | Readiness, Promotion, Freeze, Migration, Dead/Legacy |

## Invariants

- EIC production cost is the finish line; CPP is reconciliation evidence only.
- Product Template is the canonical entity; do not invent a parallel ComponentTemplate without proven need.
- Parent does not duplicate child truth.
- Form Schema → Product Definition → operator confirm → Product Truth → quantities → formulas → EIC.
- Inventory owns materials; Pricing owns purchase-price truth; Product System references both.
- Operational processes are first-class catalogs, not anonymous price lines.
- Analyzer observes/proposes only; operator confirms; no central-app CAD parser.
- Lab badge-heavy UI is not Platform UI.
- FREEZE ON versions are immutable; change via new DEV version.
- Frontend does not calculate business truth.

## Do-not-transfer warning

Do **not** transfer as Platform baseline:

- badge-heavy Lab UI
- hardcoded VL page copies as Form Generator
- WorkIntake V1 / obsolete parallel routes
- generic priced PSU selector
- Analyzer → Product Truth without confirmation
- CPP as offer completion
- invented material prices / Supplier Import stubs
- Offer / Order / Execution / mobile as reference finish line
- in-place mutation of frozen operational versions
- in-repo SVG/DXF/DWG parsers
- duplicated calculators / god services

## Evidence

- `docs/qa/product-system-reference-complete/`
- Live proof APIs: `reference-complete`, finish-line, form map, analyzer I/O, critical materials, material-market-prices, price-breakdown
- VL reference: EIC **923.2** · CPP **1061** · critical `[]` · PSU `VARIANT_SELECTOR`

## Next recommended build

`CURRENT_WORKOS_FROZEN_AS_REFERENCE` — do not execute automatically.
