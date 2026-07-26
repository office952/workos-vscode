# PRODUCT_COMPONENT_COMPOSITION_CONTRACT_V1

## Scope

- Docs and audit only.
- No delete.
- No code change.
- No frontend change.
- No backend change.
- No seed change.
- No DB change.
- No migration.
- No live seed.
- No Pricing, ProductDefinition, Product Truth writer, ProductAggregate runtime write, Quote/Order, or Execution changes.

## HEAD before

- `d86db06`

## Files read

- `docs/worklog/realignment/2026-07-09_product_template_truth_inventory_delete_candidates_audit_v1.md`
- `docs/worklog/realignment/2026-07-09_return_cant_component_source_path_alignment_readonly_v1.md`
- `docs/worklog/realignment/2026-07-09_component_templates_calculation_ownership_alignment_v1.md`
- `docs/architecture/product-system/PRODUCT_SYSTEM_PRODUCT_TEMPLATE_VS_COMPONENT_TEMPLATE_CONTRACT.md`
- `docs/architecture/product-system/PRODUCT_SYSTEM_COMPONENT_OWNED_CALCULATION_BOUNDARY.md`
- `docs/architecture/product-system/PRODUCT_SYSTEM_COMPONENT_LEVEL_CALCULATION_READINESS.md`
- `docs/architecture/product-system/FORM_SYSTEM_COMPONENT_FIELD_OWNERSHIP_MAP.md`
- `docs/architecture/product-system/RETURN_CANT_COMPONENT_CONFIRMATION_CONTRACT.md`
- `backend/seeds/seed_tpl_volumetric_letters_v2.py`
- `backend/seeds/seed_tpl_volumetric_logo_v1.py`
- `backend/seeds/seed_tpl_volumetric_letters_dossier.py`
- `backend/data/mini_module_registry_volumetric_v2.py`
- `backend/data/shared_volumetric_component_contracts.py`
- `backend/services/product_aggregate_service.py`
- `backend/services/product_template_availability_service.py`
- `backend/services/intake_v6_modular_form_contract_service.py`
- `frontend/src/pages/ProductSystem.tsx`
- `frontend/src/pages/ProductSystem.badges.test.tsx`

## Searches run

- `TPL-VOLUMETRIC-LETTERS_v2`
- `TPL-VOLUMETRIC-LOGO_v1`
- `TPL-VOLUMETRIC-FACE_v1`
- `TPL-VOLUMETRIC-BACK_v1`
- `TPL-VOLUMETRIC-RETURN`
- `TPL-VOLUM-ALUMINIU_v1`
- `TPL-VOLUMETRIC-LED_v1`
- `TPL-VOLUMETRIC-FINISH_v1`
- `comp_face_litere`
- `comp_spate_litere`
- `comp_lateral_litere`
- `comp_led_litere`
- `comp_finisaj_litere`
- `face`
- `backing`
- `back`
- `return_cant`
- `volum_aluminiu`
- `modelare_cant`
- `return_depth_mm`
- `return_finish_type`
- `letter_perimeter`
- `selected_layer_refs`
- `ProductAggregate`
- `shared_component_contracts`
- `component role`
- `component template`
- `child template`
- `dossier`
- `composition_modules`
- `components_json`
- `operations_json`
- `required_materials_json`

## Product Template role conclusion

`TPL-VOLUMETRIC-LETTERS_v2 = product composer, nu component truth container.`

Concluzie explicită:

- `TPL-VOLUMETRIC-LETTERS_v2` este Product Template activ și offerable.
- Rolul lui legitim este să compună componentele și să controleze disponibilitatea produsului, nu să țină adevărul calculabil per componentă.
- Ce poate ține legitim la parent:
  - identitatea produsului
  - family / availability / Work Intake offerability
  - child template links și relation types
  - orchestrarea de produs și reguli de compoziție
- Ce nu trebuie să fie truth calculabil la parent:
  - material truth pentru față / spate / cant
  - confirmation truth pentru componente
  - dependency truth pentru `return_cant`
  - explicit component-owned finish/material/perimeter state
- Ce este doar read model:
  - ProductAggregate merged components/materials/operations
  - warnings și provenance summaries
- Ce este legacy / duplicate / support temporar:
  - `components_json`, `operations_json`, `required_materials_json` din parent, unde se suprapun semantic cu child templates
  - dossier v2 derivat din payload legacy `TPL-VOLUMETRIC-LETTERS`
  - aliasuri readonly în jurul `components.returnCant.*`

## STRUCTURAL_COMPONENTS_CONTRACT

Componente structurale obligatorii pentru `TPL-VOLUMETRIC-LETTERS_v2`:

### A. FATA / VISUAL FACE

- Component role: față structural-vizuală a produsului.
- Structural / functional: structural.
- Current component template code: `TPL-VOLUMETRIC-FACE_v1`.
- Current component id: `comp_face_litere`.
- Expected Product Truth path:
  - `components.face.selected_layer_refs`
  - `components.face.material`
  - `components.face.thickness_mm`
  - dependency output toward confirmed perimeter.
- Expected Form System fields:
  - `face_finish_type`
  - geometry fields: `letter_face_area_m2`, `letter_perimeter_m`
  - future component-owned material/thickness confirmation.
- Geometry dependency:
  - face area
  - letter perimeter
  - selected layer refs / layer roles.
- Material dependency:
  - explicit face material is still incomplete.
- Operation dependency:
  - `debitare_fata`
  - `face_cnc_cut` family.
- Finish dependency:
  - finish target still crosses finish boundary.
- Calculation readiness: `partial`.
- Blockers:
  - material not explicitly confirmed
  - thickness path not unified
  - finish target still mixed.
- Actual source:
  - shared component contract + modular form geometry bindings + parent/read model fallback.
- Correct source:
  - component-owned face truth.
- Coherently linked in Letters today: `PARTIAL`.

### B. SPATE / BACKING

- Component role: structural back / closing panel.
- Structural / functional: structural.
- Current component template code: `TPL-VOLUMETRIC-BACK_v1`.
- Current component id: `comp_spate_litere`.
- Expected Product Truth path:
  - `components.back.backing_mode`
  - `components.back.material`
  - `components.back.bevel_enabled`.
- Expected Form System fields:
  - `backing_mode`
  - `back_bevel_enabled`.
- Geometry dependency:
  - back follows face area/outline.
- Material dependency:
  - explicit back material still too implicit.
- Operation dependency:
  - `debitare_spate`
  - `back_cut` family.
- Finish dependency:
  - only if backing finish semantics become explicit later.
- Calculation readiness: `blocked`.
- Blockers:
  - material explicitness
  - backing confirmation path.
- Actual source:
  - backing mode from review/setup plus read model.
- Correct source:
  - component-owned back truth.
- Coherently linked in Letters today: `PARTIAL`.

### C. VOLUM / RETURN / CANT

- Component role: lateral profile / return wall / volumetric side.
- Structural / functional: structural.
- Current component template code: `TPL-VOLUM-ALUMINIU_v1`.
- Current component id: `comp_lateral_litere`.
- Expected Product Truth path:
  - `components.return_cant.depth_mm`
  - `components.return_cant.material_profile`
  - `components.return_cant.finish_type`
  - `components.return_cant.color_target.*`
  - `components.return_cant.layer_group_ids`
  - `components.return_cant.confirmation_state`
  - `components.return_cant.perimeter_source`.
- Expected Form System fields:
  - `return_depth_mm`
  - `return_finish_type`
  - `volum_aluminum_module_template_code`
  - `letter_perimeter_m`
  - `letter_group_finishes`.
- Geometry dependency:
  - explicit dependency on face confirmed perimeter is expected, but not yet owned.
- Material dependency:
  - profile width/material exists as gate in child template, not as component-owned truth.
- Operation dependency:
  - `modelare_cant`
  - `RETURN_PROFILE_MACHINE_FORMING`
  - `RETURN_PROFILE_FACE_BONDING`
  - `PAINTING`.
- Finish dependency:
  - current boundary crosses review setup plus separate finish component.
- Calculation readiness: `partial / blocked`.
- Blockers:
  - `material_profile` missing as truth
  - `perimeter_source` not explicit
  - `layer_group_ids` missing
  - `confirmation_state` missing.
- Actual source:
  - child template + mini-module registry + modular form contract + readonly mapper.
- Correct source:
  - component-owned return/cant truth container.
- Coherently linked in Letters today: `PARTIAL`.

## FUNCTIONAL_COMPONENTS_CONTRACT

### D. SISTEM LED / LIGHTING

- Role: functional lighting/electrical boundary.
- Current component template code: `TPL-VOLUMETRIC-LED_v1`.
- Product Truth target:
  - `components.lighting.illumination_type`
  - `components.lighting.led_module_count`
  - `components.lighting.psu_config`
  - strategy/profile separated from primary truth.
- Depends on structural components:
  - face geometry/area
  - overall product shape
- Component-owned now:
  - strategy direction and LED field contract partially.
- Derived / consequence now:
  - some PSU and strategy aspects remain product-context/profile-like.
- Readiness: `read_only / partial`.
- Blockers:
  - zones/circuits/service access not explicit
  - profile strategy can be mistaken for primary truth.

### E. FINISAJ / FINISH

- Role: functional finish/artwork boundary.
- Current component template code: `TPL-VOLUMETRIC-FINISH_v1`.
- Product Truth target:
  - `components.finish.target`
  - `components.finish.print_required`
  - `components.finish.lamination_required`
  - any split between face/cant/artwork finish scopes.
- Depends on structural components:
  - face
  - return/cant
  - sometimes artwork/logo scope.
- Component-owned now:
  - finish family direction and downstream module identity.
- Derived / consequence now:
  - several finish decisions still live in shared review payload.
- Readiness: `blocked`.
- Blockers:
  - boundary between finish, face, cant, artwork is still mixed.

### F. SUPPORT / MOUNTING / PREMOUNT

- Role: functional support/mounting boundary.
- Current component template code: `TPL-METAL-PREMOUNT-STRUCTURE_v1`.
- Product Truth target:
  - mounting/support truth separate from derived quote input.
- Depends on structural components:
  - width/geometry
  - overall product mounting strategy.
- Component-owned now:
  - child template operations/materials and optional-add-on identity.
- Derived / consequence now:
  - `metal_support_required` bridge remains derived, not primary truth.
- Readiness: `blocked`.
- Blockers:
  - `mounting_system` versus `metal_support_required` mismatch.

## Composition matrix

| component | structural/function | required in Letters? | current component template code | current component id/key | current source path | expected source path | Product Truth path target | Form System fields | geometry dependency | material source | operation source | readiness | blocker | recommendation |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Face | structural | yes | `TPL-VOLUMETRIC-FACE_v1` | `comp_face_litere` | shared contract + geometry bindings + parent/read model fallback | component-owned face truth | `components.face.*` | `face_finish_type`, geometry fields | selected layer refs, area, perimeter | incomplete/fallback | `debitare_fata` | partial | material/thickness/finish target not unified | read-model + truth alignment first |
| Back | structural | yes | `TPL-VOLUMETRIC-BACK_v1` | `comp_spate_litere` | backing mode from review + aggregate/UI | component-owned back truth | `components.back.*` | `backing_mode`, `back_bevel_enabled` | follows face geometry/area | implicit | `debitare_spate` | blocked | back material implicit | make back material explicit first |
| Return/Cant | structural | yes | `TPL-VOLUM-ALUMINIU_v1` | `comp_lateral_litere` | child template + registry + modular form + readonly mapper | component-owned return truth | `components.return_cant.*` | `return_depth_mm`, `return_finish_type`, `letter_perimeter_m` | depends on face confirmed perimeter | child gate only | `modelare_cant` | partial / blocked | missing material/perimeter/layer/confirmation truth | implement component truth container/read-model alignment |
| Lighting | functional | conditional | `TPL-VOLUMETRIC-LED_v1` | `comp_led_litere` | shared contract + review/setup fields | component-owned lighting truth | `components.lighting.*` | `lighting_system_type`, `led_module_count`, PSU fields | face area / overall geometry | partial | `sistem_led` | partial | profile vs truth confusion | keep read-only, clarify truth boundary |
| Finish | functional | yes | `TPL-VOLUMETRIC-FINISH_v1` | `comp_finisaj_litere` | finish setup + group rows + finish module identity | component-owned finish truth | `components.finish.*` | `letter_group_finishes`, mounting template fields | depends on face/cant/artwork scope | mixed | `finisaje` | blocked | finish boundary mixed | split scopes before claiming readiness |
| Mounting/Support | functional | optional | `TPL-METAL-PREMOUNT-STRUCTURE_v1` | `comp_premount_bars` / support boundary | child template + derived bridge | component-owned support truth | support/mounting truth path not yet canonical | `mounting_system` | width/geometry | child template but trigger bridge mismatched | `structura_suport` | blocked | trigger mismatch and derived truth | align support truth before delete/move |

## FATA audit

- Represented by:
  - template `TPL-VOLUMETRIC-FACE_v1`
  - component id `comp_face_litere`
- Layer refs expected to feed it:
  - `selected_layer_refs`
  - layer role setup / face ownership.
- Geometry it needs:
  - face area
  - perimeter
  - width/height context.
- Who owns confirmed perimeter today:
  - not fully formalized as clean component-owned source; it is still the dependency expected by cant but not yet explicit enough in runtime truth.
- Who owns area today:
  - geometry/form bindings, not yet cleanly component-truthed as face-owned truth.
- Who owns face material today:
  - not explicit enough; still partially fallback and parent/review influenced.
- Who owns face cutting operation:
  - `debitare_fata` / face CNC family.
- Who produces dependency for cant:
  - face is the intended upstream owner, but explicit `confirmed_perimeter` dependency path still needs alignment.
- Is there a coherent Product Truth path today:
  - `PARTIAL`.
- Can it be calculated separately:
  - `partial`, not honest-ready.

## SPATE audit

- Represented by:
  - template `TPL-VOLUMETRIC-BACK_v1`
  - component id `comp_spate_litere`
- Material:
  - still too implicit and derivative.
- Operation:
  - `debitare_spate` / back cut family.
- Depends on face geometry:
  - yes, in practice through area/shape relationship.
- Has `backing_mode`:
  - yes.
- Has `back_bevel_enabled`:
  - yes.
- Has coherent Product Truth path:
  - `PARTIAL` only.
- Can be calculated separately:
  - `blocked` until back material and confirmation become explicit.

## VOLUM/CANT audit

- Represented by:
  - template `TPL-VOLUM-ALUMINIU_v1`
  - component id `comp_lateral_litere`
- `TPL-VOLUM-ALUMINIU_v1` is the real boundary:
  - yes, directionally and structurally.
- `comp_lateral_litere` is real component id:
  - yes, in seed, dossier-to-module mapping, ProductAggregate, and registry references.
- What comes from readonly mapper:
  - canonical target language
  - blockers
  - legacy alias interpretation
  - current source-state diagnostics.
- What comes from Form System:
  - `return_depth_mm`
  - `return_finish_type`
  - `letter_perimeter_m`
  - module activation.
- What comes from parent aggregate:
  - display/provenance traces only; must stay read model.
- What comes from seed/registry:
  - operations
  - materials
  - module code
  - workcenter hints
  - gate rules.
- What is missing for separate calculation:
  - `material_profile`
  - explicit `perimeter_source`
  - `layer_group_ids`
  - `confirmation_state`
- Is there explicit dependency on face confirmed perimeter:
  - no, not fully wired as canonical runtime truth.
- Is there component-owned `material_profile`:
  - no.
- Is there component-owned `return_depth_mm`:
  - partial only.
- Is there component-owned `return_finish_type`:
  - partial only.
- Are there `layer_group_ids`:
  - not as component-owned truth.
- Is there `confirmation_state`:
  - not as component-owned truth.
- Can it be calculated separately:
  - `partial / blocked`.

## LOGO audit

- `TPL-VOLUMETRIC-LOGO_v1` is candidate product:
  - yes.
- Work Intake active:
  - no.
- Uses shared components:
  - yes, by contract direction.
- Has own child templates:
  - yes.
- Do those child templates contradict shared reuse direction:
  - partially yes; they create a real ambiguity between profile-specific scaffolding and true shared reuse.
- Should LOGO reuse common FACE/BACK/RETURN/LED/FINISH:
  - yes, directionally.
- Owner decision needed:
  - whether logo-specific child templates remain temporary profile scaffolding or become first-class separate component families.
- What must not be activated yet:
  - Work Intake root
  - Pricing flow
  - any commercial offerability claim.

## DOSSIER_USAGE_CONTRACT

- Dossier in this system = design-time contract, audit memory, and structured intent.
- Runtime-wired part = ProductAggregate consumption of dossier sections and mapping keys.
- Legacy transformed part = `TPL-VOLUMETRIC-LETTERS_v2` dossier built from legacy `TPL-VOLUMETRIC-LETTERS` payload.
- What must not be treated as executable truth:
  - labels
  - variant lists by themselves
  - mapping keys by themselves
  - any section not actively consumed by runtime services.
- What should be promoted later into component-owned source:
  - component-specific required truths that are still only documented
  - explicit dependencies and confirmation states.
- How to avoid using dossier as direct calculation source:
  - keep dossier as contract/read-model input only
  - require runtime-owned component truth paths before calculation.

## DELETE_DEPENDS_ON_COMPOSITION_CONTRACT

- Delete must not happen before composition is explicit because right now duplicate parent rows, legacy aliases, and transformed dossier payload still act as runtime support rails for UI, ProductAggregate, and tests.
- Delete candidates blocked until composition contract is implemented:
  - duplicated parent rows in `TPL-VOLUMETRIC-LETTERS_v2`
  - `components.returnCant.*` alias family
  - some Logo-specific child templates if owner chooses shared-only direction.
- Move candidates required before delete:
  - return/cant truth fields
  - face material/perimeter truth
  - support truth.
- Aliases that must stay temporarily:
  - `components.returnCant.*`
  - legacy dossier transformation path.

## Blockers

- face confirmed perimeter dependency path is not explicit enough
- back material truth is not explicit enough
- return/cant component truth container is incomplete
- finish boundary is still mixed
- support truth is still bridged through derived semantics
- Logo shared-reuse versus logo-child-template direction is unresolved

## Recommendation

1. Next implementation/read-model task should align the component truth container for `return_cant` and the dependency on face perimeter.
2. After that, a composition read-model alignment task should normalize how FATA, SPATE și VOLUM are represented together in Letters.
3. No delete task should start before those two alignment tasks land and owner clarifies the Logo architecture choice.

## Forbidden scope confirmation

- no delete performed
- no code modified
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
TASK — PRODUCT_COMPONENT_COMPOSITION_READ_MODEL_ALIGNMENT_V1
```

Suggested scope:

- still read-only oriented or minimal read-model alignment only
- make the structural trio `FATA + SPATE + VOLUM/CANT` explicit and coherent in ProductAggregate/Product System language
- no Pricing
- no ProductDefinition
- no writer
- no delete
