# PRICING_FOUNDATION_V1 — Shared Classification Map

| entity code | current type | typed_catalog | source table | UI destination | cost meaning | notes |
|-------------|--------------|---------------|--------------|----------------|--------------|-------|
| MAT-* | inventory material | material | inventory_materials | Preturi materiale | purchase_cost | Cost achiziție label |
| CNC_ROUTER | workcenter | machine_operation | workcenter_rates | Operații utilaje · CNC mecanic | reusable_rate | |
| ACM_PANEL_CUTTING | workcenter | machine_operation | workcenter_rates | Operații utilaje · CNC mecanic | reusable_rate | |
| ACM_V_GROOVE | workcenter | machine_operation | workcenter_rates | Operații utilaje · CNC mecanic | reusable_rate | |
| LASER_CUTTING | workcenter | machine_operation | workcenter_rates | Operații utilaje · CNC laser | reusable_rate | often missing_price |
| RETURN_PROFILE_MACHINE_FORMING | workcenter | machine_operation | workcenter_rates | Operații utilaje | reusable_rate | |
| WC_METAL_FAB | workcenter | machine_operation | workcenter_rates | Operații utilaje · Alt utilaj | reusable_rate | |
| *_LABOR / ASSEMBLY / LED_ASSEMBLY / … | workcenter | labor | workcenter_rates | Manoperă și servicii | reusable_rate | |
| LAMINATION / LARGE_FORMAT_PRINT / SITE_INSTALLATION_STANDARD / … | workcenter | service | workcenter_rates | Manoperă și servicii | reusable_rate | |
| unmapped WC codes | workcenter | unknown | workcenter_rates | Manoperă și servicii · Necesită clasificare | reusable_rate | visible fallback |
| MARKUP-* | markup | markup_rule | commercial_markup_policies | Adaos | markup | unchanged |

## Inventory UI tabs (live category)

| category examples | tab |
|-------------------|-----|
| panou_compozit, plexiglas, forex | Plăci |
| vinyl, banner, mesh, laminare | Role |
| ink / litru consumabile | Cerneală |
| iluminat_led, profil_metal, consumabile, other | Altele |

## Rate-basis mismatch (detect only)

Flag `rate_basis_column_mismatch` when declared basis ≠ populated column.
Known affected active patterns: `per_square_meter` / `per_piece` values stored in `rate_per_linear_meter`.
No auto-rewrite in this build.
