# Component-Owned Truth Before Component Calculation Contract

## 1. Purpose

This document defines the required truth boundary that must exist before any future component-scoped calculation preview can be treated as real component calculation.

This is a docs-only contract. It does not implement runtime code, UI, API endpoints, Product Truth write behavior, Pricing, Quote, Order, Execution, ProductAggregate, TaskGraph, ExecutionPlan, DB writes, seeds, or migrations.

## 2. Core Rule

Mandatory rule:

```text
A component can be calculated separately only if its required calculation inputs are owned by that component's truth boundary.
```

Forbidden shortcut:

```text
Do not calculate a component by secretly reading product-level truth and calling it component calculation.
```

Permitted rule:

```text
A component may use product-level context as context only, but required calculation inputs must be mapped into component-owned truth paths with source/state.
```

Example:

```text
return_cant.perimeter_source = face.confirmed_perimeter
```

This dependency is allowed only if it is explicit, traceable, and remains outside any hidden product-template-only shortcut.

## 3. Why Component-Owned Truth Comes Before Component Calculation

Component-scoped preview contract already exists as a future boundary, but preview scope alone is not enough.

If the real required inputs still live only in the product root or only in UI defaults, then the system is still doing product-level calculation with filtered display, not component calculation.

Component calculation requires:

- explicit ownership;
- explicit Product Truth path;
- explicit source/state;
- explicit blockers;
- explicit dependency trace when another component provides upstream geometry or context.

Without that, the preview can still be useful, but it is not yet technically honest enough to be called component calculation.

## 4. Product Template Responsibilities

Product Template may own:

- product root identity;
- offerable/root boundary;
- component list;
- component order;
- required versus optional components;
- component compatibility rules;
- high-level composition;
- linked child relationships;
- orchestration and runtime availability in Work Intake.

Product Template may provide defaults only if:

- the value is explicitly marked as default;
- the value is surfaced with `fallback` or `hydrated` state;
- operator confirmation or override remains possible;
- the receiving Product Truth path belongs to the component, not to the product root as final truth.

Product Template must not own as final technical truth:

- face material;
- face thickness;
- return depth;
- return material/profile;
- back material;
- LED count;
- PSU count or sizing basis;
- finish target;
- print_required;
- lamination_required;
- support_required;
- support_type;
- component operation readiness;
- component calculation inputs.

## 5. Component Template Responsibilities

Component Template and its runtime Component Truth boundary are responsible for:

- component-specific fields;
- required inputs;
- material choices;
- dimensions and geometry needed by that component;
- operations relevant to that component;
- validations;
- blockers;
- outputs;
- calculation readiness;
- source/state for every value;
- Product Truth paths.

Canonical interpretation:

```text
Product Template composes.
Component Template owns technical truth.
Component calculation becomes valid only after truth ownership is explicit on the component side.
```

## 6. Product Truth Component Paths

Current read-only evidence already shows real component paths, but not all are equally mature.

Existing or emerging component-owned paths include:

- `components.face.*`
- `components.return.*`
- `components.back.*`
- `components.finish.*`
- `components.artwork.*`
- `components.lighting.*`
- `components.electrical.*`
- `components.support.*`
- `components.mounting.*`
- `linked_templates.logo`

Current path rules:

- a path counts as component-owned only if it has clear owner, source/state, and blocker semantics;
- a path does not become calculation-ready merely because ProductDefinition can consume it;
- derived bridges must stay explicit as dependencies, not hidden ownership.

## 7. Source/State Requirements

Every calculation-relevant component input must expose:

- owner component;
- source kind;
- state;
- Product Truth path;
- blocker or warning when incomplete;
- confirmation requirement when not yet confirmed.

Minimum source/state vocabulary for this contract:

- `suggested`
- `hydrated`
- `fallback`
- `manual`
- `confirmed`
- `blocked`
- `warning`
- `derived_dependency`
- `ui_only`
- `product_definition_only`

Interpretation rules:

- `suggested` is not enough for calculation;
- `hydrated` is not enough for calculation by itself;
- `fallback` is not enough for calculation by itself;
- `derived_dependency` is allowed only if source and upstream owner are explicit;
- `ui_only` values do not count as component-owned truth;
- `product_definition_only` values do not count as owned input truth; they are downstream consumption artifacts.

## 8. Component Truth Readiness Levels

### `TRUTH_MISSING`

Component does not have the fields required for calculation.

### `TRUTH_SUGGESTED_ONLY`

Component has only analyzer/SVG suggestions and no confirmed or durable owned truth.

### `TRUTH_HYDRATED_OR_FALLBACK`

Component has values populated, but they are still defaults, reused state, or UI hydration without confirmed ownership.

### `TRUTH_PARTIAL_CONFIRMED`

Some required inputs are confirmed and component-owned; others are still missing, fallback, hydrated, or only implied.

### `TRUTH_COMPONENT_OWNED_READY`

All minimum preview inputs exist on component-owned truth paths with explicit owner, source/state, blockers, and dependency trace where needed.

### `TRUTH_COMPONENT_CALCULATION_READY`

Component has enough owned truth for read-only calculable preview without root change or quote mode change.

Important clarification:

`TRUTH_COMPONENT_CALCULATION_READY` does not mean:

- component root;
- component quote;
- official price;
- order;
- execution;
- task materialization.

## 9. Component-by-Component Truth Requirements

### Face

Component-owned truth required:

- geometry, area, and perimeter relevant to face;
- face material;
- face thickness;
- face finish target;
- layer/group ownership;
- source/state for every value.

Not enough:

- product template default face material;
- hydrated UI material only;
- ProductDefinition-inferred face material.

Current strongest issue:

- face material and thickness still rely too much on fallback values before explicit confirmation.

### Return / cant

Component-owned truth required:

- perimeter source;
- return depth / cant height;
- return material/profile;
- return finish;
- color / paint / vinyl target;
- explicit dependency on face geometry when perimeter depends on face/root geometry.

Allowed dependency pattern:

```text
return_cant.perimeter_source = face.confirmed_perimeter
```

Not allowed:

- hidden perimeter ownership inside the product template;
- hidden return profile selection from product-level assumptions without component trace.

### Back

Component-owned truth required:

- back material;
- back thickness;
- backing mode;
- bevel or offset;
- back geometry source;
- relation to lighting and mounting when relevant.

Current strongest issue:

- back is still partially represented through root-level geometry and backing aliases instead of fully explicit owned truth.

### Lighting

Component-owned truth required:

- lighting mode;
- LED module type;
- LED density/count basis;
- module count;
- PSU sizing basis;
- circuits, zones, and service access when relevant;
- warnings and blockers.

Current strongest issue:

- many inputs exist, but zones/circuits/service access are still insufficiently owned as component truth.

### Finish

Component-owned truth required:

- finish target;
- material vs service distinction;
- vinyl / Oracal / RAL / print / lamination choice;
- `print_required`;
- `lamination_required`;
- artwork dependency;
- source/state.

Current strongest issue:

- finish still mixes material, application service, and artwork logic;
- some of this is still encoded or implied rather than cleanly owned on finish paths.

### Premount / support

Component-owned truth required:

- `support_required`;
- `support_type`;
- support material/profile;
- support dimensions;
- relation to mounting system;
- explicit separation from execution/install operational scope.

Current strongest issue:

- support is still partly bridge-derived from `mounting_system` and SVG hints;
- bridge evidence is not enough for true support ownership.

### Logo linked child

Component-owned truth required when linked child participation exists:

- logo geometry;
- logo face/back/return/lighting/finish participation;
- shared component mappings;
- linked-child status and binding source/state.

Still forbidden:

- logo root;
- logo quote;
- logo Work Intake offerability.

## 10. Product Template Default Rules

Defaults are allowed only as transitional inputs, never as silent final calculation truth.

A default may exist if:

- it is marked as default;
- it enters a component-owned truth path;
- it carries `fallback` or `hydrated` state;
- it can be confirmed or overridden;
- blockers remain visible until confirmation when the field is calculation-critical.

Defaults are not allowed to masquerade as owned truth merely because:

- they render in Review UI;
- they appear in Confirm summary;
- ProductDefinition can consume them;
- downstream read-only preview can list them.

## 11. Future Preview Preconditions

Before a future component preview request can return calculable outputs, the rule must be:

```text
component_truth_readiness >= TRUTH_COMPONENT_OWNED_READY
```

If not, the future preview response must return:

```text
readiness = blocked | partial_ready
missing_component_truth = [...]
fallback_values = [...]
confirmation_required = [...]
```

Mandatory response honesty:

- which inputs are confirmed;
- which are fallback;
- which are suggested;
- which are missing;
- which are derived dependencies;
- why preview is partial or blocked.

Component preview must not silently calculate from product template defaults.

## 12. First Candidate Decision

Recommended first candidate remains:

```text
return_cant
```

But only under the strengthened ownership rule.

`return_cant` remains first candidate only after explicit return/cant truth contract exists for:

- `return_depth`;
- return material/profile;
- return finish;
- perimeter dependency as explicit dependency;
- source/state for every required input.

Reason it still leads:

- strongest existing field ownership;
- strongest existing module/operation trace;
- geometry dependency can be expressed explicitly;
- lower semantic ambiguity than finish or premount/support.

## 13. Forbidden Shortcuts

Forbidden shortcuts:

- reading product-level root truth silently and calling it component-owned calculation;
- using ProductDefinition consumption as proof of owned input truth;
- using hydrated defaults as final calculation inputs without confirmation;
- treating UI-only form state as durable component truth;
- deriving support truth from mounting method without explicit support ownership;
- deriving finish target from implied zone semantics without explicit finish target path;
- using linked logo context as offerability evidence.

## 14. Open Questions

- Should face perimeter be a first-class face-owned truth field, or should face expose a canonical geometry package consumed by return_cant as explicit dependency?
- Should back material and thickness become explicit back-owned fields before any back preview slice, or can backing mode remain the temporary entry point?
- Should lighting own electrical and service-access details in one scope, or should electrical become a separate owned child truth boundary later?
- Should support and mounting remain sibling owned paths, or should one parent-child relationship be formalized after the trigger mismatch debt is removed?
- Should artwork become a first-class finish child truth scope before finish can ever be considered calculation-ready?

## 15. Recommended Next Slice

Recommended next prompt:

```text
FORM_SYSTEM_COMPONENT_FIELD_OWNERSHIP_MAP_V1
```

Then:

```text
INTAKE_V6_RETURN_CANT_COMPONENT_PREVIEW_READONLY_SLICE_V1
```

Reason:

- first we need a tighter field-by-field ownership map for component truth;
- then return/cant can become the first honest component-scoped preview slice without pretending product-root truth is already component-owned.