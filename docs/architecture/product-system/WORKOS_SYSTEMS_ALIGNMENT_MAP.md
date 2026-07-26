# WorkOS Systems Alignment Map

## Status

- Date: 2026-07-04 (ownership amendment 2026-07-20)
- Status: CANONICAL_DIRECTION — **External Artwork Analysis Ownership** supersedes in-WorkOS SVG/DWG/DXF analysis responsibility
- Ownership amendment: [`docs/architecture/artwork-understanding/2026-07-20_EXTERNAL_ARTWORK_ANALYSIS_OWNERSHIP.md`](../artwork-understanding/2026-07-20_EXTERNAL_ARTWORK_ANALYSIS_OWNERSHIP.md)
- Push: NONE

This document aligns the WorkOS system boundaries before implementation. It explains roles, sources of truth, handoff points, and forbidden responsibility leaks between Product System, Form System, Intake V6, **external desktop artwork analysis** (replacing WorkOS-owned SVG Analyzer responsibility), Product Truth, ProductDefinition, Quote, Order, and downstream execution systems.

It does not authorize UI work, backend work, frontend work, tests, seed changes, migrations, pricing changes, Quote changes, Order changes, ProductAggregate changes, ExecutionPlan changes, HUB activation, or Employee Mobile work.

## Purpose

This map answers the owner-level questions:

- What role does each system have?
- Who is source of truth for what?
- How does Product System connect to Form System?
- How is the Intake V6 form created?
- Must Intake V6 be modular and scalable?
- How do we avoid one separate form per Product Template?
- How do we avoid one separate form per Component Template?
- Where does SVG Analyzer fit?
- Where is final data confirmed?
- Where are Product Truth and future Component Truth produced?
- What must UI, ProductDefinition, and Pricing not do?
- How do Quote Snapshot and Order Snapshot remain protected?

## Canonical End-To-End Flow

```text
Desktop Analysis App (external — owns SVG/DWG/DXF intelligence)
-> External structured result (observed / proposed only)
-> Work Intake
-> Product System template selection
-> Intake V6 workspace (consume + review surface)
-> Form System contract composition
-> Operator review and confirmation
-> Product Truth
-> ProductDefinition compiler
-> CommercialPriceProposal / Offer
-> Quote Snapshot
-> Order Snapshot
-> ProductAggregate later
-> Task Graph later
-> ExecutionPlan later
-> Workcenters / Utilaje later
-> Employees / Skills / Capacity later
-> ExecutionReality later
-> Employee Mobile final-final
```

Current default root:

```text
root_type = product_template
root_template_code = TPL-VOLUMETRIC-LETTERS_v2
quote_mode = product_total
```

Future optional root, only after separate owner GO:

```text
root_type = component_template
root_template_code = TPL-VOLUM-ALUMINIU_v1 or TPL-VOLUMETRIC-FACE_v1
quote_mode = component_only
```

## Systems Overview Table

| System | Role | Source Of Truth For | Consumes | Produces | Must Not Do | Current Status | Future Status |
|---|---|---|---|---|---|---|---|
| 1. Work Intake | Captures request entry and initial product intent | Request context and selected offerable product candidate | Client request, selected template | Intake V6 workspace entry | Expose non-offerable templates or components as quote roots | PARTIAL / PRODUCT_TEMPLATE_ONLY | Can route to more roots after owner GO |
| 2. Product System | Design-time catalog and template/component contract library | What products/components can exist; allowed modules; shared component contracts | Owner configuration, templates, dossiers, module links | Product Template and Component Template contracts | Capture runtime truth or repair missing Intake data | PARTIAL / CANONICAL_DIRECTION | Stronger reusable component contract carrier |
| 3. Product Template | Product-level orchestrator/composition/configurator | Product composition, required/optional components, Work Intake availability | Component Templates, strategy profiles, owner rules | Product-level contract for Form System and ProductDefinition | Duplicate component logic or copy all fields manually | ACTIVE for `TPL-VOLUMETRIC-LETTERS_v2`; Logo candidate | Scalable parent over shared components |
| 4. Component Template | Reusable technical unit | Component fields, materials, operations, validations, outputs, calculation readiness | Product Template context, SVG suggestions, Form input | Component contract and future Component Truth requirements | Become offerable automatically or replace product root now | READ_ONLY / PARTIAL | Future calculable or offerable with explicit GO |
| 5. Strategy / Profile Source | Product-specific behavior over shared component | Product-specific strategy/config without forking component | Shared Component Template, Product Template profile | Strategy keys and required truth notes | Pretend to be the primary shared component | PARTIAL; Logo lighting strategy source exists | Explicit profile layer for reusable components |
| 6. Dossier / Blueprint | Design-time contract carrier | Read-only guidance for modules, sections, readiness, task rules, risks | Product Template, component links, owner docs | Dossier sections and aggregate preview guidance | Act as live runtime truth or create tasks directly | PARTIAL product-centric | Product and component dossiers after owner GO |
| 7. Form System | Modular form composition engine | Which fields/questions are needed and where each value comes from | Product Template root, active Component Templates, overrides, strategy profiles, SVG suggestions | Field contract, sections, blockers, confirmation requirements | Hardcode one-off forms or invent business fields in UI | PARTIAL / read-only contract plus runtime coupling | Canonical composer for product and component roots |
| 8. Intake V6 Workspace | Runtime workspace for the real request | Draft runtime capture state before final confirmation | Work Intake, Product System binding, SVG output, Form fields | Product Truth candidate, readiness, blockers, warnings | Become Product System catalog or pricing engine | ACTIVE / PARTIAL; product-template oriented | Modular/scalable workspace over Form System contracts |
| 9. External Artwork Analysis (desktop app) | File intelligence owner (SVG/DWG/DXF/geometry/groups/…) | Observed entities, measurements, proposed bindings | Graphic files outside WorkOS | Versioned external result (`artwork_analysis_contract_v1`) | Write Product Truth, price, unlock quote, become authority without operator | LEGACY in-repo analyzers still run — **do not extend**; ownership EXTERNAL_APP_OWNED | WorkOS consume/review/confirm only; transport TBD |
| 10. Operator Review | Human confirmation boundary | Accepted decisions for ambiguous product data | SVG suggestions, Form fields, previews | Confirmed values, manual overrides, explicit blockers resolved | Approve hidden defaults without visible state | ACTIVE / PARTIAL | Stronger suggested/confirmed/fallback separation |
| 11. Product Truth | Canonical confirmed runtime product state | Complete accepted product truth for a specific request | Intake workspace, Form System, operator confirmation, derived values | Product-level truth with component truth slices | Store guesses as final truth | DOCUMENTED_TARGET / CURRENT_CODE_PARTIAL | Required source before quote/order/execution |
| 12. Component Truth | Future canonical confirmed component state | Accepted truth for one requested Component Template root | Component form, SVG suggestions, operator confirmation | Component-only truth and readiness | Accidentally produce a full product or quote now | FUTURE / NOT_ACTIVE | Needed before component-only calculation or offer |
| 13. ProductDefinition | Compiler from truth + template to technical definition | Derived active modules, canonical values, readiness, missing fields | Product Truth, template, form contract, aggregate | Read-only ProductDefinition preview/snapshot | Price, write quote/order, invent missing fields, run execution | VALIDATED preview; product-template oriented | Component-root support only after GO |
| 14. Pricing Registry | Admin registry for rules/prices/classifications | Material prices, commercial rules, internal cost rules, capacity checks | Owner/admin entries, material maps | Rule lookups and coverage status | Repair Product Truth, decide layer/finish/support, quote by client hourly tariff | TARGET / MIXED LEGACY RISK | Separated tabs/classes with snapshot use |
| 15. CostEngine / EstimatedInternalCost | Internal estimate and margin/capacity confidence | Internal cost, materials, operations, capacity estimates | ProductDefinition/ProductAggregate, internal rules | Estimated internal cost and warnings | Decide client commercial price or block truth completion | ACTIVE / internal-only boundary documented | Better separated from commercial price |
| 16. CommercialPriceProposal / Offer | Client-facing commercial proposal | Commercial price proposal from complete truth and rules | Product Truth, ProductDefinition, Pricing Registry commercial rules | Commercial lines/totals and offer readiness | Repair missing Product Truth or use internal minutes as client price | PARTIAL / boundary canonical | Unit-based commercial proposal after truth completeness |
| 17. Quote Snapshot | Freeze accepted commercial truth | Accepted offer truth at quote time | Commercial proposal, ProductDefinition snapshot, Product Truth | Frozen quote snapshot | Depend on mutable Product System or live Intake workspace after acceptance | CANONICAL_DIRECTION | Strong freeze before order |
| 18. Order Snapshot | Freeze accepted order truth | Accepted order truth for downstream production | Quote Snapshot and accepted product configuration | Frozen order truth | Re-read mutable Product System/Intake to change accepted order | CANONICAL_DIRECTION | Source for ProductAggregate/Execution |
| 19. ProductAggregate / Task Graph / ExecutionPlan | Downstream technical graph and execution planning | Technical graph, task DAG, scheduling after snapshot | Order Snapshot, ProductDefinition snapshot, modules | Aggregate, tasks, execution plan | Fill missing intake truth or start before snapshots are stable | LATER / FORBIDDEN_NOW | Only after Product Truth and snapshots are stable |
| 20. ExecutionReality / Employee Mobile | Actual production capture and mobile execution | Actual time/materials/status after order execution | ExecutionPlan, employee work, material usage | Actuals and profitability learning | Rewrite accepted quote or act before execution model is stable | FINAL-FINAL | Post-job learning and mobile task execution |

## 1. Work Intake

Work Intake is the request entry layer. It captures request context and initial product intent, then routes the request into Intake V6 only when the selected template is allowed for quoting.

Current rule:

- only `quote_offerable` Product Templates enter Work Intake;
- `TPL-VOLUMETRIC-LETTERS_v2` is the active offerable root;
- `TPL-VOLUMETRIC-LOGO_v1` remains candidate;
- Component Templates are not Work Intake roots now.

Work Intake must not expose candidate products, runtime modules, shared components, or future component roots as quoteable choices without explicit owner GO.

## 2. Product System

Product System is the design-time catalog and architecture library. It owns product and component definitions at contract level: template identity, module links, shared component usage, allowed options, role metadata, dossier direction, and readiness metadata.

Product System is source of truth for what can exist, not for what the customer actually requested in a specific job.

It must not:

- capture runtime Product Truth;
- override missing Intake values;
- repair incomplete forms;
- calculate final quote price;
- mutate accepted Quote or Order snapshots.

## 3. Product Template

A Product Template is the product-level orchestrator. It selects, configures, and composes Component Templates into one product.

For `TPL-VOLUMETRIC-LETTERS_v2`, the Product Template consumes shared volumetric components such as face, back, return/cant, finish, mounting/structure, and LED.

A Product Template may:

- include or exclude components;
- mark components required or optional;
- apply product-level overrides;
- group questions for operator UX;
- apply strategy/profile sources;
- define Work Intake availability.

A Product Template must not manually duplicate every Component Template field. Duplication would create a separate form per product and break scalability.

## 4. Component Template

A Component Template is the reusable technical unit. It owns component-level requirements: fields, materials, allowed variants, operations, validations, blockers, outputs, and future calculation readiness.

Examples:

- `TPL-VOLUMETRIC-FACE_v1` owns face component requirements;
- `TPL-VOLUM-ALUMINIU_v1` owns return/cant requirements;
- `TPL-VOLUMETRIC-LED_v1` owns shared lighting direction.

Component Templates are not quote roots now. They may become `calculable` or `offerable` only through a separate owner-approved path.

## 5. Strategy / Profile Source

A Strategy / Profile Source profiles a shared component for a product-specific context.

Example:

- primary shared lighting component: `TPL-VOLUMETRIC-LED_v1`;
- Logo lighting strategy/profile source: `TPL-VOLUMETRIC-LOGO-LIGHTING_v1`.

The strategy source is not the primary shared component. It must not activate Logo as offerable and must not create component quote behavior.

## 6. Dossier / Blueprint

The Dossier is the design-time contract carrier. It can expose product/component composition, sections, variants, task rules, readiness notes, risks, and production guidance.

Current state is product-centric and partial. Dossier and Blueprint Studio can support Product Template views and aggregate previews, but complete independent Component Template Dossier behavior remains future.

The Dossier must not be treated as live runtime truth, a pricing engine, a task materializer, or an order mutator.

## 7. Form System

Form System is the modular composition engine. It turns template contracts into the questions and confirmation requirements shown inside Intake V6.

The Form System composes the Intake V6 form from:

- root Product Template;
- active Component Templates;
- component required fields;
- product-level overrides;
- strategy/profile source requirements;
- external artwork analysis suggestions (consumed contract; legacy `svg_analyzer_suggestion` alias);
- readiness rules;
- operator confirmation requirements.

Every field must have a source:

- `component_template`;
- `product_template_override`;
- `strategy_profile`;
- `external_artwork_suggestion` (legacy alias: `svg_analyzer_suggestion`);
- `operator_manual_input`;
- `system_derived_value`.

The Form System is the answer to avoiding one-off forms.

## 8. Intake V6 Workspace

Intake V6 is the runtime workspace for a real request. It hosts SVG upload, layer review, form sections, readiness, blockers, warnings, and operator confirmation.

Current state:

- product-template oriented;
- `TPL-VOLUMETRIC-LETTERS_v2` is the active root;
- layer role and finish readiness gates exist;
- many Product Truth contracts are still partial/transitional.

Intake V6 must become more modular by consuming Form System contracts, not by becoming a new hardcoded form per product.

## 9. External Artwork Analysis (desktop app)

**Ownership (2026-07-20):** A separate desktop application owns all graphic-file intelligence (SVG/DWG/DXF import, geometry, layers, groups, measurements, classification, auto-grouping, mapping proposals). WorkOS must not implement or extend in-repo analyzers for those duties. See [`EXTERNAL_ARTWORK_ANALYSIS_OWNERSHIP`](../artwork-understanding/2026-07-20_EXTERNAL_ARTWORK_ANALYSIS_OWNERSHIP.md).

The desktop app may emit (as **observed** / **proposed** only):

- face / artwork entity candidates;
- area / perimeter / dimensions;
- color/material clues;
- suggested bindings;
- blockers/warnings.

It must not:

- decide final Product Truth;
- decide Component Truth;
- decide finish, support, mounting, or electrical truth;
- decide price;
- unlock quote;
- bypass operator confirmation.

Canonical rule:

```text
Desktop analysis app observes / proposes (external).
WorkOS consumes + validates (no Product Truth write).
Form System asks missing inputs.
Operator confirms.
Product Truth stores accepted truth + analysis reference provenance.
```

## 10. Operator Review

Operator Review is the confirmation boundary. It converts suggestions, fallbacks, hydrated values, and manual inputs into accepted Product Truth.

The UI must show different states for:

- suggested;
- needs confirmation;
- needs form input;
- fallback or hydrated;
- operator confirmed;
- blocked;
- warning;
- ready for quote/order/execution.

The UI may present friendly layout, sections, labels, and controls. It must not invent fields, hide blockers, or make fallback values look confirmed.

## 11. Product Truth

Product Truth is the canonical confirmed runtime product state for a specific request.

For Product Template root, Product Truth contains:

- root template;
- confirmed geometry;
- layer roles;
- active component truth slices;
- field source and state;
- manual inputs;
- derived values;
- blockers;
- warnings;
- readiness.

Product Truth is produced by Intake V6 through Form System and operator confirmation. It is not produced by Pricing Registry, ProductDefinition, CostEngine, Quote, or Order.

## 12. Component Truth

Component Truth is future. It is the confirmed runtime truth for a single Component Template root.

For example, if `TPL-VOLUM-ALUMINIU_v1` becomes a component root later, Component Truth would include return/cant inputs only: perimeter, depth, material, finish, dependencies, readiness, blockers, and outputs for that component.

Current rule:

- Component Truth is not active;
- component-root Intake is not active;
- component quote is not active;
- component order is not active.

## 13. ProductDefinition

ProductDefinition is a compiler. It consumes confirmed truth and template contracts, then derives active modules, inactive modules, canonical values, missing fields, readiness, materials, operations, and validation.

ProductDefinition must fail closed on missing critical fields.

It must not:

- calculate commercial price;
- write quote;
- write order;
- write DB snapshots directly;
- invent missing fields;
- repair Product Truth;
- create tasks or execution plans;
- silently default critical data.

Current implementation is read-only preview and product-template oriented.

## 14. Pricing Registry

Pricing Registry stores classified rules and reference data: material prices, commercial rules, internal cost rules, capacity checks, effort thresholds, and analytics entries.

Pricing Registry may report missing commercial coverage after Product Truth is complete.

It must not repair:

- layer roles;
- selected layer;
- finish target;
- support decision;
- mounting truth;
- electrical truth;
- ProductDefinition blockers.

Pricing Registry is not Product Truth and must not become a hidden form.

## 15. CostEngine / EstimatedInternalCost

CostEngine and EstimatedInternalCost are internal-only. They estimate material/internal operation cost, capacity, margin confidence, and later profitability context.

They must not become the client-facing commercial formula and must not turn internal minutes into automatic client hourly price.

Missing internal-only effort data may reduce confidence, but it must not be disguised as missing Product Truth.

## 16. CommercialPriceProposal / Offer

CommercialPriceProposal is the client-facing proposal layer. It consumes complete Product Truth, ProductDefinition, and commercial pricing rules.

It produces commercial lines and totals for the client.

It must not:

- repair Product Truth;
- decide missing finish/support/electrical fields;
- use CostEngine minutes as primary client price;
- produce a final quote from unconfirmed SVG suggestions.

## 17. Quote Snapshot

Quote Snapshot freezes accepted commercial truth at quote time.

It must include enough frozen context to protect the accepted offer from later changes in:

- Product System;
- Product Template;
- Component Template;
- Dossier;
- Intake V6 workspace;
- SVG Analyzer improvements;
- Pricing Registry changes after acceptance.

Quote Snapshot must not remain live-bound to mutable Product System or Intake V6 state.

## 18. Order Snapshot

Order Snapshot freezes accepted order truth after quote acceptance.

Order Snapshot protects downstream production from mutable design-time and intake-time systems.

Order must not re-read live Product System or live Intake workspace to change accepted truth. If a template changes later, the accepted order stays on its snapshot.

## 19. ProductAggregate / Task Graph / ExecutionPlan

ProductAggregate, Task Graph, and ExecutionPlan are downstream systems. They must come after Product Truth, ProductDefinition, Quote Snapshot, and Order Snapshot are stable.

They may later produce:

- technical graph;
- task DAG;
- operation/workcenter planning;
- scheduling and execution plans.

They must not fill missing Intake truth, infer missing product decisions, or start before snapshot boundaries are stable.

## 20. ExecutionReality / Employee Mobile

ExecutionReality captures actual production results after order execution. Employee Mobile is final-final after ExecutionPlan and actuals flow are stable.

They may capture:

- actual task time;
- material usage;
- employee assignment;
- work status;
- variance and profitability feedback.

They must not rewrite accepted quote price or change accepted order truth retroactively.

## Intake V6 Modularity Verdict

Intake V6 must be modular: YES.

Intake V6 must be scalable: YES.

The scalable model is:

```text
Intake V6 shell
+ Form System composer
+ Product Template root
+ active Component Template field contracts
+ SVG Analyzer suggestions
+ operator confirmation
= Product Truth
```

The non-scalable model is forbidden:

```text
One custom form per product
One copied field set per product
One duplicated component implementation per similar product
One hidden UI decision per field
```

Current Intake V6 is already a real runtime workspace with useful Straturi / Review / Confirmare flow. The correct direction is to preserve that shell and modularize its questions through Form System contracts.

## Form System Scalability Rule

One form per Product Template: NO.

One form per Component Template: NO.

One Form System that composes questions from contracts: YES.

The Form System prevents duplication by using reusable Component Template field contracts. Product Templates select and configure components, while Component Templates carry their own requirements.

Product-specific differences belong in:

- product-level overrides;
- strategy/profile sources;
- activation rules;
- question grouping;
- UX order;
- readiness policy.

They do not belong in copied fields or separate hardcoded forms.

## Canonical Examples

### Product Template Root: `TPL-VOLUMETRIC-LETTERS_v2`

Current active flow:

```text
Work Intake
-> Intake V6 product-template workspace
-> SVG Analyzer suggests geometry/layer roles
-> Form System asks face/back/cant/finish/LED/mounting questions
-> Operator confirms
-> Product Truth
-> ProductDefinition
-> CommercialPriceProposal / Quote Snapshot
```

The form is composed from the product root and active components:

- face;
- back;
- return/cant;
- finish;
- mounting/structure;
- lighting.

### Candidate Product Template: `TPL-VOLUMETRIC-LOGO_v1`

Logo may share the same foundation components, but it is not Work Intake offerable now.

Logo differences belong in product config and strategy/profile sources, especially lighting strategy, not duplicated active Logo-specific component templates.

### Future Component Template Root: `TPL-VOLUM-ALUMINIU_v1`

Future only:

```text
Component Template root
-> component form
-> Component Truth
-> component ProductDefinition preview
-> component-only calculation/offer only after GO
```

It must calculate only return/cant, not a whole volumetric product.

## Legacy Logo Safety

Legacy Logo-specific templates must not reappear as active shared-model components:

- `TPL-VOLUMETRIC-LOGO-FACE_v1`
- `TPL-VOLUMETRIC-LOGO-BACK_v1`
- `TPL-VOLUMETRIC-LOGO-RETURN_v1`
- `TPL-VOLUMETRIC-LOGO-FINISH_v1`
- `TPL-VOLUMETRIC-LOGO-MOUNTING_v1`

They may remain hidden, deprecated, historical, or reserved metadata until a separate zero-reference audit and owner decision.

`TPL-VOLUMETRIC-LOGO-LIGHTING_v1` is a strategy/profile source over shared LED direction, not the primary shared LED component and not an offerable root.

## No-Regression Rule

Do not break the existing preserved spine:

```text
Work Intake / Intake
-> Intake V6 workspace
-> Product Truth
-> ProductDefinition
-> Offer / Quote
-> Quote Snapshot
-> Order Snapshot
```

The alignment direction strengthens this spine. It does not replace it.

Do not regress:

- Straturi / Review / Confirmare as the Intake V6 base;
- suggested vs confirmed separation;
- Product Truth before quote;
- ProductDefinition as no-pricing compiler;
- Quote Snapshot freeze;
- Order Snapshot freeze;
- CostEngine internal-only boundary;
- Pricing Registry not repairing truth gaps.

## What This Document Does Not Authorize

This document does not authorize:

- UI implementation;
- backend implementation;
- frontend implementation;
- test changes;
- seed changes;
- DB migration;
- runtime changes;
- code cleanup;
- UI cleanup;
- component-root Intake activation;
- component quote activation;
- Logo Work Intake activation;
- pricing changes;
- CostEngine changes;
- CommercialPriceProposal changes;
- Quote Snapshot changes;
- Order Snapshot changes;
- ProductAggregate changes;
- Task Graph changes;
- ExecutionPlan changes;
- HUB;
- Employee Mobile;
- deletion of legacy Logo templates;
- `git add .`;
- commit;
- push.

## Next Recommended Step

Owner review of this alignment map.

After review, the safest next docs-only contract is:

`PRODUCT_SYSTEM_FORM_SYSTEM_COMPOSITION_CONTRACT.md`

That follow-up should define the Form System contract model in detail:

- form root types;
- field source schema;
- component field ownership;
- product overrides;
- strategy/profile fields;
- SVG suggestion bindings;
- operator confirmation states;
- Product Truth output mapping;
- validation/blocker taxonomy;
- no one-off form rules.

No implementation should start until owner confirms this map and selects the next boundary.
