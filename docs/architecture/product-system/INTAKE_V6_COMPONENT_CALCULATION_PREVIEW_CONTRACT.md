# Intake V6 Component Calculation Preview Contract

## 1. Purpose

This document defines the future read-only contract for component-scoped preview inside the existing Intake V6 letters-root flow.

The goal is to let an operator request a bounded technical preview for one component scope such as face, return/cant, back, lighting, finish, or premount/support without changing the product root, without activating component quote, and without producing downstream side effects.

This document is docs-only. It does not implement backend runtime, frontend UI, API routing, Pricing, Quote, Order, Execution, ProductAggregate, TaskGraph, ExecutionPlan, DB writes, seeds, or migrations.

## 2. Background

The current audited runtime direction is:

```text
root_template_code = TPL-VOLUMETRIC-LETTERS_v2
root_type = product_template
quote_mode = product_total
mode = read_only_preview
```

Read-only audit confirmed that the repo already contains:

- Product System shared component visibility for face, back, return/cant, lighting, finish, and premount/support.
- Form System Backbone ownership, source/state, blocker, and root guard semantics.
- Product Truth draft structures split by component domain.
- ProductDefinition preview/read-only consumption of modular form fields and active/inactive module states.
- Pre-order technical preview precedent for metadata-only preview with explicit no-write guards.

Read-only audit also confirmed what is still missing:

- no operator action equivalent to `calculeaza doar componenta`;
- no component-scoped preview request/response contract;
- no component root activation;
- no component quote activation;
- no component-scoped commercial authority.

## 3. Non-goals

This contract does not authorize or imply:

- component root;
- component quote;
- `root_type=component_template`;
- `quote_mode=component_only`;
- Logo root offerability;
- official commercial price;
- quote creation;
- order creation;
- execution or task materialization;
- stock movement;
- ProductAggregate, TaskGraph, or ExecutionPlan activation;
- seed, migration, or DB writes;
- cleanup expansion around `TPL-VOLUMETRIC-MOUNTING-STRUCTURE_v1`.

## 4. Canonical Boundary

The preview remains inside the existing product root.

Mandatory root lock:

```text
root_template = TPL-VOLUMETRIC-LETTERS_v2
root_type = product_template
quote_mode = product_total
component_scope = face | return_cant | back | lighting | finish | premount_support
mode = read_only_preview
```

Canonical reading:

- operator asks for a read-only preview of one component scope;
- system reuses existing Product Truth / Form System / ProductDefinition structures;
- response reports calculable values, missing values, blockers, and source/state confidence;
- response does not create official price, quote, order, tasks, execution, or stock movement.

Boundary invariants:

- root never changes from `TPL-VOLUMETRIC-LETTERS_v2` in this slice;
- component scope is a filter and trace boundary, not a new product identity;
- component template metadata may be referenced, but component template cannot become root;
- linked Logo can appear only as read-only context, not as root or commercial authority.

## 5. Request Contract

### Proposed request shape

```ts
type ComponentPreviewRequest = {
  workspace_id: string;
  root_template_code: "TPL-VOLUMETRIC-LETTERS_v2";
  root_type: "product_template";
  quote_mode: "product_total";
  mode: "read_only_preview";
  component_scope:
    | "face"
    | "return_cant"
    | "back"
    | "lighting"
    | "finish"
    | "premount_support";
  include_missing_fields: true;
  include_blockers: true;
  include_source_state: true;
  include_product_definition_trace: true;
};
```

### Request rules

- `workspace_id` is mandatory because preview is runtime-workspace scoped, not catalog-only.
- `root_template_code` must remain `TPL-VOLUMETRIC-LETTERS_v2` for V1.
- `root_type` must remain `product_template`.
- `quote_mode` must remain `product_total`.
- `mode` must remain `read_only_preview`.
- `component_scope` must not silently fall back to full product summary if unsupported.
- unsupported scope must return `not_supported`.
- shared component template codes must not be accepted as root substitutes in this contract.

### Request validation blockers

- `ROOT_TYPE_BLOCKED`
- `QUOTE_MODE_BLOCKED`
- `ROOT_NOT_OWNER_VALID`
- `COMPONENT_ROOT_BLOCKED`
- `LOGO_NOT_OFFERABLE`
- `UNSUPPORTED_COMPONENT_SCOPE`
- `WORKSPACE_TEMPLATE_MISMATCH`

## 6. Response Contract

### Proposed response shape

```ts
type ComponentPreviewResponse = {
  workspace_id: string;
  root_template_code: "TPL-VOLUMETRIC-LETTERS_v2";
  root_type: "product_template";
  quote_mode: "product_total";
  mode: "read_only_preview";
  component_scope: string;

  component_template_code: string;
  component_concept: string;

  readiness:
    | "ready_for_preview"
    | "partial_ready"
    | "blocked"
    | "not_supported";

  source_state_summary: {
    confirmed: number;
    suggested: number;
    hydrated: number;
    fallback: number;
    missing: number;
    blocked: number;
    warning: number;
  };

  inputs: Array<{
    field_key: string;
    label: string;
    product_truth_path: string | null;
    source: "confirmed" | "suggested" | "hydrated" | "fallback" | "missing";
    value: unknown;
    required: boolean;
    blocker_code?: string;
  }>;

  outputs_preview: Array<{
    output_key: string;
    label: string;
    value: unknown;
    unit?: string;
    confidence: "high" | "medium" | "low";
    reason?: string;
  }>;

  blockers: Array<{
    code: string;
    severity: "blocking" | "warning";
    message: string;
    field_key?: string;
    product_truth_path?: string;
  }>;

  product_definition_trace: {
    selected_modules: string[];
    optional_modules: string[];
    inactive_modules: string[];
    canonical_value_keys: string[];
    notes: string[];
  };

  boundaries: {
    no_component_root: true;
    no_component_quote: true;
    no_pricing_authority: true;
    no_order: true;
    no_execution: true;
    no_task_materialization: true;
    no_stock_movement: true;
  };
};
```

### Why one small addition was made

`product_definition_trace` is added explicitly to avoid a risky future shortcut where preview consumers guess module activation from UI labels alone. The repo already has selected/optional/inactive module vocabulary in ProductDefinition preview, so the response should expose that trace intentionally.

### Response rules

- `readiness=ready_for_preview` means enough data exists for read-only preview, not quote-ready.
- `readiness=partial_ready` means preview can show useful scoped information with visible fallback/hydrated/missing caveats.
- `readiness=blocked` means required component inputs are missing or boundary rules are violated.
- `readiness=not_supported` means the requested scope is outside V1 contract and must not degrade to product summary.
- `inputs` must preserve source/state honesty.
- `outputs_preview` must remain technical/read-only and must not imply official price or downstream task commitment.
- `blockers` must include both component-local blockers and root/boundary blockers when relevant.

## 7. Component Scopes

Supported V1 scopes:

- `face`
- `return_cant`
- `back`
- `lighting`
- `finish`
- `premount_support`

Special case:

- Logo remains linked-child context only.
- Logo is not a supported root preview scope in this contract.
- If logo-linked context is referenced, it may appear only as a note or blocker trace under the letters root.

Scope semantics:

- `face` means front visual component preview for face material/thickness/area/finish dependencies.
- `return_cant` means lateral return/profile preview under the letters root.
- `back` means backing panel preview.
- `lighting` means LED plus immediate electrical preview relevant to product truth.
- `finish` means finish/artwork/application preview, not pricing.
- `premount_support` means support/premount preview with explicit support vs mounting boundary preserved.

## 8. Component-specific Inputs, Outputs, and Blockers

### 8.1 Face

Component template:

```text
TPL-VOLUMETRIC-FACE_v1
```

Required inputs:

- `face.material`
- face thickness confirmation
- `letter_face_area_m2`
- confirmed or accepted face layer group refs
- `face_finish_type` when finish applies to face

Possible preview outputs:

- face area basis
- face material family
- face thickness
- face finish target trace
- face operation references such as cut / vinyl application preview

Main blockers:

- `FACE_MATERIAL_MISSING`
- `FACE_MATERIAL_FALLBACK_REQUIRES_CONFIRMATION`
- `FACE_THICKNESS_FALLBACK_REQUIRES_CONFIRMATION`
- `FACE_LAYER_NOT_FOUND`

Source/state issues:

- face material and thickness are still often fallback until explicit confirmation;
- area can be present earlier than material truth;
- finish target can remain incomplete even when geometry exists.

Why partial ready:

- shape and area are real enough for preview;
- material/thickness authority is still weaker than return/cant;
- face-only preview risks looking stronger than confirmed truth if fallback is hidden.

### 8.2 Return / cant

Component template:

```text
TPL-VOLUM-ALUMINIU_v1
```

Required inputs:

- `return_depth_mm`
- `return_finish_type`
- `letter_perimeter_m`
- return material/profile family
- optional return color code when wrap/finish requires it

Possible preview outputs:

- perimeter basis
- depth
- selected return finish family
- material/profile family by depth gate
- preview operation references such as forming, face bonding, painting

Main blockers:

- `RETURN_CANT_MATERIAL_MISSING`
- `RETURN_CANT_HEIGHT_CONFIRMATION_REQUIRED`
- `RETURN_CANT_DEPTH_MISSING`

Why first candidate / most ready:

- inputs are clearer than other scopes;
- perimeter and depth are already modeled;
- mini-module contract already expresses materials, operations, and outputs;
- risk of accidental pricing authority is lower than finish or lighting;
- preview can demonstrate component scoping without changing root or quote mode.

### 8.3 Back

Component template:

```text
TPL-VOLUMETRIC-BACK_v1
```

Required inputs:

- `backing_mode`
- bevel decision when applicable
- face-area-derived geometry basis
- back material rule or alias resolution

Possible preview outputs:

- backing mode
- bevel status
- back cut preview references
- back panel active/inactive trace in ProductDefinition

Main blockers:

- backing mode unresolved
- bevel unresolved when variant requires it
- lack of explicit back material confirmation

Missing truth:

- back is still partly expressed through shared geometry and backing aliases;
- back material authority is weaker than return/cant;
- component-specific geometry is not first-class.

### 8.4 Lighting

Component template:

```text
TPL-VOLUMETRIC-LED_v1
```

Required inputs:

- `lighting_system_type`
- illuminated gate
- LED count or LED density basis
- PSU selection
- light color when relevant

Possible preview outputs:

- lighting mode
- LED count preview
- PSU selection preview
- lighting module activation trace
- operation references such as install and test

Main blockers:

- `LIGHTING_MODE_CONFIRMATION_REQUIRED`
- missing LED count / PSU values
- unresolved electrical detail blockers

Missing zones/circuits/service access:

- zones;
- circuits;
- service access;
- stronger electrical topology truth;
- site-specific cable or PSU placement must remain order/execution-only by default.

### 8.5 Finish

Component template:

```text
TPL-VOLUMETRIC-FINISH_v1
```

Required inputs:

- `face_finish_type`
- `finish_target`
- artwork decisions when printed artwork exists
- print/lamination booleans or equivalent explicit truth
- group finish confirmations when grouped finishes exist

Possible preview outputs:

- face finish family
- oracal series trace
- print/lamination preview flags
- finish target trace
- grouped finish breakdown

Main blockers:

- `FINISH_TARGET_MISSING`
- `ARTWORK_DECISION_MISSING`
- `PRINT_REQUIRED_UNKNOWN`
- `LAMINATION_REQUIRED_UNKNOWN`

Material/service/artwork boundary:

- finish still blends material choice, service application, and artwork decision;
- current encoded artwork execution is not a clean canonical target model;
- this scope is preview-worthy but not the first safe implementation candidate.

### 8.6 Premount / support

Component template:

```text
TPL-METAL-PREMOUNT-STRUCTURE_v1
```

Required inputs:

- `mounting_system`
- derived or confirmed support requirement
- support type
- bar material
- premount bar length or equivalent basis

Possible preview outputs:

- support activation trace
- bar material derivation
- premount length basis
- premount operation references
- optional module activation trace

Main blockers:

- `MOUNTING_SYSTEM_CONFIRMATION_REQUIRED`
- `SUPPORT_REQUIRED_UNKNOWN`
- `SUPPORT_TYPE_MISSING`
- `TRIGGER_FIELD_MISMATCH`

Support vs mounting risk:

- current bridge derives support evidence from `mounting_system` and SVG hints;
- support truth is not identical to mounting truth;
- this is the scope with the highest semantic confusion risk if preview language is sloppy.

### 8.7 Logo candidate

Current status:

- not a supported component preview root;
- may participate only as linked-child context under the letters root;
- no Logo offerability is enabled.

Rules:

- requesting logo as root-equivalent preview must fail closed;
- logo-linked notes may appear only as contextual blockers, segment notes, or linked trace;
- no Logo commercial authority is implied by pricing availability or shared module reuse.

## 9. First Implementation Candidate

Recommended first candidate:

```text
return_cant
```

### Why return/cant is the first candidate

- its required inputs are already explicit in Form System and modular bindings;
- perimeter and depth already exist as technical basis;
- module registry already defines materials, operations, and output traces;
- it carries lower semantic blur than finish and lower topology debt than lighting;
- it demonstrates component-scoped preview without requiring component root or commercial authority.

### MVP for return/cant preview

- accept `component_scope=return_cant` under locked letters root;
- report return depth, finish type, perimeter basis, material/profile family, and source/state summary;
- expose module activation trace for `modelare_cant`;
- expose blockers when return depth/material/finish truth is missing or unconfirmed;
- expose no-write boundary badges.

### What must stay read-only

- no official commercial price;
- no quote line creation;
- no module persistence changes;
- no task generation;
- no execution routing;
- no inventory or stock movement.

### What must be blocked explicitly

- root changes to `component_template`;
- `quote_mode=component_only`;
- silent full-product fallback when `return_cant` preview cannot be computed;
- any attempt to interpret preview outputs as official offer lines;
- any downstream task or order side effect.

### Boundary test that proves the slice

A future boundary test should prove that a `return_cant` preview request:

- keeps `root_type=product_template`;
- keeps `quote_mode=product_total`;
- reports scoped return preview data;
- does not expose official commercial total;
- does not create order/execution/task/stock side effects.

## 10. UI Contract

Future UI belongs in Intake V6 Review as a read-only diagnostic surface.

Expected interaction model:

- default mode remains product summary / all;
- operator may switch to a component scope selector;
- selector options:
  - Fata
  - Cant / lateral
  - Spate
  - Iluminare
  - Finisaj
  - Suport / premount

Expected read-only sections:

- readiness badge;
- inputs list;
- missing fields;
- source/state summary;
- preview outputs;
- blockers;
- boundary badges:
  - `read-only`
  - `no component root`
  - `no component quote`
  - `no order`
  - `no execution`

UI prohibitions:

- no button for component quote creation;
- no button for order creation;
- no button for execution handoff;
- no official price;
- no task materialization controls;
- no stock controls.

Canonical UI copy should stay explicit:

```text
Component preview only.
Read-only.
Does not create quote, order, execution, tasks, or stock movement.
```

## 11. Future Tests

Minimum required future tests:

1. request with `component_scope=return_cant` keeps `root_type=product_template` and `quote_mode=product_total`.
2. request with shared component template code as root returns blocker `COMPONENT_ROOT_BLOCKED`.
3. response includes source/state summary.
4. response includes blockers for missing required fields.
5. response does not include official commercial price.
6. response has no order/execution/task/stock side effects.
7. Logo candidate cannot be requested as root.
8. unsupported `component_scope` returns `not_supported`, not fallback to full product.
9. `premount_support` response preserves `TRIGGER_FIELD_MISMATCH` warning when support truth is only bridge-derived.
10. `finish` response preserves explicit blockers for target and artwork decisions instead of collapsing into a generic preview-ready state.

## 12. Forbidden Shortcuts

Forbidden shortcuts for future implementation:

- treating a shared component template as preview root;
- treating component preview as component quote;
- reusing pricing preview totals as component preview outputs;
- silently upgrading fallback/hydrated values to confirmed truth;
- using ProductDefinition selected modules as proof of commercial readiness;
- merging support and mounting into one truth field;
- treating Logo linked-child context as root offerability evidence;
- falling back from unsupported scope to full product preview without an explicit `not_supported` response.

## 13. Open Questions

- Should V1 response include a normalized `scope_owner_component_key` separate from `component_scope` for finish/artwork and mounting/support alias clarity?
- Should face preview expose face thickness as explicit input even before runtime UI has first-class controls, or only report it as fallback/unconfirmed?
- Should back preview keep using face-area-derived geometry or wait for a cleaner back-specific geometric basis?
- Should lighting preview include electrical warnings inline or keep them as nested `electrical` notes under the same scope?
- Should finish preview split artwork decisions into a separate sub-scope later, or remain grouped in V1?
- Should `premount_support` stay a combined scope in V1 or report sub-areas `mounting` and `support` separately in diagnostics while preserving one request scope?

## 14. Recommended Implementation Slice

Recommended next implementation prompt:

```text
INTAKE_V6_RETURN_CANT_COMPONENT_PREVIEW_READONLY_SLICE_V1
```

Reason:

- it is the cleanest proof-of-boundary candidate;
- it has the clearest input/output mapping already present in current contracts;
- it demonstrates component-scoped preview without root or quote changes;
- it avoids the heavier semantic debt present in lighting, finish, and premount/support.