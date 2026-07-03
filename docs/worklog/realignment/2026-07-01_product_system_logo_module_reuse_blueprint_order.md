# PRODUCT SYSTEM — LOGO MODULE REUSE + BLUEPRINT ORDER

## Scope

Urgent controlled audit for `TPL-VOLUMETRIC-LOGO_v1` with two objectives:

1. verify whether logo child templates can be safely replaced by common reusable volumetric modules;
2. fix owner-facing `Blueprint vertical` order without broad architecture churn.

## Findings

### 1. Module reuse is not a safe drop-in swap

Current logo flow is semantically coupled to dedicated `logo_*` contracts across:

- `backend/data/mini_module_registry_volumetric_v2.py`
- `backend/services/intake_v6_pilot_contract_seed.py`
- `backend/services/product_definition_builder_service.py`
- `backend/services/product_aggregate_service.py`

The live Product System DB links for `TPL-VOLUMETRIC-LOGO_v1` point to dedicated logo child templates, not to the common letters modules. That is currently consistent with the registry and preview pipeline.

### 2. Backend structural order was corrected in seed

`backend/seeds/seed_tpl_volumetric_logo_v1.py` now seeds parent dossier components in canonical order:

1. `comp_logo_face`
2. `comp_logo_finish`
3. `comp_logo_return`
4. `comp_logo_back`
5. `comp_logo_lighting`
6. `comp_logo_mounting`

`backend/tests/test_seed_tpl_volumetric_logo_v1.py` was updated to lock this order and idempotent reruns.

### 3. UI mismatch root cause

The owner-facing `Blueprint vertical` mismatch was not caused by the seed after the canonical reorder.

Observed runtime split:

- direct backend probe from the local repo returned `modules.required[*].display_order = 1..6` in the canonical order;
- same-origin aggregate payload consumed by the Product System page on `http://127.0.0.1:3001` returned `aggregate.components` in canonical order, but `modules.required[*].display_order = null`.

Because `frontend/src/features/product-system/TemplateLibraryView.tsx` sorted layers by:

1. required before optional
2. `displayOrder`
3. `template_code`

the missing `display_order` values caused an alphabetical fallback:

- BACK
- FACE
- FINISH
- LIGHTING
- MOUNTING
- RETURN

## Controlled remediation

Implemented a narrow UI fallback in `frontend/src/features/product-system/TemplateLibraryView.tsx`:

- when `aggregate.modules.*[*].display_order` is missing,
- derive layer order from `aggregate.components[*].source_template_code -> display_order`.

This preserves the existing contract when module display order is present, while repairing the owner-facing list for payloads that only carry the component order.

Focused validation added in `frontend/src/features/product-system/TemplateLibraryView.test.tsx`.

## Validation

- backend: `pytest tests/test_seed_tpl_volumetric_logo_v1.py tests/test_intake_v6_assembly_preview.py` previously passed after seed reorder
- frontend: `pnpm.cmd exec vitest run src/features/product-system/TemplateLibraryView.test.tsx` passed after the UI fallback
- type/errors: no errors reported in touched frontend files

## Reuse classification

| child_logo_template | modul comun echivalent | verdict | motiv |
| --- | --- | --- | --- |
| `TPL-VOLUMETRIC-LOGO-FACE_v1` | `TPL-VOLUMETRIC-FACE_v1` / `debitare_fata` | unsafe now | logo flow uses `logo_face`, `logo_face_print`, `logo_face_laminate`, `logo_area` semantics and dedicated field bindings |
| `TPL-VOLUMETRIC-LOGO-FINISH_v1` | `TPL-VOLUMETRIC-FINISH_v1` / `finisaje` | unsafe now | logo finish is bound to `print_media`, `laminate_media`, artwork-driven logic and `logo_finish_application` |
| `TPL-VOLUMETRIC-LOGO-RETURN_v1` | `TPL-VOLUM-ALUMINIU_v1` / `modelare_cant` | unsafe now | logo return uses `logo_return_profile`, `logo_perimeter`, and dedicated logo return operations |
| `TPL-VOLUMETRIC-LOGO-BACK_v1` | `TPL-VOLUMETRIC-BACK_v1` / `debitare_spate` | unsafe now | current preview and contracts reference `logo_back_material` and `comp_logo_back` semantics |
| `TPL-VOLUMETRIC-LOGO-LIGHTING_v1` | `TPL-VOLUMETRIC-LED_v1` / `sistem_led` | unsafe now | logo lighting uses dedicated `logo_led_modules`, `logo_psu_count`, and logo-specific operation codes |
| `TPL-VOLUMETRIC-LOGO-MOUNTING_v1` | `TPL-METAL-PREMOUNT-STRUCTURE_v1` / `structura_suport` | unsafe now | mounting is modeled as logo-specific mounting template/install behavior, not as generic premount structure |

## Final position

- Safe now: keep dedicated logo child templates.
- Safe now: enforce canonical blueprint order in seed and add UI fallback when backend module display order is absent.
- Not safe now: replace live logo child links with common volumetric modules without a broader contract redesign across registry, pilot seed, aggregate mapping, and ProductDefinition preview.

## Follow-up UI separation

Owner decision after the audit: do not mix sellable product templates with technical reusable modules in the same primary surface.

Implemented in `frontend/src/features/product-system/TemplateLibraryView.tsx`:

- new `Template-uri produs` tab showing only assembly/product templates derived purely from existing aggregate/catalog links;
- new `Componente / module reutilizabile` tab showing child modules and technical templates;
- component chips rendered under each product template card;
- chip hover shows component code, shared/specific status, and `used by templates` list;
- chip click switches to the Components tab and focuses the selected module;
- conservative component filters: `Toate`, `Shared`, `Specific`, `Orphans`.

Classification stays frontend-only and non-destructive:

- product template = template with outgoing linked modules in aggregate/catalog;
- reusable component = remaining technical template without outgoing assembly structure;
- shared = used by more than one parent template;
- specific = used by zero or one parent template;
- orphan = used by zero parent templates.

Focused validation:

- `pnpm.cmd exec vitest run src/features/product-system/TemplateLibraryView.test.tsx` passed with coverage for:
	- canonical Blueprint vertical order fallback from aggregate components;
	- product-vs-component separation;
	- chip click switching into Components.