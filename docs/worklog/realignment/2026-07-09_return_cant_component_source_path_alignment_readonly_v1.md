# RETURN_CANT_COMPONENT_SOURCE_PATH_ALIGNMENT_READONLY_V1

## Verdict

`RETURN_CANT_COMPONENT_SOURCE_PATH_ALIGNMENT_READONLY_PASS`

## Scope

- Read-only Product System alignment for `return_cant` / `VOLUM ALUMINIU / CANT`.
- No Pricing implementation.
- No real calculation.
- No ProductDefinition changes.
- No Product Truth writer changes.
- No UI mutation or promote flow.
- No Quote / Order / Execution changes.
- No ProductAggregate runtime write changes.
- No DB schema / migration / live seed changes.

## HEAD before

- `0067982`

## Files read

- `docs/worklog/realignment/2026-07-09_component_templates_calculation_ownership_alignment_v1.md`
- `docs/architecture/product-system/RETURN_CANT_COMPONENT_CONFIRMATION_CONTRACT.md`
- `docs/architecture/product-system/PRODUCT_SYSTEM_COMPONENT_OWNED_CALCULATION_BOUNDARY.md`
- `docs/architecture/product-system/FORM_SYSTEM_COMPONENT_FIELD_OWNERSHIP_MAP.md`
- `docs/architecture/product-system/PRODUCT_SYSTEM_PRODUCT_TEMPLATE_VS_COMPONENT_TEMPLATE_CONTRACT.md`
- `frontend/src/pages/ProductSystem.tsx`
- `frontend/src/pages/ProductSystem.badges.test.tsx`
- `backend/seeds/seed_tpl_volumetric_letters_v2.py`
- `backend/data/mini_module_registry_volumetric_v2.py`
- `backend/services/intake_v6_modular_form_contract_service.py`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldsReadonlyMapper.ts`
- `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.ts`
- `frontend/src/features/operational-registry/TemplateOperationMappingPanel.tsx`

## Files touched

- `frontend/src/pages/ProductSystem.tsx`
- `frontend/src/pages/ProductSystem.badges.test.tsx`
- `docs/worklog/realignment/2026-07-09_return_cant_component_source_path_alignment_readonly_v1.md`

## Source path findings

### Root rule reaffirmed

- Product Template composes.
- Component Template must own calculable truth.
- ProductAggregate remains read model only.
- UI must show sources and gaps without inventing truth.

### Module / component identity

- Shared child template: `TPL-VOLUM-ALUMINIU_v1`
- Mini-module code: `modelare_cant`
- Dossier component id: `comp_lateral_litere`
- Current product root: `TPL-VOLUMETRIC-LETTERS_v2`

### Field-level source findings for cant

#### `return_depth_mm`

- Current source: `finish_setup.return_depth_mm`
- Legacy aliases still visible in readonly evidence:
  - `components.return.depth_mm`
  - `components.returnCant.depthMm`
- Read-only canonical target now shown in UI as:
  - `components.return_cant.depth_mm`
- Status: `form system only`
- Blocker: `RETURN_CANT_HEIGHT_CONFIRMATION_REQUIRED`

#### `return_finish_type`

- Current source: `finish_setup.return_finish_type`
- Legacy readonly alias: `components.returnCant.finishType`
- Read-only canonical target shown in UI as:
  - `components.return_cant.finish_type`
- Status: `form system only`
- Blocker: `RETURN_CANT_FINISH_MISSING`

#### `letter_perimeter_m`

- Current source: `quote_geometry.letter_perimeter_m`
- Modular form contract binds it to:
  - `geometry_svg`
  - `modelare_cant`
  - `debitare_fata`
- Return/cant readonly mapper still treats this as root geometry context, not confirmed component dependency truth.
- Canonical dependency target shown in UI as:
  - `components.return_cant.perimeter_source -> components.face.confirmed_perimeter`
- Status: `parent aggregate only`
- Blocker: `RETURN_CANT_DEPENDENCY_FACE_GEOMETRY_UNCONFIRMED`

#### `material_profile`

- Current source is only the child template catalog/material gate:
  - `TPL-VOLUM-ALUMINIU_v1.required_materials_json[*]`
  - gated by `return_depth_mm`
- Materials present in component template catalog:
  - `MAT-PROFIL-LATERAL-LITERE-30MM`
  - `MAT-PROFIL-LATERAL-LITERE-60MM`
  - `MAT-PROFIL-LATERAL-LITERE-80MM`
  - `MAT-PROFIL-LATERAL-LITERE-100MM`
- Read-only canonical target shown in UI as:
  - `components.return_cant.material_profile`
- Status: `component-owned source missing`
- Blocker: `RETURN_CANT_MATERIAL_MISSING`

#### Finish / color target

- Current source crosses:
  - `finish_setup.return_finish_type`
  - `return_oracal_code`
  - separate finish boundary `TPL-VOLUMETRIC-FINISH_v1`
- Read-only canonical target shown in UI as:
  - `components.return_cant.finish_type`
  - `components.return_cant.color_target.*`
- Status: `separate finish component`
- Blocker: `RETURN_CANT_FINISH_MISSING`

#### `layer_group_ids`

- Current source remains product/root context only:
  - selected layer refs
  - layer role setup
  - letter group finish rows
- Canonical target remains:
  - `components.return_cant.layer_group_ids`
- Status: missing as component truth
- Blocker: `RETURN_CANT_LAYER_GROUP_SOURCE_MISSING`

#### `confirmation_state`

- Current signals are still global/workflow-level only:
  - `finish_setup.confirmed`
  - row confirmations
  - geometry/workspace confirmations
- Canonical target remains:
  - `components.return_cant.confirmation_state`
- Status: missing as component truth
- Blocker: `RETURN_CANT_SOURCE_STATE_NOT_CONFIRMED`

### Operations findings

- `operation: modelare_cant`
  - source: child template operation `RETURN_PROFILE_MACHINE_FORMING`
  - workcenter: `WC_FORMING`
  - UI status: `component-owned template only`
- `operation: bonding / lipire cant`
  - source: child template operation `RETURN_PROFILE_FACE_BONDING`
  - workcenter: `WC_ASSEMBLY`
  - UI status: `component-owned template only`
- paint labor still exists as child template operation:
  - `PAINTING`
  - workcenter: `WC_PAINT`

### Resources / tools findings

- Explicit child-template workcenter hints exist:
  - `WC_FORMING`
  - `WC_ASSEMBLY`
  - `WC_PAINT`
- Product System already has an operational registry surface pointing to:
  - `operation_resource_requirements`
- But the new read-only cant section does not invent machine/resource mappings beyond that.
- UI status shown: `operation registry missing`
- Blocker shown: `RETURN_CANT_OPERATION_RESOURCE_MAPPING_MISSING`

### Reuse finding for LOGO

- `TPL-VOLUMETRIC-LOGO_v1` still appears as candidate / not Work Intake.
- The new cant source-path section explicitly marks the reuse implication:
  - the same cant boundary should be reusable for Letters and Logo
  - no LOGO activation was added

## Cant separate calculation findings

Current status remains:

```text
partial_ready · calculation blocked
```

Why blocked:

- `material_profile` is still missing as explicit component-owned truth.
- `letter_perimeter_m` is still root/aggregate dependency context, not a confirmed component dependency path.
- `confirmation_state` is still missing at component scope.
- `layer_group_ids` still lack component-scoped mapping.
- finish/color still cross review setup plus separate finish boundary.

## UI changes

- Kept the existing ownership panel.
- Updated the displayed read-only canonical path for depth to:
  - `components.return_cant.depth_mm`
- Added a new section on the `VOLUM ALUMINIU / CANT` card:
  - `Separate calculation source paths`
- Added explicit rows for:
  - material cant / profil aluminiu
  - `return_depth_mm`
  - `return_finish_type`
  - `letter_perimeter_m / perimeter dependency`
  - `operation: modelare_cant`
  - `operation: bonding / lipire cant`
  - `finish source`
  - `resources / tools`
  - `separate calculation readiness`
- Added three visual summary buckets:
  - what we can read now
  - what is still parent aggregate only
  - what must move into Component Template
- Added explicit LOGO reuse note without activating LOGO.

## What owner can verify visually

Owner can now verify in Product System that:

1. `TPL-VOLUM-ALUMINIU_v1` is the real shared child/component boundary for cant.
2. `return_depth_mm` and `return_finish_type` still come from Form System / hydrated review flow, not confirmed component truth.
3. `letter_perimeter_m` is still parent/root dependency context.
4. operations already exist in the child template, but truth inputs are not fully component-owned.
5. resources/tools are still only hinted by workcenters and operational registry boundary, not fully surfaced as component-owned execution truth.
6. separate calculation remains blocked for honest reasons, not hidden by UI.

## What remains missing

- explicit component-owned `material_profile`
- explicit component-owned `perimeter_source`
- explicit component-owned `layer_group_ids`
- explicit component-owned `confirmation_state`
- confirmed dependency path from `components.face.confirmed_perimeter`
- explicit resource / machine mapping surfaced from operational registry when needed

## Screenshots paths

- `docs/worklog/realignment/assets/2026-07-09_return_cant_component_source_path_alignment_readonly_v1/product_system_products_context.png`
- `docs/worklog/realignment/assets/2026-07-09_return_cant_component_source_path_alignment_readonly_v1/product_system_letters_context.png`
- `docs/worklog/realignment/assets/2026-07-09_return_cant_component_source_path_alignment_readonly_v1/product_system_letters_editor_context.png`
- `docs/worklog/realignment/assets/2026-07-09_return_cant_component_source_path_alignment_readonly_v1/product_system_letters_ownership_matrix.png`
- `docs/worklog/realignment/assets/2026-07-09_return_cant_component_source_path_alignment_readonly_v1/product_system_return_cant_source_paths.png`
- `docs/worklog/realignment/assets/2026-07-09_return_cant_component_source_path_alignment_readonly_v1/product_system_return_cant_closeup.png`
- `docs/worklog/realignment/assets/2026-07-09_return_cant_component_source_path_alignment_readonly_v1/product_system_form_system_bindings.png`
- `docs/worklog/realignment/assets/2026-07-09_return_cant_component_source_path_alignment_readonly_v1/product_system_logo_context.png`

## Tests run

```powershell
Set-Location C:\Users\offic\workos_app_vs\frontend
npm.cmd run test -- src/pages/ProductSystem.badges.test.tsx
```

Result:

- `4 passed`

## Backend regressions

```powershell
Set-Location C:\Users\offic\workos_app_vs\backend
.\.venv\Scripts\python.exe -m pytest tests/test_product_truth_writer.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_product_truth_writer_dry_run.py -q
```

Results:

- `4 passed`
- `7 passed`

## Browser note

- Product System browser proof completed at `http://127.0.0.1:3000/product-system`.
- Separate runtime issue still visible in Form System path:
  - `cost-bom-preview` request fails due to CORS
  - out of scope for this slice
  - does not block the required ownership/source-path proof

## Forbidden scope confirmation

- no Pricing
- no ProductDefinition
- no Product Truth writer change
- no promote button
- no UI mutation
- no Quote / Order
- no Execution
- no ProductAggregate runtime write
- no DB migration
- no live seed

## Next recommended prompt

```text
TASK — RETURN_CANT_COMPONENT_TRUTH_CONTAINER_READONLY_ALIGNMENT_V1
```

Recommended boundary:

- stay read-only
- align `components.return_cant.instances.*` shape across Product System and readonly mapper language
- expose dependency path from `components.face.confirmed_perimeter`
- do not activate Pricing, ProductDefinition, writer, or component root