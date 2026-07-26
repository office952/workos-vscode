# Linked Template Composition Contract

## 1. Purpose

A commercial product can be a composition of compatible templates.

This contract defines how WorkOS represents a root product template plus linked child, segment, support, artwork, logo, vinyl, print, lighting, mounting, or electrical templates while preserving one Intake, one runtime Product Truth, one downstream offer/order path, and future task intents without duplicate real operations.

This document does not implement Pricing, Quote, Order, Executie, ProductAggregate, Task Graph, ExecutionPlan, DB writes, seeds, or migrations.

## 2. Definitions

### Root Template

The primary commercial template for the request.

Rules:

- appears in Work Intake as root;
- controls the offer/order boundary;
- produces the root Product Truth;
- may include linked templates;
- remains the only quote root in this composition unless a separate owner GO changes that boundary.

### Linked Child Template

An internal template used as a segment, support, artwork surface, logo segment, mounted segment, vinyl/print segment, lighting segment, mounting segment, or electrical segment inside the root composition.

Rules:

- is not a separate offer in that context;
- is not root offerable in that context;
- does not produce a separate quote;
- contributes fields, materials, rules, readiness and future task intents;
- must carry source, state and Product Truth path;
- remains subordinate to the root Product Truth and downstream snapshot boundary.

### Composition Role

A template role inside a specific composition.

Allowed vocabulary:

- `root_product`
- `linked_logo_segment`
- `linked_letters_segment`
- `linked_support_panel`
- `linked_artwork_surface`
- `linked_vinyl_surface`
- `linked_lighting_segment`
- `linked_mounting_segment`
- `linked_electrical_segment`

The same template may have different roles in different products.

### Template Capability

Template capability records what a template may do in a given architecture context.

Capability fields:

- `offerable_as_root`
- `usable_as_child`
- `allowed_parent_templates`
- `allowed_child_templates`
- `allowed_composition_roles`
- `task_intent_keys`
- `merge_policy`

Capability is not runtime Product Truth. It defines allowed composition behavior.

## 3. Current Rule

For the current Intake V6 volumetric letters case:

- root: `TPL-VOLUMETRIC-LETTERS_v2`
- linked child segment: `TPL-VOLUMETRIC-LOGO_v1`
- role: `linked_logo_segment`
- UI zone: `Vector Atipic / logo`
- runtime rows: `logo stanga`, `logo dreapta`
- runtime role: `printed_artwork`
- binding status: `suggested` until explicit runtime confirmation and Product Truth mapping are complete

Rules:

- `TPL-VOLUMETRIC-LOGO_v1` is child only in this composition;
- `TPL-VOLUMETRIC-LOGO_v1` is not Work Intake root offerable in this flow;
- `TPL-VOLUMETRIC-LOGO_v1` does not create a separate quote;
- `TPL-VOLUMETRIC-LOGO_v1` does not create a separate order;
- `TPL-VOLUMETRIC-LOGO_v1` does not activate component quote/root behavior;
- Logo segments contribute source/state/Product Truth requirements under the Letters root.

## 4. Future ACM Rule

Example: `TPL-ACM-CASETAT_v1` may be:

- root product when selling a simple ACM panel;
- `linked_support_panel` when used as support/base for volumetric letters;
- `linked_artwork_surface` when it carries vinyl, print, or applied graphics;
- part of a larger composition with linked letters, linked logo, vinyl, print, and mounting requirements.

The template identity can stay the same while the composition role changes by context.

## 5. Unified Intake Rule

Form System must produce one coherent form for the full composition.

Rules:

- no separate form per child template;
- no duplicated common fields;
- child-specific fields appear only when required by the current composition;
- source/state must remain explicit;
- operator confirmation boundary must remain visible;
- SVG Analyzer suggestions do not become final Product Truth by themselves;
- fallback or hydrated values do not become confirmed Product Truth by themselves.

## 6. Product Truth Rule

Product Truth for a linked composition must include:

- root path;
- linked template path;
- segment id or layer key;
- owning template;
- owning component;
- source type;
- state;
- blockers.

Conceptual path example:

```text
linked_templates.logo.segments.logo-stanga
```

The runtime source of segment keys is the Intake V6 workspace payload, not the static Form System backbone service.

## 7. Task Intent / No Duplicate Task Rule

This contract does not implement Task Graph.

Rule:

- templates may emit future task intents;
- task intents will be unified later by an owner-approved task composer;
- identical real operations must be merged;
- specific operations remain separate only when they represent genuinely different work;
- multiple templates must not create duplicate tasks just because multiple templates exist.

Example: ACM + letters + logo + vinyl/print may later produce coherent intents for:

- prepare ACM support;
- apply vinyl/print to support;
- produce volumetric letters;
- produce logo segment;
- mount letters/logo on support;
- final assembly verification.

It must not produce four unrelated mounting tasks without a real operational reason.

## 8. Runtime Linked Segment Extraction

The static `linked_template_composition` contract declares that a root template can own linked child templates. Runtime payload extraction discovers which real segments exist in a specific Intake V6 workspace.

For the current `TPL-VOLUMETRIC-LETTERS_v2` workspace, runtime segment extraction reads:

- `payload.layer_role_setup.layers`
- `payload.layer_role_setup.layer_bindings`
- `payload.finish_setup.artwork_finishes`

Current discovered logo segments:

- `logo-stanga`
- `logo-dreapta`

Rules:

- `logo-stanga` and `logo-dreapta` remain part of root product `TPL-VOLUMETRIC-LETTERS_v2`;
- their owning linked child template is `TPL-VOLUMETRIC-LOGO_v1`;
- their composition role is `linked_logo_segment`;
- their layer role is `printed_artwork`;
- layer role confirmation, artwork finish confirmation, and template binding status are separate states;
- `binding_status=suggested` must remain suggested and must not become root offerability;
- artwork finish `confirmed=true` does not mean Logo has a separate quote or order;
- Product Truth readiness is not the same thing as the UI `OK` badge;
- no separate quote, order, task graph, execution plan, or task materialization is created by extraction.

Runtime extraction output is read-only and may report:

- segment key and display name;
- parent root template code;
- owning linked template code;
- composition role;
- confirmed layer role;
- binding status and reason;
- source paths inside runtime payload;
- finish values and finish confirmation;
- conceptual Product Truth path;
- quote policy and future task merge policy;
- summary counts for confirmed segments, suggested bindings, missing finishes, and missing bindings.

The extraction helper must not invent missing segments. If a layer or binding exists but finish data is missing, it reports `missing_finish` instead of creating a false confirmation.

## 9. Forbidden

- child template does not become root without owner GO;
- child template does not create separate quote without owner GO;
- no Pricing changes in this slice;
- no Quote/Order changes in this slice;
- no Executie changes in this slice;
- no ProductAggregate implementation in this slice;
- no Task Graph implementation in this slice;
- no ExecutionPlan implementation in this slice;
- no DB writes, seeds, or migrations in this slice.

## 10. Current Implementation Boundary

This slice implements only read-only contract mapping in Form System Backbone.

Implemented boundary:

- declares `linked_template_composition` for `TPL-VOLUMETRIC-LETTERS_v2`;
- declares `TPL-VOLUMETRIC-LOGO_v1` as `linked_logo_segment`;
- declares `no_separate_quote`;
- declares root offerability blocked for the child in this flow;
- declares no duplicate task policy as documentation/contract only;
- keeps downstream write intent all false.

Not implemented:

- Task Composer;
- ProductAggregate;
- Task Graph;
- ExecutionPlan;
- Pricing merge;
- quote/order merge;
- runtime segment extraction;
- DB schema;
- seeds or migrations.

Runtime extraction V1 adds only a backend helper and tests. It does not add an endpoint, does not change UI, and does not connect to Pricing, Quote/Order, Executie, ProductAggregate, Task Graph, ExecutionPlan, DB, seeds, or migrations.

## 11. Linked Segment Diagnostic Endpoint

Runtime linked segments may be exposed through a read-only diagnostic workspace endpoint:

```text
GET /api/v1/intake-v6/workspaces/{workspace_id}/linked-template-segments
```

Purpose:

- answer which linked runtime segments are detected for this workspace;
- show how those segments relate to the root and linked child templates;
- expose source/state/Product Truth mapping diagnostics;
- preserve downstream safety.

Payload sources:

- `payload.layer_role_setup.layers`
- `payload.layer_role_setup.layer_bindings`
- `payload.finish_setup.artwork_finishes`
- static `linked_template_composition` from the root Form System Backbone

State interpretation:

- `binding_status=suggested` means the layer has a proposed linked template target; it is not root offerability and not a separate quote;
- segment `state=confirmed` means the runtime layer role and artwork finish row are confirmed in the workspace payload;
- `state=confirmed` is not full Product Truth completion while template binding is still `suggested`;
- UI `OK` for artwork remains row-level confirmation, not final product/quote/order/execution readiness.

Forbidden effects:

- no Product Truth write;
- no Pricing;
- no Quote/Order;
- no Executie;
- no ProductAggregate;
- no Task Graph;
- no ExecutionPlan;
- no DB write;
- no Logo root activation;
- no separate Logo quote;
- no component quote/root.

Future use:

- feed a read-only Product Truth readiness diagnostic for linked segments;
- help UI diagnostics explain why `logo-stanga` / `logo-dreapta` are linked child segments under the Letters root;
- later inform task intent merge design without materializing tasks in Intake V6.

## 12. Product Truth Readiness for Linked Segments

Linked segment readiness is stricter than row-level artwork confirmation.

Rules:

- UI `OK` means the artwork row is confirmed; it does not mean full Product Truth readiness;
- layer role confirmation, finish/artwork confirmation, and linked template binding confirmation are separate states;
- `finish.confirmed=true` does not unlock Pricing, Quote, Order, Executie, ProductAggregate, Task Graph, or ExecutionPlan;
- `binding_status=suggested` produces `product_truth_readiness.status=partial`;
- full linked segment Product Truth readiness requires an explicit linked template binding confirmation path;
- this readiness layer is diagnostic and read-only; it does not write Product Truth.

Current runtime for `logo-stanga` / `logo-dreapta`:

- layer role confirmed: DA, `printed_artwork`;
- finish/artwork confirmed: DA;
- linked template binding confirmed: NU, `binding_status=suggested`;
- readiness status: `partial`;
- required confirmation: `confirm_linked_template_binding`;
- blocker/warning: `LINKED_TEMPLATE_BINDING_SUGGESTED`.

Readiness output may appear per segment:

```json
{
	"status": "partial",
	"is_ready": false,
	"reason": "template_binding_suggested",
	"ready_for_pricing": false,
	"ready_for_quote": false,
	"ready_for_order": false,
	"ready_for_execution": false,
	"confirmed_as_artwork": true,
	"finish_confirmed": true,
	"layer_role_confirmed": true,
	"template_binding_confirmed": false,
	"binding_status": "suggested",
	"required_confirmation": "confirm_linked_template_binding",
	"product_truth_path": "linked_templates.TPL-VOLUMETRIC-LOGO_v1.segments.logo-stanga"
}
```

Summary readiness remains downstream-safe:

- `pricing_ready=false`;
- `quote_ready=false`;
- `order_ready=false`;
- `execution_ready=false`.

Even if a future segment reaches `status=ready`, this slice still does not activate downstream systems. Readiness is an explanation layer, not a workflow trigger.