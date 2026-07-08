# Screenshots Index

Directory:
- `docs/qa/mounting-finish-alias-canonicalization-2026-07-08/screenshots/`

## Captures

1. `01_product_system_overview.png`
   - `/product-system` overview loaded from live UI
   - confirms Product System route/runtime availability for this audit

2. `02_product_system_components_tab.png`
   - shared components view
   - shows finish and mounting as shared component rows

3. `03_product_system_composition_shared_base.png`
   - composition view
   - shows shared volumetric base using `TPL-METAL-PREMOUNT-STRUCTURE_v1`

4. `04_product_system_products_shared_modules.png`
   - products view
   - shows common modules list for Letters and Logo with canonical mounting module code

5. `05_product_system_finish_surface.png`
   - focused finish card
   - shows UI alias `volumetric_finish` mapped to canonical template `TPL-VOLUMETRIC-FINISH_v1`

6. `06_product_system_mounting_surface.png`
   - focused mounting card
   - shows UI alias `volumetric_mounting_structure` mapped to canonical template `TPL-METAL-PREMOUNT-STRUCTURE_v1`

## Proof summary

The screenshot set proves:
- Product System remains reachable after the local fix
- finish stayed stable at `TPL-VOLUMETRIC-FINISH_v1`
- mounting now displays the backend-canonical template code `TPL-METAL-PREMOUNT-STRUCTURE_v1`
- display aliases still exist at UI level, but no longer advertise a conflicting mounting template code