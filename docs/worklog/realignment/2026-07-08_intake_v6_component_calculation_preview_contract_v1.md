# 2026-07-08 - intake v6 component calculation preview contract v1

Summary:

- defined a docs-only future contract for component-scoped read-only preview inside the existing Intake V6 letters-root flow;
- preserved the mandatory root lock: `TPL-VOLUMETRIC-LETTERS_v2`, `product_template`, `product_total`, `read_only_preview`;
- clarified supported scopes: face, return_cant, back, lighting, finish, premount_support;
- clarified that Logo remains linked-child context only and is not a supported root preview scope.

Main decision:

- component preview must be a scoped diagnostic under the product root, not a new product identity and not a component-only commercial path.

Why this shape is safe:

- Form System Backbone already blocks component root and component quote.
- Product Truth draft already carries per-component blockers and source/state honesty.
- ProductDefinition preview already has selected/optional/inactive module vocabulary.
- Pre-order technical preview already proves the no-write preview pattern.

First implementation candidate:

- `return_cant`

Reason:

- clearest inputs;
- existing perimeter/depth/material basis;
- existing module/operation trace;
- lower semantic risk than finish, lighting, or premount/support.

Explicitly not changed:

- no code;
- no endpoint;
- no UI;
- no Pricing / Quote / Order / Execution;
- no ProductAggregate / TaskGraph / ExecutionPlan;
- no DB/seed/migration.

Recommended next prompt:

- `INTAKE_V6_RETURN_CANT_COMPONENT_PREVIEW_READONLY_SLICE_V1`