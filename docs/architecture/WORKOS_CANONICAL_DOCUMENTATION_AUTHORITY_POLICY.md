# WorkOS - Canonical Documentation Authority Policy

## Status

- Date: 2026-07-04
- Status: CANONICAL_DIRECTION / DOCS_ONLY / NO_RUNTIME_CHANGE
- Code changes: NONE
- Runtime changes: NONE
- Docs cleanup: NONE
- Commit: NONE
- Push: NONE

## Purpose

This document defines how WorkOS documentation must be interpreted before implementation.

WorkOS contains useful historical documents, current runtime evidence, recent canonical contracts, audit reports, worklogs, and old implementation assumptions. They are not all equal authority.

Central rule:

```text
New canonical docs define desired direction.
Current runtime/code proves what exists factually now.
Legacy docs provide context/evidence, not authorization.
Conflicts stop implementation until owner review.
```

## Authority Levels

### Level 1 - Current Runtime / Code Evidence

Runtime and code are factual evidence for what exists now.

They can prove:

- which routes exist;
- which services write data;
- which UI states are currently visible;
- which tests protect a behavior;
- which legacy paths still exist;
- which seeds, registries, fixtures, and defaults can still influence runtime.

They cannot, by themselves, authorize old direction.

Rules:

- If runtime matches the new canonical direction, it is supporting evidence.
- If runtime contradicts new canonical direction, mark `RUNTIME_CONFLICT`.
- Do not silently follow old runtime behavior as desired direction.
- Do not fix conflicts automatically.
- Audit and ask owner before implementation.

### Level 2 - New Canonical Direction Docs

The following documents are the current direction authority:

- `docs/architecture/product-system/WORKOS_SYSTEMS_ALIGNMENT_MAP.md`
- `docs/architecture/product-system/PRODUCT_SYSTEM_PRODUCT_TEMPLATE_VS_COMPONENT_TEMPLATE_CONTRACT.md`
- `docs/architecture/product-system/PRODUCT_SYSTEM_COMPONENT_LEVEL_CALCULATION_READINESS.md`
- `docs/architecture/product-system/PRODUCT_SYSTEM_FORM_SYSTEM_COMPOSITION_CONTRACT.md`
- `docs/architecture/product-system/PRODUCT_SYSTEM_COMPONENT_PRODUCTION_OPERATIONS_CONTRACT.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_E2E_DISCOVERY_DIRECTION_AND_ROADMAP.md`
- `docs/architecture/product-system/INTAKE_V6_PRODUCT_TRUTH_CONTRACT.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_INTAKE_V6_REUSABLE_COMPONENTS_CONTRACT.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_INTAKE_V6_MODULAR_FORM_READINESS_BOUNDARY.md`
- `docs/architecture/product-system/VOLUMETRIC_LETTERS_INTAKE_V6_MODULAR_FORM_UI_STATE_CONTRACT.md`
- `docs/qa/intake-v6-order-ui-baseline/2026-07-04/INTAKE_V6_ORDER_INTEGRATION_AUDIT.md`
- `docs/qa/intake-v6-order-ui-baseline/2026-07-04/INTAKE_V6_CONFIRMATION_HANDOFF_COMPLETION_AUDIT.md`
- `docs/qa/intake-v6-order-ui-baseline/2026-07-04/INTAKE_V6_CURRENT_UI_BASELINE.md`

These documents define current owner direction for:

- Product System;
- Product Template vs Component Template;
- Form System;
- Intake V6;
- SVG Analyzer;
- Product Truth;
- ProductDefinition;
- Dossier / Blueprint;
- Component Production Operations;
- Pricing / CommercialPriceProposal;
- Quote Snapshot;
- Order Snapshot;
- ProductAggregate / Task Graph / ExecutionPlan later.

### Level 3 - Current QA / Audit Evidence

QA and audit evidence includes:

- Intake V6 screenshot baselines;
- runtime verification reports;
- current UI capture notes;
- targeted test evidence;
- worklogs that record what was read, changed, or not changed.

These documents are factual evidence, not architecture authority by themselves.

Use them to answer:

- what the UI looked like before refactor;
- which path was actually verified;
- what runtime risk was observed;
- what remained partial.

Do not use a QA artifact to override a canonical direction contract.

### Level 4 - Legacy / Archived Docs

Legacy, archived, transitional, or old worklogs may contain useful facts.

They may be used for:

- historical context;
- old route discovery;
- risk evidence;
- old decisions that need explicit supersession;
- fixture and seed origins;
- regression test intent.

They must not authorize new implementation if they contradict Level 2 canonical docs.

Conflict rule:

```text
Legacy doc conflict = STOP + owner review.
```

### Level 5 - Superseded / Dangerous Docs

A document is treated as superseded or dangerous for implementation authority if it promotes or implies:

- one-off forms;
- hardcoded form per product;
- ProductAggregate before Product Truth and snapshots;
- Task Graph before Product Truth and snapshots;
- ExecutionPlan before ProductAggregate/Task Graph and Order Snapshot;
- Pricing Registry repairing Product Truth;
- ProductDefinition guessing missing fields;
- Dossier as live runtime truth;
- Dossier as task materializer;
- QuoteWizard as current V6 canonical quote model;
- legacy Logo templates as active components;
- parallel task catalog detached from Component Templates;
- Quote/Order depending on mutable live Intake or Product System state.

These docs may be read as evidence, but they are not implementation authority.

## Canonical Wins Rule

```text
If legacy docs conflict with current canonical docs, canonical docs win.
If current runtime conflicts with canonical docs, report RUNTIME_CONFLICT.
If docs conflict with code, do not fix automatically; audit and ask owner.
If tests encode legacy behavior, mark TEST_CONFLICT before changing tests.
```

## Current Canonical Direction Summary

The current canonical direction is:

- Product System = design-time catalog / contract library.
- Product Template = product orchestrator / composition / configurator.
- Component Template = real technical unit and owner of technical fields, operations, validations, outputs.
- Strategy/Profile Source = profile over shared component, not primary component.
- Form System = composes Intake V6 form from contracts.
- Intake V6 = modular, scalable runtime workspace.
- SVG Analyzer = suggestion engine only.
- Operator/Product Truth = confirmation boundary.
- Product Truth = confirmed runtime truth before ProductDefinition and quote.
- ProductDefinition = compiler/preview, not pricing and not guessing.
- Dossier = read-only contract carrier.
- Component Production Operations = operation/task contracts in Component Templates.
- Pricing Registry = rules/coverage, not Product Truth repair.
- CommercialPriceProposal = client commercial proposal after complete truth.
- CostEngine = internal-only estimate/capacity/profitability input.
- Quote Snapshot = frozen accepted commercial truth.
- Order Snapshot = frozen accepted order truth.
- ProductAggregate / Task Graph / ExecutionPlan = later.
- Employee Mobile = final-final.

## Conflict Types

Use these labels when auditing old docs or runtime/code:

| Conflict Type | Meaning |
|---|---|
| `OLD_INTAKE_FLOW` | Old Intake V3/V4/QuoteWizard path is presented as current canonical V6 direction. |
| `OLD_FORM_HARDCODING` | Document or code encourages hardcoded form fields instead of contract composition. |
| `PRODUCTAGGREGATE_TOO_EARLY` | ProductAggregate is pushed before Product Truth and snapshots are stable. |
| `EXECUTIONPLAN_TOO_EARLY` | Task Graph, ExecutionPlan, sessions, or Employee Mobile are pushed too early. |
| `PRICING_REPAIRS_TRUTH` | Pricing Registry or pricing preview repairs missing Product Truth. |
| `PRODUCTDEFINITION_GUESSES` | ProductDefinition invents missing fields or silently defaults critical values. |
| `DOSSIER_AS_RUNTIME_TRUTH` | Dossier becomes live runtime truth or task materializer. |
| `PARALLEL_TASK_CATALOG` | Task catalog is detached from Component Templates. |
| `LEGACY_LOGO_ACTIVE` | Legacy Logo templates become active components or Work Intake roots. |
| `COMPONENT_DUPLICATION` | Similar products fork duplicate component templates instead of sharing components. |
| `QUOTE_ORDER_SNAPSHOT_RISK` | Quote/Order remains dependent on mutable Intake/Product System state. |
| `RUNTIME_CONFLICT` | Existing runtime behavior contradicts canonical direction. |
| `TEST_CONFLICT` | Tests encode legacy behavior that conflicts with canonical direction. |
| `SEED_CONFLICT` | Seeds or fixtures can reactivate old model. |
| `REGISTRY_CONFLICT` | Registry/availability data can expose forbidden roots or components. |

## Required Implementation Preflight

Before any implementation touching Product System, Intake V6, Form System, ProductDefinition, Pricing, Quote, Order, ProductAggregate, Task Graph, or ExecutionPlan:

1. Read the Level 2 canonical docs relevant to the slice.
2. Check Level 3 QA/audit evidence for current runtime behavior and UI baseline.
3. Search Level 4 legacy docs for conflicting old assumptions.
4. Search code/seeds/registries/fixtures for runtime conflicts.
5. If any conflict appears, record it and stop for owner review.
6. Do not cleanup old docs or code as part of the implementation unless explicitly scoped.

## Do Not Do

- Do not delete old docs to remove ambiguity.
- Do not edit old docs during implementation unless the task explicitly asks for docs reconciliation.
- Do not treat old docs as approval for old behavior.
- Do not treat current code as desired future architecture when it contradicts canonical docs.
- Do not weaken tests to fit the new direction.
- Do not modify seeds/registries to make a build green without owner review.
- Do not activate Logo, component quote, component root, ProductAggregate, Task Graph, ExecutionPlan, HUB, or Employee Mobile from legacy docs.

## Next Recommended Step

Use this policy together with:

`docs/architecture/WORKOS_PY_SEED_REGISTRY_RUNTIME_RISK_POLICY.md`

Before implementation, create a scoped pre-implementation audit for the target slice and classify all doc/runtime conflicts with the labels above.
