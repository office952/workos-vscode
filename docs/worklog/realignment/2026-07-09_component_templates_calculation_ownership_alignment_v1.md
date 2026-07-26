# COMPONENT_TEMPLATES_CALCULATION_OWNERSHIP_ALIGNMENT_V1

## Verdict

`COMPONENT_TEMPLATES_CALCULATION_OWNERSHIP_ALIGNMENT_PASS`

## Scope

- Controlled frontend-only Product System implementation.
- No Pricing, Quote, Order, Execution, ProductDefinition write-path, Product Truth writer, schema, migration, seed, or runtime mutation changes.
- UI proof only: make component calculation ownership visible and honest for `TPL-VOLUMETRIC-LETTERS_v2`.

## Files changed

- `frontend/src/pages/ProductSystem.tsx`
- `frontend/src/pages/ProductSystem.badges.test.tsx`

## What changed

- Added a new read-only `Component calculation ownership` panel in the Product System editor for templates with shared volumetric contracts.
- Explicitly labeled Product Template as composer only.
- Added hard boundaries in the UI: `Read-only`, `No component root`, `No component quote`, `No promote`, `No mutation call`.
- Added per-component ownership cards for:
  - `TPL-VOLUMETRIC-FACE_v1`
  - `TPL-VOLUMETRIC-BACK_v1`
  - `TPL-VOLUM-ALUMINIU_v1`
  - `TPL-VOLUMETRIC-FINISH_v1`
  - `TPL-METAL-PREMOUNT-STRUCTURE_v1`
  - `TPL-VOLUMETRIC-LED_v1`
- Added explicit canonical field keys, Product Truth paths, source/state labels, and warnings.
- Kept VOLUM ALUMINIU / CANT honest: `partial_ready · calculation blocked`, with no fake ready state.
- Added candidate/read-only messaging path for `TPL-VOLUMETRIC-LOGO_v1` when the editor context carries the logo profile.

## Ownership findings captured in UI

### Product Template role

- `TPL-VOLUMETRIC-LETTERS_v2` remains the active product-root composer.
- Product Template still carries fallback, hydrated, or dependency context for component-owned truth.
- The UI now warns that this is an ownership audit surface, not a calculation activation surface.

### VOLUM ALUMINIU / CANT

- Owner boundary shown as `Component Template`.
- Separate calculation shown as `partial_ready · calculation blocked`.
- Canonical field keys shown:
  - `return_depth_mm`
  - `perimeter_source`
  - `material_profile`
  - `finish_type`
  - `color_target`
  - `layer_group_ids`
  - `confirmation_state`
- Honest gaps shown:
  - `material_profile` still missing as component truth
  - `perimeter_source` still a dependency, not a first-class component path
  - `confirmation_state` missing at the component boundary

### LOGO candidate state

- Browser catalog proof confirms `TPL-VOLUMETRIC-LOGO_v1` is still candidate / not Work Intake.
- No activation or offerability changes were made.

## Frontend tests

### Focused Vitest

Command:

```powershell
Set-Location C:\Users\offic\workos_app_vs\frontend
npm.cmd run test -- src/pages/ProductSystem.badges.test.tsx
```

Result:

- `4 passed`

Coverage proved by test:

- composer role badge is rendered
- ownership matrix is visible in Product System editor
- VOLUM ALUMINIU / CANT shows blocked/partial status instead of fake readiness
- canonical field keys are visible
- `source not wired yet` and `component-owned source missing` warnings are visible
- no `Promote` CTA is rendered
- no `ready for future calculation` fake state is rendered

## Backend regression checks

Commands:

```powershell
Set-Location C:\Users\offic\workos_app_vs\backend
.\.venv\Scripts\python.exe -m pytest tests/test_product_truth_writer.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_product_truth_writer_dry_run.py -q
```

Results:

- `tests/test_product_truth_writer.py`: `4 passed`
- `tests/test_product_truth_writer_dry_run.py`: `7 passed`

These confirm the Product Truth writer/dry-run lane remained unaffected by the UI-only ownership change.

## Browser proof

Runtime verified at:

- `http://127.0.0.1:3000/product-system`

Screenshots saved to:

- `docs/worklog/realignment/assets/2026-07-09_component_templates_calculation_ownership_alignment_v1/product_system_products_catalog_context.png`
- `docs/worklog/realignment/assets/2026-07-09_component_templates_calculation_ownership_alignment_v1/product_system_letters_context.png`
- `docs/worklog/realignment/assets/2026-07-09_component_templates_calculation_ownership_alignment_v1/product_system_logo_candidate_context.png`
- `docs/worklog/realignment/assets/2026-07-09_component_templates_calculation_ownership_alignment_v1/product_system_letters_ownership_matrix.png`
- `docs/worklog/realignment/assets/2026-07-09_component_templates_calculation_ownership_alignment_v1/product_system_letters_volum_aluminiu_cant.png`
- `docs/worklog/realignment/assets/2026-07-09_component_templates_calculation_ownership_alignment_v1/product_system_letters_form_system_field_bindings.png`

## Browser findings

- The new ownership panel rendered correctly in the live Product System editor for `TPL-VOLUMETRIC-LETTERS_v2`.
- The products catalog still shows the expected split:
  - `TPL-VOLUMETRIC-LETTERS_v2` offerable
  - `TPL-VOLUMETRIC-LOGO_v1` candidate / not Work Intake
- The Form System field bindings panel loaded, but the page also emitted a separate runtime issue:
  - `cost-bom-preview` request failed due to CORS on `http://127.0.0.1:8000/api/v1/product-system/cost-bom-preview/TPL-VOLUMETRIC-LETTERS_v2`
  - this is outside the scope of this ownership UI task
  - it did not block the required ownership or field-binding proof

## Boundary confirmation

- No promote button added.
- No mutation call added.
- No fake component-ready state added.
- No backend ownership activation added.
- No Product Template to Component Template runtime promotion added.

## Roadmap checkpoint

Current checkpoint after this slice:

```text
Product Template = visible composer
Component Template = visible technical owner candidate
Separate component calculation = still blocked until component-owned sources are wired
```

## Suggested next prompt

```text
TASK — RETURN_CANT_COMPONENT_SOURCE_PATH_ALIGNMENT_READONLY_V1
```

Focus for that next slice:

- align canonical read-only source paths for `return_cant`
- keep product-root flow unchanged
- expose dependency/source-state more explicitly
- do not activate component root or component quote