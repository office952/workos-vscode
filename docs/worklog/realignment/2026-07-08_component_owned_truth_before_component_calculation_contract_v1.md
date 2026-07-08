# 2026-07-08 - component owned truth before component calculation contract v1

Summary:

- defined a docs-only contract that says component calculation can exist only after required inputs are owned by the component truth boundary;
- clarified that product-level preview scope alone is not enough;
- preserved the current product-root boundary and all forbidden runtime areas.

Main finding:

- the repo already has many component-shaped Product Truth paths, but several critical values are still fallback, hydrated, bridge-derived, or UI-only;
- that means future component preview must still be gated by truth ownership before it can be called honest component calculation.

Current best candidate remains:

- `return_cant`

But only after:

- return depth;
- return material/profile;
- return finish;
- perimeter dependency;
- source/state

are all explicitly owned or traced under return/cant truth.

Explicitly not changed:

- no code;
- no UI;
- no endpoint;
- no Pricing / Quote / Order / Execution;
- no ProductAggregate / TaskGraph / ExecutionPlan;
- no DB / seed / migration.

Recommended next prompt:

- `FORM_SYSTEM_COMPONENT_FIELD_OWNERSHIP_MAP_V1`

After that:

- `INTAKE_V6_RETURN_CANT_COMPONENT_PREVIEW_READONLY_SLICE_V1`