# Product System Seed — TPL-VOLUMETRIC-LOGO_v1

## Preflight
- `product_templates`: no live rows for `TPL-VOLUMETRIC-LOGO_v1` or child templates `FACE/RETURN/BACK/LIGHTING/FINISH/MOUNTING`.
- `product_template_module_links`: no parent-child links for a logo parent because the parent row was absent.
- `product_blueprint_dossier`: no dossier for a logo parent because the parent row was absent.
- Canonical family source used for seed shape: `TPL-VOLUMETRIC-LETTERS_v2` with `family_id=litere_volumetrice`, `family_name=Litere volumetrice`.

## Seed Scope
- Create/update parent row `TPL-VOLUMETRIC-LOGO_v1`.
- Create/update child rows:
  - `TPL-VOLUMETRIC-LOGO-FACE_v1`
  - `TPL-VOLUMETRIC-LOGO-RETURN_v1`
  - `TPL-VOLUMETRIC-LOGO-BACK_v1`
  - `TPL-VOLUMETRIC-LOGO-LIGHTING_v1`
  - `TPL-VOLUMETRIC-LOGO-FINISH_v1`
  - `TPL-VOLUMETRIC-LOGO-MOUNTING_v1`
- Create/update parent-child links as `required_module`.
- Create/update minimal dossier for parent and child rows.

## Runtime Expectations
- `ProductAggregate` for `TPL-VOLUMETRIC-LOGO_v1` no longer returns 404.
- `modular-form-contract` for `TPL-VOLUMETRIC-LOGO_v1` remains read-only and available.
- `ProductDefinition` preview for `TPL-VOLUMETRIC-LOGO_v1` becomes available once DB rows and links exist.
- `AssemblyPreview` behavior for `IR-MR18L96M` remains unchanged.

## Validation Results
- Focused tests passed: `pytest tests/test_seed_tpl_volumetric_logo_v1.py tests/test_intake_v6_assembly_preview.py` -> `20 passed`.
- First live seed run results:
  - `created_templates = 7`
  - `updated_templates = 0`
  - `created_dossiers = 7`
  - `updated_dossiers = 0`
  - `created_links = 6`
  - `updated_links = 0`
- Second live seed run confirmed idempotency:
  - `created_templates = 0`
  - `updated_templates = 7`
  - `created_dossiers = 0`
  - `updated_dossiers = 7`
  - `created_links = 0`
  - `updated_links = 6`
- Live DB verification confirmed rows exist for:
  - `TPL-VOLUMETRIC-LOGO_v1`
  - `TPL-VOLUMETRIC-LOGO-FACE_v1`
  - `TPL-VOLUMETRIC-LOGO-RETURN_v1`
  - `TPL-VOLUMETRIC-LOGO-BACK_v1`
  - `TPL-VOLUMETRIC-LOGO-LIGHTING_v1`
  - `TPL-VOLUMETRIC-LOGO-FINISH_v1`
  - `TPL-VOLUMETRIC-LOGO-MOUNTING_v1`
- Live DB verification confirmed `6` active `required_module` links from parent to logo child templates.
- Live DB verification confirmed parent dossier exists with `status=approved`, `dossier_version=1`.
- Product System runtime verification after seed:
  - `ProductAggregate(TPL-VOLUMETRIC-LOGO_v1)` resolved with `6` components and `6` required modules.
  - `modular-form-contract(TPL-VOLUMETRIC-LOGO_v1)` resolved with `active_module_count = 7` and attached `product_definition_preview`.
  - `ProductDefinition preview(TPL-VOLUMETRIC-LOGO_v1)` resolved with logo modules available and logo component IDs present.
- Real workspace verification for `IR-MR18L96M` after seed:
  - `assembly_type = letters_logo`
  - `cmp_volumetric_letters -> cnc_sheet_cutting -> MAT-ACP-FATA-LITERE`
  - `cmp_volumetric_logo -> print_vinyl -> MAT-VINYL-PRINT`
  - stale warnings `runtime_target_not_product_template_live` and `logo_template_not_product_system_live` were removed from the rich workspace preview path once logo became live.
  - remaining warning is still real and unchanged: `candidate:opc_cmp_volumetric_logo_face:candidate_not_consolidated_missing_material`.

## Not Touched
- No Cost Engine changes.
- No Quote/Order changes.
- No execution task materialization.
- No UI redesign.
- No Step 1 dropdown behavior changes.