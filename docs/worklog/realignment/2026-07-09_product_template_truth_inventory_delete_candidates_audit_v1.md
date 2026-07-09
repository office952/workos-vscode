# PRODUCT_TEMPLATE_TRUTH_INVENTORY_AND_DELETE_CANDIDATES_AUDIT_V1

## Scope

- Audit only.
- No delete.
- No code change.
- No frontend change.
- No backend change.
- No seed change.
- No DB change.
- No migration.
- No live seed.
- No Pricing, Quote/Order, Execution, ProductDefinition, Product Truth writer, or ProductAggregate runtime write changes.

## HEAD before

- `23075eb`

## Files read

- `docs/worklog/realignment/2026-07-09_component_templates_calculation_ownership_alignment_v1.md`
- `docs/worklog/realignment/2026-07-09_return_cant_component_source_path_alignment_readonly_v1.md`
- `docs/architecture/product-system/PRODUCT_SYSTEM_PRODUCT_TEMPLATE_VS_COMPONENT_TEMPLATE_CONTRACT.md`
- `docs/architecture/product-system/PRODUCT_SYSTEM_COMPONENT_OWNED_CALCULATION_BOUNDARY.md`
- `docs/architecture/product-system/PRODUCT_SYSTEM_COMPONENT_LEVEL_CALCULATION_READINESS.md`
- `docs/architecture/product-system/FORM_SYSTEM_COMPONENT_FIELD_OWNERSHIP_MAP.md`
- `docs/architecture/product-system/RETURN_CANT_COMPONENT_CONFIRMATION_CONTRACT.md`
- `frontend/src/pages/ProductSystem.tsx`
- `frontend/src/pages/ProductSystem.badges.test.tsx`
- `backend/seeds/seed_tpl_volumetric_letters_v2.py`
- `backend/seeds/seed_tpl_volumetric_logo_v1.py`
- `backend/seeds/seed_tpl_volumetric_letters_dossier.py`
- `backend/data/mini_module_registry_volumetric_v2.py`
- `backend/data/shared_volumetric_component_contracts.py`
- `backend/services/intake_v6_modular_form_contract_service.py`
- `backend/services/product_template_availability_service.py`
- `backend/services/product_aggregate_service.py`
- `backend/services/template_architecture_scope.py`
- `backend/models/product_templates.py`

## Searches run

- `TPL-VOLUMETRIC-LETTERS_v2`
- `TPL-VOLUMETRIC-LOGO_v1`
- `TPL-VOLUMETRIC-FACE_v1`
- `TPL-VOLUMETRIC-BACK_v1`
- `TPL-VOLUMETRIC-RETURN`
- `TPL-VOLUM-ALUMINIU_v1`
- `TPL-VOLUMETRIC-LED_v1`
- `TPL-VOLUMETRIC-FINISH_v1`
- `TPL-METAL-PREMOUNT-STRUCTURE_v1`
- `return_cant`
- `modelare_cant`
- `return_depth_mm`
- `return_finish_type`
- `letter_perimeter`
- `volum_aluminiu`
- `comp_lateral_litere`
- `material registry`
- `operation_resource_requirements`
- `field bindings`
- `required fields`
- `ProductAggregate`
- `archived`
- `candidate`
- `parent aggregate only`
- `component-owned source missing`

## Template role audit

### `TPL-VOLUMETRIC-LETTERS_v2`

- Status: active / offerable product.
- Work Intake: yes.
- Runtime role: Product Template root.
- System role: composer.
- What it composes:
  - `TPL-VOLUMETRIC-FACE_v1`
  - `TPL-VOLUMETRIC-BACK_v1`
  - `TPL-VOLUM-ALUMINIU_v1`
  - `TPL-VOLUMETRIC-FINISH_v1`
  - `TPL-VOLUMETRIC-LED_v1`
  - `TPL-METAL-PREMOUNT-STRUCTURE_v1`
- What legitimately remains at parent:
  - inclusion/exclusion of child modules
  - relation type for links
  - product-level availability / offerability
  - product label / family / catalog identity
  - product-level orchestration hints
- What must not remain parent-owned long-term:
  - calculable return/cant truth
  - calculable face/back/lighting truth
  - component material profile truth
  - component confirmation truth
- What is ProductAggregate / read-model only:
  - merged component/material/operation presentation
  - dossier + child template aggregation
  - provenance summary
  - linked module display and warnings
- What is UI-only display:
  - catalog labels
  - readiness badges
  - ownership warnings
- What is suspicious as wrong source of truth:
  - parent template still hosts operations_json / required_materials_json that can look authoritative even when child templates exist
  - v2 dossier is derived from legacy dossier seed and still carries transformed legacy intent

### `TPL-VOLUMETRIC-LOGO_v1`

- Status: candidate product.
- Work Intake: no.
- Runtime role: non-offerable Product Template candidate.
- Structure: yes, seeded with logo-specific child templates and parent component specs.
- Operations/resources: yes, but they are candidate-side modular stubs, not approved runtime offer flow.
- Shared components: directionally yes through shared volumetric contracts, but current logo seed also carries profile-specific child templates (`LOGO-FACE`, `LOGO-RETURN`, `LOGO-BACK`, `LOGO-LIGHTING`, `LOGO-FINISH`, `LOGO-MOUNTING`).
- Pricing: must remain excluded from active commercial flow for now.
- Missing to become full active template:
  - owner GO
  - explicit runtime boundary cleanup between shared components and logo-specific profile children
  - stronger proof that logo child templates are either real component templates or temporary candidate scaffolding

### Component/shared child templates audited

- `TPL-VOLUMETRIC-FACE_v1`
- `TPL-VOLUMETRIC-BACK_v1`
- `TPL-VOLUM-ALUMINIU_v1`
- `TPL-VOLUMETRIC-LED_v1`
- `TPL-VOLUMETRIC-FINISH_v1`
- `TPL-METAL-PREMOUNT-STRUCTURE_v1`

All appear in Product System availability metadata as runtime modules/shared components, not current Work Intake roots.

## Component role audit

| Component | Template code | Current role | What it holds now | What it should hold | Separate calculation status | Materials/operations/fields | Main gap | Parent-owned wrongness |
|---|---|---|---|---|---|---|---|---|
| FATA / VIZUAL | `TPL-VOLUMETRIC-FACE_v1` | component template / shared component | face-facing geometry/material/finish direction via shared contract and aggregate linkage | confirmed face material, thickness, layer refs, finish target | partial | module `debitare_fata`, field bindings include `face_finish_type`, geometry bindings from modular form | material/thickness still partly fallback or draft-shaped | finish/material intent still too easy to infer from parent flow |
| VOLUM ALUMINIU / CANT | `TPL-VOLUM-ALUMINIU_v1` | component template / shared component | material variants, child operations, link contract, form requirements | explicit component-owned depth/material/perimeter/confirmation/layer mapping | partial / blocked | materials and operations exist; field bindings include `return_depth_mm`, `return_finish_type`, `letter_perimeter_m`, module activation | source paths still incomplete | return truth still partly parent/root/context owned |
| CAPAC SPATE | `TPL-VOLUMETRIC-BACK_v1` | component template / shared component | backing mode / back cut direction | explicit back material, back confirmation truth | blocked | `debitare_spate`, `backing_mode`, `back_bevel_enabled` | material remains implicit | parent flow still hosts too much backing interpretation |
| SISTEM LED | `TPL-VOLUMETRIC-LED_v1` | component template / shared component | lighting strategy carrier for letters, LED module/PSU direction | explicit component-owned lighting truth with zones/circuits/service access | read-only / partial | `sistem_led`, `lighting_system_type`, `led_module_count`, PSU values | not fully confirmed | parent/product profile can still masquerade as lighting truth |
| FINISAJ | `TPL-VOLUMETRIC-FINISH_v1` | component template / shared component | finish family / print / laminate / mounting template side-effects | clear finish target and family boundaries | blocked | `finisaje`, `mounting_template_enabled`, `letter_group_finishes` | mixed boundary between face/cant/artwork | parent review setup still carries too much finish authority |
| PREMOUNT / STRUCTURE | `TPL-METAL-PREMOUNT-STRUCTURE_v1` | component template / internal/shared child | optional premount bars, structure contract | explicit support truth separated from derived `metal_support_required` | blocked | `structura_suport`, `mounting_system`, derived quote input bridge | trigger mismatch and support truth missing | parent/product flow still bridges support semantics indirectly |

## Dossier usage audit

### What dossier is good for now

- design-time contract intent
- component list / labels / roles
- mapping material_keys and operation_keys
- task rule intent
- quote readiness notes
- documentation of allowed variants and production assumptions

### What is already wired in runtime

- ProductAggregate reads dossier and merges it with child templates and parent rows
- ProductAggregate derives component rows from dossier sections
- ProductAggregate derives mapping-only material_keys and operation_keys from dossier costengine mapping

### What remains docs/intention only

- much of the structural mapping in `seed_tpl_volumetric_letters_dossier.py`
- many future readiness assumptions and task semantics
- owner-facing design intent for variants and rules

### What must not be treated as executable truth

- dossier labels
- dossier mapping keys by themselves
- legacy template-level variant lists
- any dossier field not consumed by form contract, child template, or aggregate builder

### Important dossier conclusion

`seed_tpl_volumetric_letters_v2.py` builds the v2 dossier by transforming legacy dossier payload from `seed_tpl_volumetric_letters_dossier.py`, where the original template code is still `TPL-VOLUMETRIC-LETTERS`. This is useful for continuity, but it is also a live legacy seam. The dossier is therefore a hybrid of real runtime input plus transformed legacy intent, not a pure component-owned executable source of truth.

## Information inventory matrix

| Template/component | Information | Source path / file | Category | Current owner | Correct owner | Status | Risk | Recommendation |
|---|---|---|---|---|---|---|---|---|
| Letters v2 | module composition | `product_template_module_links` + availability service | B. KEEP_CORRECT_PARENT_COMPOSER | Product Template | Product Template | correct | low | keep |
| Letters v2 | offerability / active status | `product_templates.active` + availability service | B. KEEP_CORRECT_PARENT_COMPOSER | Product Template | Product Template | correct | low | keep |
| Letters v2 | parent operations/material rows | `components_json`, `operations_json`, `required_materials_json` | E. DUPLICATE | Product Template | mixed | duplicated with child templates and aggregate | medium | keep temporarily; migrate first |
| Letters v2 | transformed legacy dossier payload | `seed_tpl_volumetric_letters_v2.py::_v2_dossier_payload` | F. LEGACY_ALIAS | Product Template / dossier | component contracts + parent composition split | active legacy seam | medium | keep temporarily |
| ProductAggregate | merged component/material/operation view | `backend/services/product_aggregate_service.py` | D. DERIVED_READ_MODEL_ONLY | ProductAggregate | ProductAggregate | correct as read model | high if treated as truth | keep read-only |
| Return cant | `return_depth_mm` | modular form + readonly mapper + legacy aliases | C. MOVE_TO_COMPONENT_TEMPLATE | Form System / parent flow | Component Template truth | partial | medium | migrate first |
| Return cant | `material_profile` | child template material gate only | C. MOVE_TO_COMPONENT_TEMPLATE | child catalog gate only | Component Template truth | missing explicit truth | high | migrate first |
| Return cant | `letter_perimeter_m` dependency | root geometry / form binding | H. CONTRADICTS_SYSTEM | root geometry context | face dependency consumed by component | blocked | high | explicit dependency path |
| Return cant | legacy `components.returnCant.*` alias | readonly mapper / draft path references | F. LEGACY_ALIAS | legacy runtime/draft | canonical `components.return_cant.*` | active alias | medium | keep temporarily |
| Return cant | `modelare_cant` module operations | mini-module registry + child seed | A. KEEP_CORRECT_COMPONENT_OWNED | Component Template | Component Template | correct direction | low | keep |
| Finish | `letter_group_finishes` and setup payload | form contract and review flow | I. UNKNOWN_NEEDS_OWNER_DECISION | shared review payload | split between finish + cant + face components | mixed | medium | owner decision required |
| Structure | `metal_support_required` derived bridge | modular form contract derived_quote_input | H. CONTRADICTS_SYSTEM | derived quote input bridge | support component truth | known mismatch | medium | migrate first |
| Logo v1 | candidate status | availability service + shared contracts | B. KEEP_CORRECT_PARENT_COMPOSER | Product Template | Product Template | correct | low | keep candidate |
| Logo profile children | logo-specific face/return/back/etc templates | `seed_tpl_volumetric_logo_v1.py` | I. UNKNOWN_NEEDS_OWNER_DECISION | candidate template family | maybe shared components or temporary profile templates | unresolved | medium | owner decision required |
| Shared contracts | Letters + Logo shared component metadata | `backend/data/shared_volumetric_component_contracts.py` | B. KEEP_CORRECT_PARENT_COMPOSER | architecture metadata | architecture metadata | correct as direction | low | keep |
| UI ownership/readiness labels | Product System panel texts | `frontend/src/pages/ProductSystem.tsx` | D. DERIVED_READ_MODEL_ONLY | UI | UI | correct diagnostic | low | keep |
| Availability role metadata | `ROLE_METADATA_BY_MODULE_CODE` | `product_template_availability_service.py` | I. UNKNOWN_NEEDS_OWNER_DECISION | backend UI metadata | maybe dossier or canonical metadata later | useful but hardcoded | low | keep temporarily |

## Special audit — `TPL-VOLUMETRIC-LETTERS_v2`

### What remains in Product Template

- product identity
- Work Intake offerability
- module composition
- relation type and child linkage
- product-level composer semantics

### What should move toward Component Templates

- return/cant component truth fields
- explicit face material/thickness truth
- back material truth
- support truth
- any calculable component confirmation state

### What is only read model

- ProductAggregate components/materials/operations rollup
- provenance summary
- merged warnings

### What is duplicated

- parent operations/materials versus child template operations/materials
- dossier operation/material keys versus child template definitions
- legacy and canonical path families around `return_cant`

### What is legacy

- source legacy template code `TPL-VOLUMETRIC-LETTERS`
- transformed dossier payload carried into v2
- legacy aliases such as `components.returnCant.*`

### What must not be deleted yet

- legacy dossier seed
- parent template rows used by UI/tests/aggregate fallback
- aliases consumed by readonly mappers/tests

### Delete candidates after owner GO only

- duplicated parent material/operation rows once child templates and consumers fully own them
- legacy alias-only references once canonical path migration completes

## Special audit — VOLUM ALUMINIU / CANT

### What exists for separate calculation today

- child template `TPL-VOLUM-ALUMINIU_v1`
- mini-module `modelare_cant`
- child operations:
  - `RETURN_PROFILE_MACHINE_FORMING`
  - `RETURN_PROFILE_FACE_BONDING`
  - `PAINTING`
- child material variants:
  - `MAT-PROFIL-LATERAL-LITERE-30MM`
  - `MAT-PROFIL-LATERAL-LITERE-60MM`
  - `MAT-PROFIL-LATERAL-LITERE-80MM`
  - `MAT-PROFIL-LATERAL-LITERE-100MM`
  - `MAT-ORACAL-651`
  - `MAT-VOPSEA-RAL`
  - `MAT-ADEZIV-CANT-LITERE`
- form contract bindings:
  - `return_depth_mm`
  - `return_finish_type`
  - `volum_aluminum_module_template_code`
  - `letter_perimeter_m`

### What is missing for separate calculation

- explicit `material_profile` truth path
- explicit `perimeter_source` dependency path
- explicit `layer_group_ids`
- explicit `confirmation_state`
- explicit resource authorization/machine mapping surfaced as trusted component-owned support data

### What is correct in component

- component template existence
- module code existence
- operation definitions
- material variant gates
- child dossier intent

### What is wrong in parent/root context

- depth and finish still read as review/setup hydration instead of confirmed component truth
- perimeter still behaves as root geometry context
- support from aggregate/parent traces can look more authoritative than they should

### What comes from Form System

- `return_depth_mm`
- `return_finish_type`
- module activation code
- `letter_group_finishes`
- `letter_perimeter_m`

### What comes from readonly mapper

- canonical target language under `components.return_cant.*`
- blockers and dependency warnings
- legacy alias translation

### What comes from seed/registry

- operations and materials in `seed_tpl_volumetric_letters_v2.py`
- module contract in `mini_module_registry_volumetric_v2.py`
- child template linkage via module links

### What comes only from docs/dossier

- final canonical confirmation semantics
- final perimeter dependency contract
- final missing truth field contracts

### Legacy alias inventory

- `components.return.depth_mm`
- `components.returnCant.depthMm`
- `components.returnCant.finishType`
- `components.returnCant.colorCode`

### Delete candidate after migration only

- legacy alias references around `components.returnCant.*`
- any parent-only fallback rows that duplicate child template return operations/materials

## Special audit — `TPL-VOLUMETRIC-LOGO_v1`

- Current role: candidate Product Template.
- Status: not Work Intake offerable.
- Archived: no explicit evidence of archived; it is candidate, not archived.
- Linked child only: not exactly; it is a candidate parent product that also participates in shared component contracts and has logo-specific child profile templates.
- Structure: yes, it has parent component specs and logo-specific child seeds.
- Operations/resources active: yes as candidate modular data, but not approved active commercial root behavior.
- Shared components used: yes in shared contract metadata for face/back/return/lighting/finish/mounting.
- What does not correspond cleanly with the system:
  - shared-component direction says Logo should reuse the same six shared components
  - logo seed also creates dedicated logo-face/logo-return/logo-back/logo-lighting/logo-finish/logo-mounting templates
  - this looks like profile-specific scaffolding that can drift into duplicated component logic
- Candidate delete risk:
  - the logo-specific child template family may contain future dead pieces, but there is not enough evidence to delete now
  - these should remain owner-decision-required until the shared-component versus profile-template boundary is explicitly settled
- What must not be activated yet:
  - Work Intake root
  - Pricing flow
  - any claim that Logo is quote-offerable

## DELETE_CANDIDATES_PENDING_OWNER_GO

| Path / key | What it is | Why candidate | Why not now | Risk if deleted | Pre-delete verification | Recommendation |
|---|---|---|---|---|---|---|
| parent `operations_json` / `required_materials_json` rows in `TPL-VOLUMETRIC-LETTERS_v2` that duplicate child templates | duplicated parent payload | child templates already model component operations/materials | UI, ProductAggregate, tests may still read them | breaks aggregate/UI/test expectations | zero-import and runtime/aggregate proof | migrate first |
| legacy `components.returnCant.*` aliases | legacy return/cant path family | canonical target is `components.return_cant.*` | readonly mappers and tests still depend on alias awareness | false breakage in diagnostics and adapters | full path migration proof | keep temporarily |
| legacy dossier seed for `TPL-VOLUMETRIC-LETTERS` | old dossier source payload | v2 dossier is transformed from it | v2 build still consumes it | breaks dossier generation chain | replace `_dossier_payload()` dependency first | keep temporarily |
| logo-specific profile child templates (`TPL-VOLUMETRIC-LOGO-FACE_v1`, `...RETURN_v1`, `...BACK_v1`, `...LIGHTING_v1`, `...FINISH_v1`, `...MOUNTING_v1`) | candidate logo sub-template family | may duplicate shared component direction | owner has not chosen between shared-only vs profile-template model | deleting could remove current candidate/runtime references and tests | explicit owner decision on Logo architecture | owner decision required |
| hardcoded availability role metadata | backend-side UI metadata map | may later move to canonical metadata | still drives current Product System labels | UI role labels regress | replacement metadata path | keep temporarily |
| trigger field bridge `metal_support_required` semantics | derived bridge, not pure delete target | known mismatch with mounting_system | still supports current flows | breaks optional structure semantics | support truth migration task | migrate first |

## MOVE_TO_COMPONENT_TEMPLATE_CANDIDATES

| Information | Current source | Current owner | Recommended target | Why move | Test needed after move | Risk / dependencies |
|---|---|---|---|---|---|---|
| `return_depth_mm` as confirmed truth | `finish_setup.return_depth_mm` + aliases | Form System / parent flow | `components.return_cant.depth_mm` | calculable component truth must live on component boundary | readonly mapper + Product System source-path test | affects UI, Form System, Pricing inputs later |
| `material_profile` | child material gate only | child catalog consequence | `components.return_cant.material_profile` | required for separate calculation | readonly mapper + component preview test | affects UI, ProductAggregate, Pricing later |
| `perimeter_source` | `quote_geometry.letter_perimeter_m` context | root geometry context | `components.return_cant.perimeter_source` + face dependency path | remove parent/root truth leakage | dependency/readiness tests | affects UI, ProductAggregate, Form System explanations |
| `layer_group_ids` | selected refs / layer roles / group rows | product/root context | `components.return_cant.layer_group_ids` | component-scoped finish and segmentation need explicit mapping | readonly mapper + source-path audit UI test | affects UI and Form System boundary |
| `confirmation_state` | workflow/global confirmations | product/root workflow | `components.return_cant.confirmation_state` | component confirmation cannot be inferred from row/global confirms | confirmation contract tests | affects UI/readiness only until writer task |
| back material truth | implicit from backing mode | parent/back flow | component-owned back material field | avoid implicit component calculations | back component audit test | affects UI, ProductAggregate, Pricing later |
| support truth | `metal_support_required` derived bridge | quote_input derived | support component truth field | derived consequence should not be primary truth | support/mounting boundary tests | affects Form System, ProductAggregate, Pricing later |

## CONTRADICTIONS_WITH_SYSTEM

| Contradiction | Why it contradicts system |
|---|---|
| Parent template still carries duplicated component operations/materials while component templates also exist | Product Template should compose, not remain de facto component source |
| `return_depth_mm` and `return_finish_type` still live primarily as review/setup input | calculable truth should be component-owned |
| `letter_perimeter_m` still acts as root context rather than explicit face dependency for cant | component dependency boundary is not explicit |
| Logo shared-component contract and logo-specific child template family coexist | architecture direction and candidate implementation are not fully aligned |
| Dossier is transformed from legacy `TPL-VOLUMETRIC-LETTERS` payload into v2 | legacy intent and current runtime are coupled |
| `metal_support_required` bridge still stands in for support truth | derived consequence is acting too close to source truth |
| ProductAggregate can look authoritative because it merges everything in one place | ProductAggregate is read model only, not primary truth |

## WHAT_MUST_NOT_BE_DELETED_YET

- `TPL-VOLUMETRIC-LOGO_v1` candidate parent template
- logo candidate references in Product System UI and tests
- logo-specific child templates until owner picks shared-only versus profile-template direction
- legacy dossier seed feeding v2 dossier transformation
- parent operations/materials still consumed by ProductAggregate/UI/tests
- readonly alias handling for `components.returnCant.*`
- shared contract metadata used by Product System panels
- any source used by readonly ownership/source-path panels

## Risks

- deleting parent duplicates too early could break ProductAggregate output, Product System catalog/detail, or tests
- deleting logo-specific children too early could erase current candidate/runtime references before architecture decision
- treating dossier as executable truth would overstate current runtime alignment
- treating ProductAggregate as source of truth would hide missing component-owned fields

## Recommendation

1. Owner should approve a move plan before any delete plan.
2. First migration target should be `return_cant` canonical container and dependency path completion.
3. After that, run a dedicated audit on parent duplicated operations/materials for letters v2.
4. Logo needs a separate owner decision: shared-component-only future or profile-template family retained.
5. Only after those two decisions should a delete task be opened.

## Forbidden scope confirmation

- no delete performed
- no code modified by this audit
- no frontend modified
- no backend modified
- no seed modified
- no DB migration
- no live seed
- no Pricing
- no ProductDefinition
- no Product Truth writer change
- no UI mutation
- no ProductAggregate runtime write

## Next recommended prompt

```text
TASK — RETURN_CANT_COMPONENT_TRUTH_CONTAINER_READONLY_ALIGNMENT_V1
```

Recommended boundary:

- docs/UI audit or readonly display only
- align `components.return_cant.instances.*` language across Product System and readonly mapper
- make dependency on `components.face.confirmed_perimeter` explicit
- no Pricing
- no ProductDefinition
- no writer
- no delete
