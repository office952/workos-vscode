# RETURN_CANT_COMPONENT_TRUTH_CONTAINER_MIGRATION_PLAN_V1

## Scope

- Migration plan only.
- No implementation.
- No delete.
- No frontend change.
- No backend change.
- No seed change.
- No DB change.
- No migration.
- No live seed.
- No Pricing.
- No ProductDefinition.
- No Product Truth writer.
- No ProductAggregate runtime write.
- No LOGO activation.

## HEAD before

- `917f6d9`

## Files read

- `docs/worklog/realignment/2026-07-09_return_cant_component_truth_container_readonly_endpoint_alignment_v1.md`
- `docs/worklog/realignment/2026-07-09_product_component_composition_read_model_alignment_v1.md`
- `docs/worklog/realignment/2026-07-09_product_component_composition_contract_v1.md`
- `docs/architecture/product-system/RETURN_CANT_COMPONENT_CONFIRMATION_CONTRACT.md`
- `docs/architecture/product-system/PRODUCT_SYSTEM_COMPONENT_OWNED_CALCULATION_BOUNDARY.md`
- `frontend/src/features/product-system/returnCantReadonlyContainerModel.ts`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper.ts`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.ts`
- `backend/data/mini_module_registry_volumetric_v2.py`
- `backend/data/shared_volumetric_component_contracts.py`
- `backend/services/product_aggregate_service.py`
- `backend/services/intake_v6_modular_form_contract_service.py`

## Searches run

- `source_face_perimeter_ref`
- `confirmed_perimeter_m`
- `material_profile`
- `layer_group_ids`
- `confirmation_state`
- `components.return_cant.instances`
- `components.face.confirmed_perimeter`
- `components.returnCant`
- `quote_geometry.letter_perimeter_m`
- `return_depth_mm`
- `return_finish_type`
- `modelare_cant`
- `comp_lateral_litere`
- `TPL-VOLUM-ALUMINIU_v1`

## Migration field inventory

### 1. `source_face_perimeter_ref`

- Meaning:
  explicit reference from one `return_cant` instance to the upstream face perimeter source.
- Candidate source:
  future canonical reference to `components.face.confirmed_perimeter`.
- Current source today:
  none as explicit field; only conceptual dependency exists.
- What is missing:
  stable reference field and dependency contract binding.
- What depends on it:
  `perimeter_source`, `confirmed_perimeter_m`, blocked/partial readiness, future pricing-safe component calculation.
- Risk if migrated too early:
  fake certainty around a perimeter dependency that still has no explicit owner-safe runtime source.
- Test that would prove migration:
  readonly mapper test asserting `source_face_perimeter_ref` is present and points to the canonical face perimeter path while root geometry remains downgraded to context-only.

### 2. `confirmed_perimeter_m`

- Meaning:
  the component-owned resolved perimeter value for the return/cant instance.
- Candidate source:
  derived from face confirmed perimeter, not directly from root geometry.
- Current source today:
  only `quote_geometry.letter_perimeter_m` context and readonly warnings.
- What is missing:
  canonical value field scoped to the return/cant instance.
- What depends on it:
  quantity basis, truthful component calculation readiness, honest downstream consumption.
- Risk if migrated too early:
  copying root context into component truth and masking missing dependency semantics.
- Test that would prove migration:
  readonly adapter test where `confirmed_perimeter_m` is emitted only when upstream face perimeter is explicit and confirmed.

### 3. `material_profile`

- Meaning:
  the selected aluminum profile/material truth for the return/cant instance.
- Candidate source:
  component-owned selection derived or confirmed from the depth gate, but stored explicitly on the component instance.
- Current source today:
  child template profile gates in `TPL-VOLUM-ALUMINIU_v1`; no explicit truth field.
- What is missing:
  explicit selected material/profile truth field.
- What depends on it:
  separate calculation, material alignment, future downstream consumption, readiness.
- Risk if migrated too early:
  material might be inferred from gate rules without a real confirmation/source-state distinction.
- Test that would prove migration:
  mapper/adapter test confirming profile selection emits the explicit `material_profile` field and no longer relies on implied gate-only semantics.

### 4. `layer_group_ids`

- Meaning:
  component-scoped mapping from selected layers/groups to the return/cant instance.
- Candidate source:
  layer-role/selection outputs promoted through a component-specific mapping step.
- Current source today:
  selected layer refs, layer confirmations, and row evidence only.
- What is missing:
  canonical component-owned field for mapped layer groups.
- What depends on it:
  scoped preview/readiness, finish segmentation, truthful instance identity.
- Risk if migrated too early:
  wrongly treating generic selected refs as already component-scoped.
- Test that would prove migration:
  readonly mapper test asserting `layer_group_ids` exists only after explicit mapping, with root/selection evidence downgraded otherwise.

### 5. `confirmation_state`

- Meaning:
  final component-scoped confirmation gate for the return/cant instance.
- Candidate source:
  component-level confirmation semantics defined in the confirmation contract.
- Current source today:
  only workflow/global confirmations and row-level confirms.
- What is missing:
  actual component instance field and strict promotion rules.
- What depends on it:
  readiness, truth completeness, future write/promotion discipline.
- Risk if migrated too early:
  promoting workflow/row confirmation into false component truth.
- Test that would prove migration:
  confirmation contract test proving row/global confirmation does not unlock the field, while explicit component confirmation does.

## Recommended migration order

Recommended order:

1. `source_face_perimeter_ref`
2. `confirmed_perimeter_m`
3. `layer_group_ids`
4. `material_profile`
5. `confirmation_state`

### Why this order

1. `source_face_perimeter_ref` first:
   without the dependency anchor, return/cant keeps borrowing root geometry context.

2. `confirmed_perimeter_m` second:
   once the dependency reference exists, the value can be modeled honestly as dependency output rather than copied evidence.

3. `layer_group_ids` third:
   instance identity and segmentation should stabilize before material/confirmation finalization.

4. `material_profile` fourth:
   profile selection should land after geometry/dependency/instance scope are explicit, so it binds to the correct component instance.

5. `confirmation_state` last:
   confirmation should be the closing gate, not the mechanism that hides missing prerequisites.

## Canonical source decisions

| Field | Canonical source proposed | Legacy source temporary | Root context downgraded | ProductAggregate treatment | Compatibility note |
|---|---|---|---|---|---|
| `source_face_perimeter_ref` | explicit ref to `components.face.confirmed_perimeter` | none | `quote_geometry.letter_perimeter_m` | derived-only context | UI/read-model must keep showing blocked until ref exists |
| `confirmed_perimeter_m` | resolved from canonical face dependency | none | `letter_perimeter_m` | derived-only support | readonly panels keep showing context-only until migrated |
| `layer_group_ids` | component-scoped mapped layer ids | selected refs / row ids | generic selected layer refs | support only | readonly mappers keep warning on unmapped refs |
| `material_profile` | explicit component-owned selected profile | depth gate implication only | n/a | do not infer from aggregate rows | child template gate remains support, not final truth |
| `confirmation_state` | explicit component-level confirmation | workflow/global confirms | row/global confirmations | derived-only note | readonly views must keep showing blocked until explicit field exists |

## Legacy alias survival plan

For `components.returnCant.*`:

- keep temporarily:
  - `components.returnCant.depthMm`
  - `components.returnCant.finishType`
  - `components.returnCant.colorCode`
- why:
  readonly mappers, tests, and legacy draft/runtime language still rely on them for compatibility and diagnostics.
- replacement:
  component-owned target fields under `components.return_cant.instances[]`.
- when they become delete candidates:
  only after canonical component instance fields exist, readonly compatibility tests pass, and UI/read-model no longer rely on alias interpretation.
- tests required before delete:
  - legacy alias compatibility test
  - readonly mapper canonicalization test
  - ProductSystem readonly rendering test
  - no-mutation regression proving aliases are no longer needed for read-only explanation.

## ProductAggregate boundary plan

- ProductAggregate remains derived read model.
- It must not become the source for:
  - `material_profile`
  - `confirmed_perimeter_m`
  - `confirmation_state`
  - `layer_group_ids`
- Future ProductAggregate should only consume the component-owned container once those fields exist.
- Before any ProductAggregate runtime change, verify:
  - canonical component fields exist first
  - ProductAggregate is reading them, not synthesizing them
  - current parent/dossier support rows can be downgraded without losing diagnostic visibility.

## Migration proof tests plan

### Frontend readonly tests

- ProductSystem test:
  continue proving target container, FACE dependency, legacy alias note, blocked readiness.

### Mapper / adapter tests

- `returnCantTruthFieldsReadonlyMapper`:
  prove canonical fields replace context-only language one by one.
- `returnCantTruthFieldCaptureReadonlyAdapter`:
  prove instance-bound target paths and dependency semantics remain explicit.

### Backend read-only test if later needed

- only if a shared backend read-only endpoint/service is later introduced.
- prove GET/read-only and no mutation.

### No-mutation proof

- explicit test or contract check that new readonly/container helpers do not write Product Truth, DB, or ProductAggregate.

### Legacy alias compatibility test

- prove legacy alias paths continue to render as compatibility language until canonical fields replace them.

### ProductAggregate derived-only test

- prove ProductAggregate consumes canonical fields when they exist, but does not invent them when missing.

## Risks

- migrating `confirmed_perimeter_m` too early could freeze root geometry context as fake component truth
- migrating `material_profile` too early could turn a gate rule into false confirmed truth
- migrating `confirmation_state` too early could promote row/workflow confirmation into final component truth
- deleting legacy aliases too early would break readonly diagnostics and tests

## Recommendation

1. First implementation slice should start with the dependency anchor: `source_face_perimeter_ref`.
2. Do not touch ProductAggregate runtime until canonical fields exist.
3. Delete work must remain blocked until migration and compatibility tests pass.

## Forbidden scope confirmation

- no implementation
- no delete
- no frontend modified
- no backend modified
- no seed modified
- no DB migration
- no seed live
- no Pricing
- no ProductDefinition
- no Product Truth writer change
- no ProductAggregate runtime write
- no LOGO activation

## Next recommended prompt

```text
TASK — RETURN_CANT_SOURCE_FACE_PERIMETER_REF_READONLY_SLICE_V1
```

Suggested scope:

- first implementation slice only for `source_face_perimeter_ref`
- stay read-only if possible or minimal canonical-source introduction without full writer implementation
- no Pricing
- no ProductDefinition
- no writer
- no delete
