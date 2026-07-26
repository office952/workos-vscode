# COMPONENT_OWNED_TRUTH_BEFORE_COMPONENT_CALCULATION_CONTRACT_V1

Date: 2026-07-08
Project: WorkOS
Mode: docs-only / read-only contract definition

## 1. Safety gate

Commands run:

```text
git status -sb
git rev-parse --short HEAD
git diff --cached --name-only
git status --short --untracked-files=no
git diff --check
```

Result:

- accepted HEAD before contract work: `51af1ba`
- staged files before work: none
- tracked diffs before work: none
- preexisting untracked parked lanes: present
- action taken on parked lanes: none
- safety verdict: contract work could proceed

## 2. Scope

Goal:

- define the truth-ownership contract that must exist before any future component-scoped calculation can be considered real component calculation.

In scope:

- docs-only ownership audit;
- component truth readiness levels;
- component-by-component truth requirements;
- product-template versus component-truth rules;
- future preview preconditions;
- worklog and commit if clean.

Out of scope:

- backend implementation;
- frontend implementation;
- UI changes;
- endpoint changes;
- Product Truth write changes;
- component root;
- component quote;
- Pricing / Quote / Order / Execution;
- ProductAggregate / TaskGraph / ExecutionPlan;
- DB / seed / migration.

## 3. Files inspected

Prior component preview contract:

- `docs/architecture/product-system/INTAKE_V6_COMPONENT_CALCULATION_PREVIEW_CONTRACT.md`
- `docs/qa/intake-v6-component-calculation-preview-contract-2026-07-08/INTAKE_V6_COMPONENT_CALCULATION_PREVIEW_CONTRACT_V1.md`
- `docs/worklog/realignment/2026-07-08_intake_v6_component_calculation_preview_contract_v1.md`

Prior readiness audit and proof:

- `docs/qa/intake-v6-component-calculation-readiness-2026-07-08/INTAKE_V6_COMPONENT_CALCULATION_READINESS_AUDIT_V1.md`
- `docs/qa/intake-v6-component-calculation-readiness-2026-07-08/screenshots_index.md`
- `docs/worklog/realignment/2026-07-08_intake_v6_component_calculation_readiness_audit_v1.md`

Architecture contracts:

- `docs/architecture/product-system/PRODUCT_SYSTEM_COMPONENT_OWNED_CALCULATION_BOUNDARY.md`
- `docs/architecture/product-system/PRODUCT_SYSTEM_FORM_SYSTEM_COMPOSITION_CONTRACT.md`
- `docs/architecture/product-system/INTAKE_V6_PRODUCT_TRUTH_CONTRACT.md`
- `docs/architecture/product-system/PRODUCT_TRUTH_CONFIRMATION_POLICY.md`
- `docs/architecture/product-system/PRODUCT_SYSTEM_PRODUCT_TEMPLATE_VS_COMPONENT_TEMPLATE_CONTRACT.md`

Backend read-only code:

- `backend/data/shared_volumetric_component_contracts.py`
- `backend/data/mini_module_registry_volumetric_v2.py`
- `backend/services/intake_v6_modular_form_contract_service.py`
- `backend/services/form_system_contract_backbone_service.py`
- `backend/services/product_definition_builder_service.py`
- `backend/services/pre_order_technical_preview_readonly_service.py`

Frontend read-only code:

- `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.ts`
- `frontend/src/lib/intakeV6/formSystemBackboneFieldProjection.ts`
- `frontend/src/lib/intakeV6/formSystemBackboneAwareness.ts`
- `frontend/src/components/workos/intake-v6/FormSystemBackboneAwarenessPanel.tsx`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ConfirmStep.tsx`

## 4. Core findings

Confirmed now:

- component-aware truth paths already exist for face, return/cant, back, finish, lighting, support, mounting, and linked logo context;
- many inputs are still fallback, hydrated, suggested, or bridge-derived;
- ProductDefinition can consume and classify modules, but this is downstream consumption, not proof of owned input truth;
- UI Review/Confirm can hydrate and display values that are still not confirmed or still not component-owned;
- component preview contract is useful, but not yet sufficient to prove honest component calculation.

Central finding:

```text
Component calculation requires component-owned truth first.
Without that, the system is still doing product-root truth with filtered display.
```

## 5. Component truth ownership matrix

| component | required calculation inputs | where input lives now | should live in component truth? | current Product Truth path | current owner component | current source/state | is confirmed? | is fallback/hydrated/suggested? | is derived from product root? | is UI-only? | can component calculate from its own truth today? | missing component-owned truth | risk |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| face | area, perimeter basis, material, thickness, finish target, layer ownership | `quote_geometry`, `finish_setup`, layer role setup, builder defaults | yes | `components.face.*`, `components.finish.target` | `face` plus `finish_artwork` for target | fallback for material/thickness, suggested for layer refs, blocked for target when absent | partial | yes | geometry depends on root geometry package | no | no | explicit material, thickness, finish target, confirmed layer ownership | fallback can be mistaken for truth |
| return_cant | perimeter source, depth, material/profile, finish, color target | `quote_geometry`, `finish_setup`, module link field, optional group rows | yes | `components.return.*`, plus finish group rows | `return_cant` | hydrated depth, manual/missing material, mixed finish states | partial | yes | perimeter depends on face/root geometry unless exposed explicitly | no | partial only | explicit perimeter dependency path, explicit material/profile truth, confirmed finish target on cant | hidden perimeter ownership would fake component calculation |
| back | back material, thickness, backing mode, bevel, geometry source | `finish_setup`, builder alias defaults, face area proxy | yes | `components.back.*` emerging in draft | `back` | backing mode hydrated, bevel manual/hydrated, material implied | partial | yes | yes, geometry often proxied from root/face | no | no | explicit back material and thickness, explicit back geometry source | back can look independent while still borrowing root assumptions |
| lighting | lighting mode, LED type, density/count basis, module count, PSU basis, circuits/zones/service access | `finish_setup`, derived helpers, draft electrical section | yes | `components.lighting.*`, `components.electrical.*` | `lighting_led` and electrical child area | fallback/hydrated for mode and PSU, unknown for some electrical details | partial | yes | some values derived from illumination gate and root geometry context | some helper defaults | no | explicit module count basis, PSU basis, zones/circuits/service access | easy to overstate readiness because UI already shows LED values |
| finish | finish target, material/service split, print_required, lamination_required, artwork dependency | `finish_setup`, `artwork_finishes`, grouped finishes, implied UI semantics | yes | `components.finish.*`, `components.artwork.*` | `finish_artwork` | blocked for target when absent, hydrated for print/lamination, manual or unknown for artwork decisions | partial | yes | partly, because target and artwork can be inferred from root review context | some implied UI semantics | no | explicit finish target, explicit print/lamination truth, explicit artwork dependency ownership | finish can collapse into a mixed pseudo-truth layer |
| premount_support | support_required, support_type, support material/profile, support dimensions, mounting relation | `finish_setup.mounting_system`, `quote_input` derived fields, support hints from SVG | yes | `components.support.*`, `components.mounting.*` | `mounting_support` plus support child area | suggested/unknown for support, hydrated for mounting system, derived for bar data | partial | yes | yes, bridge from mounting/root width into support truth | some fields are helper-derived | no | explicit support_required, support_type, dimensions, owned material/profile | strongest semantic risk: support hidden inside mounting bridge |
| logo linked child | logo geometry, linked-child binding, component participation, shared mappings | linked template composition, artwork/layer bindings, logo strategy notes | yes for linked-child context, no for root | `linked_templates.logo` | linked child / not root | suggested binding by default, read-only candidate | no | yes | yes, currently depends on root workspace and linked bindings | no | no | explicit linked-child geometry/truth participation if ever previewed under root context | high risk if confused with offerable root |

## 6. Component truth readiness levels

- `TRUTH_MISSING`: component lacks required owned fields.
- `TRUTH_SUGGESTED_ONLY`: only analyzer or suggestion-level truth exists.
- `TRUTH_HYDRATED_OR_FALLBACK`: values exist, but are still defaults or reused state.
- `TRUTH_PARTIAL_CONFIRMED`: some owned inputs are confirmed, others remain missing/fallback/hydrated.
- `TRUTH_COMPONENT_OWNED_READY`: minimum preview inputs are on component-owned truth paths with explicit source/state.
- `TRUTH_COMPONENT_CALCULATION_READY`: enough owned truth exists for read-only calculable preview, without root or quote change.

Applied current reading:

- face: `TRUTH_PARTIAL_CONFIRMED`
- return_cant: `TRUTH_PARTIAL_CONFIRMED`, nearest to `TRUTH_COMPONENT_OWNED_READY`
- back: `TRUTH_HYDRATED_OR_FALLBACK`
- lighting: `TRUTH_HYDRATED_OR_FALLBACK`
- finish: `TRUTH_PARTIAL_CONFIRMED`
- premount_support: `TRUTH_HYDRATED_OR_FALLBACK`
- logo linked child: `TRUTH_SUGGESTED_ONLY`

## 7. Product Template vs component truth findings

Product Template may continue to own:

- root identity;
- component composition;
- required/optional status;
- orchestration;
- compatibility;
- Work Intake offerability;
- linked child relationships.

Product Template must not remain the final owner for calculation-critical component truth.

Observed current debt patterns:

- face material and thickness still rely on owner-approved defaults before explicit confirmation;
- return perimeter still depends on root geometry package unless dependency is made explicit;
- back material remains too implicit;
- lighting and electrical still contain helper/default values that are not owned truth;
- support still depends on mounting bridge and root width-derived values.

## 8. Future preview precondition

Future component preview must be gated by:

```text
component_truth_readiness >= TRUTH_COMPONENT_OWNED_READY
```

If not, response must return at minimum:

```text
readiness = blocked | partial_ready
missing_component_truth = [...]
fallback_values = [...]
confirmation_required = [...]
```

Preview must never silently read Product Template defaults and present the result as honest component calculation.

## 9. First candidate decision

`return_cant` remains the best first candidate, but only after explicit return/cant truth contract exists.

Why it still leads:

- strongest current ownership signal in Form System and mini-module registry;
- strongest operation/material trace;
- dependency on face geometry can be expressed explicitly instead of hidden.

What return/cant must own first:

- `return_depth`;
- return material/profile;
- return finish;
- explicit perimeter dependency source;
- source/state for every input.

## 10. Recommended next slice

Recommended next prompt:

```text
FORM_SYSTEM_COMPONENT_FIELD_OWNERSHIP_MAP_V1
```

Then:

```text
INTAKE_V6_RETURN_CANT_COMPONENT_PREVIEW_READONLY_SLICE_V1
```

Reason:

- ownership map should be tightened first;
- then return/cant can be implemented as the first honest read-only component preview slice.

## 11. No-code confirmation

This slice created documentation only.

Confirmed not changed:

- no backend runtime code;
- no frontend runtime code;
- no UI behavior;
- no endpoint;
- no Pricing / Quote / Order / Execution;
- no ProductAggregate / TaskGraph / ExecutionPlan;
- no DB / seed / migration.