# MOUNTING_AND_FINISH_ALIAS_CANONICALIZATION_AUDIT_V1

Date: 2026-07-08

Scope:
- audit frontend/backend/docs/UI for mounting and finish canonical naming
- decide canonical keys/codes vs tolerated aliases
- apply only a local fix if the mismatch is clear, isolated, and non-behavioral outside Product System UI

Boundary:
- no activation of new root templates
- no QuoteWizard / CostEngine / ProductDefinition behavior change
- no intake contract refactor
- no downstream order/task wiring changes

## Files changed

- frontend/src/pages/ProductSystem.tsx
- frontend/src/features/product-system/TemplateLibraryView.tsx
- frontend/src/features/product-system/TemplateLibraryView.test.tsx
- docs/qa/mounting-finish-alias-canonicalization-2026-07-08/MOUNTING_AND_FINISH_ALIAS_CANONICALIZATION_AUDIT_V1.md
- docs/qa/mounting-finish-alias-canonicalization-2026-07-08/screenshots_index.md
- docs/worklog/realignment/2026-07-08_mounting_and_finish_alias_canonicalization_audit_v1.md

## Commands run

- grep/read-only searches across frontend, backend, docs for mounting and finish aliases
- `npm.cmd run test -- src/features/product-system/TemplateLibraryView.test.tsx` from `frontend/`

Results:
- focused Product System test passed: 13/13
- UI runtime proof captured on `/product-system`

## Executive decision

Decision: AUDIT + LOCAL FIX

Why this stayed local:
- the only confirmed live mismatch was a Product System UI mapping that rendered the stale alias `TPL-VOLUMETRIC-MOUNTING-STRUCTURE_v1`
- backend canonical runtime/template contract already uses `TPL-METAL-PREMOUNT-STRUCTURE_v1`
- finish naming drift in this slice is display-level aliasing, not a conflicting runtime template code

Local fix applied:
- Product System shared volumetric mappings now use `TPL-METAL-PREMOUNT-STRUCTURE_v1`
- display aliases such as `volumetric_finish` and `volumetric_mounting_structure` were left intact because they currently act as UI-facing labels/test ids, not backend truth keys

## Primary findings

### Finding 1 — mounting template code drift was real and unsafe

Canonical backend/runtime evidence consistently points to:
- template code: `TPL-METAL-PREMOUNT-STRUCTURE_v1`
- shared component key: `volumetric_mounting_interface`

Evidence surfaces:
- `backend/services/template_architecture_scope.py`
- `backend/data/shared_volumetric_component_contracts.py`
- `backend/data/mini_module_registry_volumetric_v2.py`
- `backend/services/product_template_availability_service.py`
- `backend/services/active_template_scope.py`

The stale alias `TPL-VOLUMETRIC-MOUNTING-STRUCTURE_v1` appeared in the audited active UI slice as a frontend-only Product System mapping. It is not declared as a backend runtime alias in `RUNTIME_TEMPLATE_CODE_BY_ALIAS` and therefore is a dangerous pseudo-canonical name.

Risk if left unchanged:
- Product System UI would display a mounting module code different from the active backend module code
- future audits could misread a frontend display string as a real registered template
- docs/UI/code drift would widen at the Form System -> Product Truth -> ProductDefinition boundary

### Finding 2 — finish naming drift is alias-layer, not template-code drift

Canonical finish evidence points to:
- template code: `TPL-VOLUMETRIC-FINISH_v1`
- shared component key: `volumetric_surface_finish`

The active UI slice still uses the display alias `volumetric_finish` in some Product System owner labels and test ids. This alias is tolerated in the current slice because it does not claim a different template code and does not conflict with backend runtime resolution.

### Finding 3 — mounting and finish each already have split semantic layers

Mounting separates:
- component contract key: `volumetric_mounting_interface`
- UI alias/display key: `volumetric_mounting_structure`
- intake field: `finish_setup.mounting_system`
- derived quote key: `metal_support_required`
- runtime module/template: `structura_suport` / `TPL-METAL-PREMOUNT-STRUCTURE_v1`

Finish separates:
- component contract key: `volumetric_surface_finish`
- UI alias/display key: `volumetric_finish`
- runtime module/template: `finisaje` / `TPL-VOLUMETRIC-FINISH_v1`
- detailed form fields: `face_finish_type`, `return_finish_type`, `paint_ral_code`, `paint_finish`, `face_vinyl_*`

This layering is acceptable only if display aliases do not drift into fake template codes or overwrite contract keys.

## Mounting alias matrix

| Token / code | Classification | Status | Evidence / notes |
|---|---|---|---|
| `TPL-METAL-PREMOUNT-STRUCTURE_v1` | canonical runtime template code | CANONICAL | backend architecture scope, shared component contracts, mini-module registry, ProductAggregate tests |
| `structura_suport` | canonical module code | CANONICAL | mini-module registry, availability metadata, intake modular form contract |
| `volumetric_mounting_interface` | canonical shared component key | CANONICAL | shared volumetric contracts, Product System mapping |
| `finish_setup.mounting_system` | canonical operator input field | CANONICAL | intake modular form contract service |
| `metal_support_required` | derived quote/input activation flag | CANONICAL_DERIVED | intake modular form contract service; bridge from mounting_system |
| `volumetric_mounting_structure` | UI alias / display owner key | TOLERATED_ALIAS | Product System components/test ids only in audited slice |
| `mounting_structure` | role label / composition role key | TOLERATED_ALIAS | availability metadata and UI composition rows |
| `premount` / `premount_structure` | descriptive operational alias | TOLERATED_ALIAS | mini-module registry / docs; not a competing template code |
| `TPL-VOLUMETRIC-MOUNTING-STRUCTURE_v1` | stale pseudo-canonical template code | DANGEROUS_ALIAS | appeared in Product System frontend mapping; not backed by backend runtime alias resolution |

Answer to mandatory question:
- `TPL-METAL-PREMOUNT-STRUCTURE_v1` is the canonical active template code.
- `TPL-VOLUMETRIC-MOUNTING-STRUCTURE_v1` is a stale alias, not canonical in the audited live slice, and was corrected where it actively misrepresented Product System UI truth.

## Finish alias matrix

| Token / code | Classification | Status | Evidence / notes |
|---|---|---|---|
| `TPL-VOLUMETRIC-FINISH_v1` | canonical runtime template code | CANONICAL | backend architecture scope, availability metadata, Product System mapping |
| `finisaje` | canonical module code | CANONICAL | shared contracts, intake modular contract, availability metadata |
| `volumetric_surface_finish` | canonical shared component key | CANONICAL | shared volumetric contracts, Product System mapping |
| `volumetric_finish` | UI alias / display owner key | TOLERATED_ALIAS | Product System components/test ids only in audited slice |
| `face_finish_type` | canonical detailed face finish field | CANONICAL_FIELD | intake validators and Intake V6 review step |
| `return_finish_type` | canonical detailed return finish field | CANONICAL_FIELD | Intake V6 finish setup sync |
| `paint_ral_code` / `paint_finish` | canonical paint detail fields | CANONICAL_FIELD | backend validators |
| `face_vinyl_roll_width_mm` / `face_vinyl_*` | canonical vinyl detail fields | CANONICAL_FIELD | backend validators and Intake V6 review step |
| `surface_finish` | descriptive concept label | TOLERATED_DOC_ALIAS | aligns conceptually with canonical component key |
| `finish` | generic umbrella label | HAZARDOUS_IF_UNSCOPED | too broad unless explicitly tied to module, component, or field |
| `letter_finish` | ambiguous historical phrase | HAZARDOUS_IF_UNSCOPED | can collapse face/return/artwork distinctions |

## UI proof

Runtime proof confirmed on `/product-system`:
- components view shows `volumetric_finish` mapped to `TPL-VOLUMETRIC-FINISH_v1`
- components view shows `volumetric_mounting_structure` mapped to `TPL-METAL-PREMOUNT-STRUCTURE_v1`
- products/composition views now show the same canonical mounting module code for shared volumetric base

See screenshot index:
- `docs/qa/mounting-finish-alias-canonicalization-2026-07-08/screenshots_index.md`

## Safety verdict

Safe conclusions:
- mounting runtime truth is owned by the backend code path around `TPL-METAL-PREMOUNT-STRUCTURE_v1`
- finish runtime truth is owned by `TPL-VOLUMETRIC-FINISH_v1` and the `volumetric_surface_finish` contract key
- Product System can keep compact display aliases if they stay presentation-only

Unsafe moves deferred out of scope:
- renaming all UI aliases to canonical backend keys in one sweep
- rewriting intake and quote bridges around `metal_support_required`
- treating generic `finish` strings as interchangeable with field-level finish truth
- touching QuoteWizard, CostEngine, ProductDefinition, or execution wiring

## Next safe slice

1. If desired, standardize Product System display keys from `volumetric_finish` / `volumetric_mounting_structure` to canonical contract keys in a dedicated UI-only slice.
2. Audit docs that still present the stale alias `TPL-VOLUMETRIC-MOUNTING-STRUCTURE_v1` as if it were a real active runtime template.
3. Leave intake/quote bridge semantics unchanged unless a dedicated build targets the `mounting_system` -> `metal_support_required` boundary.