# INTAKE_V6_COMPONENT_CALCULATION_PREVIEW_CONTRACT_V1

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

- accepted HEAD before contract work: `8923ba0`
- staged files before work: none
- tracked diffs before work: none
- preexisting untracked parked lanes: present
- action taken on parked lanes: none
- safety verdict: contract work could proceed

## 2. Scope

Goal:

- define a future read-only component-scoped preview contract inside Intake V6 without activating component root, component quote, pricing authority, or downstream writes.

In scope:

- architecture contract for request/response shape;
- component scope matrix;
- first implementation candidate decision;
- future UI contract definition;
- future test contract definition;
- QA/worklog docs.

Out of scope:

- backend implementation;
- frontend implementation;
- new endpoint;
- new UI;
- new calculation;
- Pricing / Quote / Order / Execution changes;
- ProductAggregate / TaskGraph / ExecutionPlan changes;
- DB writes / migrations / seeds;
- stale mounting cleanup expansion.

## 3. Files inspected

Prior audit and proof:

- `docs/qa/intake-v6-component-calculation-readiness-2026-07-08/INTAKE_V6_COMPONENT_CALCULATION_READINESS_AUDIT_V1.md`
- `docs/qa/intake-v6-component-calculation-readiness-2026-07-08/screenshots_index.md`
- `docs/worklog/realignment/2026-07-08_intake_v6_component_calculation_readiness_audit_v1.md`

Architecture contracts:

- `docs/architecture/product-system/PRODUCT_SYSTEM_COMPONENT_OWNED_CALCULATION_BOUNDARY.md`
- `docs/architecture/product-system/PRODUCT_SYSTEM_FORM_SYSTEM_COMPOSITION_CONTRACT.md`
- `docs/architecture/product-system/INTAKE_V6_PRODUCT_TRUTH_CONTRACT.md`
- `docs/architecture/product-system/PRODUCT_TRUTH_CONFIRMATION_POLICY.md`
- `docs/architecture/product-system/COMMERCIAL_PREVIEW_BOUNDARY_CONTRACT.md`
- `docs/architecture/product-system/PRODUCT_SYSTEM_COMPONENT_PRODUCTION_OPERATIONS_CONTRACT.md`

Backend read-only code:

- `backend/services/intake_v6_modular_form_contract_service.py`
- `backend/services/form_system_contract_backbone_service.py`
- `backend/services/product_definition_builder_service.py`
- `backend/services/pre_order_technical_preview_readonly_service.py`
- `backend/services/template_usage_mode_policy.py`
- `backend/services/product_template_availability_service.py`
- `backend/data/shared_volumetric_component_contracts.py`
- `backend/data/mini_module_registry_volumetric_v2.py`

Frontend read-only code:

- `frontend/src/lib/intakeV6/preOrderTechnicalPreviewApi.ts`
- `frontend/src/lib/intakeV6/formSystemBackboneFieldProjection.ts`
- `frontend/src/lib/intakeV6/formSystemBackboneAwareness.ts`
- `frontend/src/lib/intakeV6/productTruth/productTruthDraftBuilder.ts`
- `frontend/src/components/workos/intake-v6/PreOrderTechnicalPreviewPanel.tsx`
- `frontend/src/components/workos/intake-v6/FormSystemBackboneAwarenessPanel.tsx`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ReviewStep.tsx`
- `frontend/src/components/workos/intake-v6/steps/IntakeV6ConfirmStep.tsx`

## 4. Contract summary

Root lock preserved:

```text
root_template_code = TPL-VOLUMETRIC-LETTERS_v2
root_type = product_template
quote_mode = product_total
mode = read_only_preview
```

Core contract decision:

- component preview is a scoped read-only diagnostic under the letters root;
- it is not component root;
- it is not component quote;
- it is not commercial authority;
- it is not task or execution materialization.

Request summary:

- workspace-scoped;
- root locked to letters v2;
- one of `face`, `return_cant`, `back`, `lighting`, `finish`, `premount_support`;
- must include missing fields, blockers, source/state, and ProductDefinition trace.

Response summary:

- returns component template code and concept;
- returns readiness state;
- returns source/state summary;
- returns scoped inputs and preview outputs;
- returns blockers and boundary badges;
- returns ProductDefinition selected/optional/inactive module trace.

## 5. Boundary findings

Confirmed from current code/contracts:

- Form System Backbone blocks `component_template` roots and `component_only` quote mode.
- shared component template codes are internal/shared units, not roots.
- Product Truth draft already models component-owned fields and blockers.
- Pre-order technical preview already proves a metadata-only preview pattern with no-write guards.
- Confirm and Review UI already use read-only language and explicit no-write semantics.

Must remain forbidden:

- no component root;
- no component quote;
- no official commercial price;
- no order;
- no execution;
- no task materialization;
- no stock movement;
- no Logo offerability.

## 6. Component matrix

| scope | template | readiness for preview contract | strongest inputs | main blockers | contract verdict |
|---|---|---|---|---|---|
| face | `TPL-VOLUMETRIC-FACE_v1` | partial | area, layer refs, face finish | material/thickness fallback confirmation | valid scope, not first candidate |
| return_cant | `TPL-VOLUM-ALUMINIU_v1` | strongest | perimeter, depth, finish, profile material | depth/material confirmation | best first candidate |
| back | `TPL-VOLUMETRIC-BACK_v1` | partial with gap | backing mode, bevel | missing explicit back truth/material authority | valid scope, later |
| lighting | `TPL-VOLUMETRIC-LED_v1` | partial with audit debt | lighting mode, LED count, PSU | missing zones/circuits/service access | valid scope, not first |
| finish | `TPL-VOLUMETRIC-FINISH_v1` | partial with boundary blur | finish type, target, artwork decisions | target/artwork/print-laminate split | valid scope, not first |
| premount_support | `TPL-METAL-PREMOUNT-STRUCTURE_v1` | partial with semantic risk | mounting system, bar material, premount length | support vs mounting, trigger mismatch | valid scope, later |
| logo candidate | `TPL-VOLUMETRIC-LOGO_v1` | linked-only | linked child context only | root blocked, not offerable | not a supported root preview scope |

## 7. First candidate decision

Recommended first implementation candidate:

```text
return_cant
```

Reason:

- modular bindings already expose return depth, finish, and perimeter basis;
- mini-module registry already documents materials, operations, and downstream traces;
- lower semantic blur than finish;
- lower topology debt than lighting;
- safer proof of scoped preview without changing product root or quote mode.

Proposed MVP:

- request `component_scope=return_cant`;
- respond with scoped return inputs, missing fields, source/state summary, blockers, and preview outputs;
- include `modelare_cant` ProductDefinition trace;
- preserve no-write boundary badges.

## 8. Risks

Main risks identified while defining the contract:

- face may look stronger than confirmed truth if fallback material/thickness is not surfaced visibly;
- finish may collapse material/service/artwork into one unsafe pseudo-price narrative if labels are careless;
- lighting may imply electrical completeness before zones/circuits/service access are modeled;
- premount/support may blur support truth with mounting truth if the bridge is presented as canonical truth;
- unsupported scopes must fail closed and must not silently revert to full product summary.

## 9. Future UI contract

Recommended UI shape, not implementation:

- place in Intake V6 Review;
- read-only only;
- default product summary plus optional component-scope selector;
- surface readiness, inputs, missing fields, source/state, preview outputs, blockers;
- always show boundary badges:
  - `read-only`
  - `no component root`
  - `no component quote`
  - `no order`
  - `no execution`

Must not exist:

- component quote CTA;
- order CTA;
- execution CTA;
- official price;
- tasks;
- stock actions.

## 10. Future tests required

Minimum future tests documented:

1. `return_cant` request keeps `root_type=product_template` and `quote_mode=product_total`.
2. shared component root request returns `COMPONENT_ROOT_BLOCKED`.
3. response includes source/state summary.
4. response includes blockers for missing required fields.
5. response excludes official commercial price.
6. response produces no order/execution/task/stock side effects.
7. Logo candidate cannot be requested as root.
8. unsupported scope returns `not_supported`.

## 11. No-code confirmation

This slice created documentation only.

Confirmed not changed:

- no backend runtime code;
- no frontend runtime code;
- no tests;
- no seeds;
- no migrations;
- no server startup;
- no build or test execution.

## 12. Forbidden scope confirmation

Still forbidden after this contract work:

- component root;
- component quote;
- Logo offerability;
- Pricing changes;
- Quote / Order changes;
- Execution changes;
- ProductAggregate changes;
- TaskGraph changes;
- ExecutionPlan changes;
- DB / seed / migration changes;
- new cleanup around `TPL-VOLUMETRIC-MOUNTING-STRUCTURE_v1`.

## 13. Output files

Created for this slice:

- `docs/architecture/product-system/INTAKE_V6_COMPONENT_CALCULATION_PREVIEW_CONTRACT.md`
- `docs/qa/intake-v6-component-calculation-preview-contract-2026-07-08/INTAKE_V6_COMPONENT_CALCULATION_PREVIEW_CONTRACT_V1.md`
- `docs/worklog/realignment/2026-07-08_intake_v6_component_calculation_preview_contract_v1.md`

## 14. Recommended next slice

Recommended implementation prompt:

```text
INTAKE_V6_RETURN_CANT_COMPONENT_PREVIEW_READONLY_SLICE_V1
```

Alternative audit prompt if more ownership mapping is needed first:

```text
FORM_SYSTEM_COMPONENT_FIELD_OWNERSHIP_MAP_V1
```