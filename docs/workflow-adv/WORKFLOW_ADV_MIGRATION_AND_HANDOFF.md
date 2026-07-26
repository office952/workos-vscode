# Workflow-ADV migration and handoff

## Decision

Workflow-ADV starts from accepted contracts and evidence in Current WorkOS, not from a wholesale application copy. Current WorkOS remains an evidence-bearing laboratory. Workflow-ADV Lab remains a controlled proving environment. Workflow-ADV Platform is the production target. Workflow-ADV Analyzer is a separate desktop application.

The migration goal is a governed Platform that preserves proven semantic boundaries while deliberately replacing laboratory UI and legacy implementation paths.

## Evidence baseline

| Item | Value |
|---|---|
| Owner-accepted evidence HEAD | `9769bbe8` |
| Documentation tip | `fd2532e1` |
| Analyzer contract | `workflow_adv_analyzer_io_contract_v1` |
| Reference flow | request → form → PD → operator-confirmed PT → quantities → catalog resources → EIC |
| EIC fixture proof | VL `923.2` |
| CPP status | reconciliation only (`1061` fixture evidence); not an offer finish line |

## Migration phases

### Phase 0 — Freeze the handoff boundary

- Pin the evidence baseline and this documentation set.
- Inventory existing paths without deleting or extending them.
- Record source artifact, authority, transfer decision, owner, and known limit.
- Stop feature expansion in Current WorkOS within the Workflow-ADV boundary.

### Phase 1 — Establish Platform foundations

- Create versioned contract handling, identity/audit, role permissions, error model, observability, and Freeze control-plane design.
- Establish typed API/domain boundaries and a test/fixture harness.
- Create role-separated navigation and the desktop-first Platform shell.
- Do not migrate template pages or calculator code as a shortcut.

### Phase 2 — Land transfer artifacts

- Transfer contract prose/types, fixture data, automated tests, proof/evidence, and provenance expectations.
- Re-express them under Platform ownership and module boundaries.
- Preserve the lab reference flow and EIC finish line.
- Validate that transferred tests retain their assertions rather than being weakened.

### Phase 3 — Implement governed product workflow

- Implement reusable Form System, Product System contracts, Product Definition/Product Truth confirmation boundary, catalog-backed resources, and EIC evidence path in the planned module order.
- Surface Analyzer payload review as a consumer-only integration.
- Implement Admin/Dev workflows only on versioned drafts and governed promotion.

### Phase 4 — Verify and accept

- Run contract, fixture, API/domain, role/authorization, accessibility, and runtime verification.
- Promote through the canonical stages.
- Owner accepts and freezes the operational version.

### Phase 5 — Retire or quarantine legacy

- Quarantine legacy paths behind explicit labels/feature routing, then remove only with a zero-reference check and owner GO.
- Preserve required audit/evidence records.
- Do not make deletion a prerequisite for Platform progress.

## Transfer, rewrite, abandon

| Category | Decision | Examples |
|---|---|---|
| Transfer | Bring semantic artifacts with provenance | product/form/PD/PT/quantity/EIC contracts; Analyzer I/O contract; governance contracts; fixtures; targeted tests; runtime proof |
| Rewrite | Rebuild as Platform-owned modules and UI | role-based IA, reusable Form System UI, Admin catalog/version workflows, audit, freeze controls, typed APIs, observability |
| Abandon / do not transfer | Keep out of Platform baseline | Lab badge chrome, legacy routes, duplicated calculators, offer/Execution finish line, central in-repo parsers, hardcoded template-code pages |
| Quarantine pending owner GO | Existing behavior may remain but is not authoritative | WorkIntake V1, existing in-repo analysis code, old dev-server/environment paths, experimental screens |

## What transfers

The following are transferable only when their source, version, and limitations are preserved:

- product template and child-composition ownership boundaries;
- reusable Form System field contract: source, destination, validation, visibility, confirmation, and formula impact;
- distinction between Product Definition (intent/draft) and Product Truth (operator-confirmed runtime fact);
- declared quantity keys, one formula owner, and no frontend business-truth recalculation;
- inventory/catalog-backed resource and `VARIANT_SELECTOR` policies;
- operational process, labor, and service contract boundaries;
- EIC breakdown semantics and explanatory evidence;
- Analyzer observed/proposed + operator confirmation model;
- promotion, Dev Mode, Freeze, lifecycle, and audit contracts;
- fixtures and tests that demonstrate those contracts, including their invalid/error cases.

## What must be rewritten

Rewrite rather than copy:

- Platform information architecture and operator-first desktop UI;
- validation/error interaction and accessibility behavior;
- module layout and dependency direction;
- API adapters and typed transport boundaries;
- Admin catalog/template/version/freeze experiences;
- observability, authorization, and audit control planes;
- implementation-specific persistence design once separately approved.

## What is intentionally out of scope

This handoff does not authorize:

- Supplier Import;
- a generic visual Form Builder or visual add-child factory;
- offer, order, Snapshot, or Execution expansion beyond a separately approved build;
- automatic pricing from RAL/Oracal or other UI registries;
- CostEngine changes;
- analyzer/parser implementation in the Platform;
- activation of future templates merely because fixtures exist;
- mobile-first/final mobile delivery.

## Initial Platform module order

Implement in this order, with each module promoted independently where practical:

1. **Foundation:** identity/roles, audit, version IDs, typed error model, observability, test fixtures.
2. **Governance:** promotion stages, Dev Mode isolation, Freeze records and owner-only unfreeze workflow.
3. **Product System:** template/composition contracts and scoped lifecycle metadata.
4. **Form System:** reusable field contract composition, valid choices, validation, provenance, confirmation requirements.
5. **Product Truth boundary:** draft Product Definition, review, operator confirmation, immutable confirmed revision.
6. **Catalog-backed resources:** material variants, processes, labor/services, provenance and ownership rules.
7. **Quantity/EIC evidence:** server/domain-owned quantities and EIC breakdown with no frontend authority.
8. **Analyzer adapter:** versioned payload validation, review UI, provenance, confirmation bridge; no parser.
9. **Operator Platform UI:** queue, request/review/confirmation, readiness/EIC, exceptions.
10. **Admin and Dev UI:** governed authoring/versioning/audit and draft-only diagnostics.

Offer, Order, Execution, and downstream planning are later modules, not implicit continuations of the EIC reference path.

## Handoff package

Each transferred module includes:

- source document and evidence commit/hash;
- canonical contract and version;
- fixture set and expected outputs;
- automated tests and runtime verification evidence;
- explicit ownership/dependency map;
- UI role impacts and accessibility requirements;
- security/authorization and audit requirements;
- legacy/deprecation decision;
- unresolved decisions and named owner.

The receiver acknowledges which artifacts are transferred, rewritten, deferred, or rejected. Unacknowledged artifacts are not silently assumed to be Platform requirements.

## Completion criteria

The handoff is complete when the Platform team can implement a module without guessing authority, data flow, confirmation, versioning, or proof obligations—and without importing a legacy route, parser, or Lab screen to fill that gap.
