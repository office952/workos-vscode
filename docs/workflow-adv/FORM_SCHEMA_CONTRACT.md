# Form Schema contract

## Purpose
Define the schema-driven Intake contract. The VL 26-field map is the reference implementation, not a universal form UI.

## Ownership
Workflow-ADV owns the reusable field contract. A Product Template owns its schema declaration. Intake renders/captures it; Intake does not own business formulas.

## Required field shape
| Field attribute | Requirement |
|---|---|
| `field_id`, `label`, `type`, `unit`, `required`, `default`, `options` | identity and input semantics |
| `visibility_rule`, `validation_rule` | presentation and acceptance constraints |
| `owner`, `source`, `decision` | accountability and provenance |
| `destinations`, `product_definition_keys`, `child_template_codes` | downstream mapping |
| `quantity_keys`, `cost_lines`, `readiness_keys`, `affects` | declared impact; no hidden consumers |
| `analyzer_candidate`, `analyzer_field`, `confirmation_required` | external-analysis handling |
| `version`, `classification`, `hardcoded_ui`, `consumers` | contract versioning and transferability |

Allowed sources: `OPERATOR`, `ANALYZER_OBSERVED`, `ANALYZER_PROPOSED`, `AI_DEFAULT`, `OWNER_DEFAULT`, `CATALOG`, `DERIVED`.

## VL 26-field reference map
| Field IDs | Primary source | Primary downstream purpose |
|---|---|---|
| `vector_file` | OPERATOR | PD/readiness; specialized file adapter |
| `width_mm`, `height_mm` | OPERATOR | PD/PT, quantities |
| `letter_count`, `letter_perimeter_m`, `letter_face_area_m2` | ANALYZER_OBSERVED | PD/PT after confirmation, quantities/cost |
| `face_finish_type` | OPERATOR | face material/process recipe |
| `return_depth_mm`, `return_finish_type` | OPERATOR | Volum Aluminiu child inputs/recipe |
| `volum_aluminum_module_template_code` | OWNER_DEFAULT | declared child composition |
| `backing_mode`, `back_bevel_enabled` | OPERATOR | backing recipe |
| `lighting_system_type`, `led_module_count`, `selected_psu_watts` | OPERATOR / DERIVED / OPERATOR | lighting recipe and concrete PSU selection |
| `mounting_system`, `mounting_solution` | OPERATOR | support capability/recipe |
| `mains_cable_length_m` | OPERATOR | cable quantity |
| `power_supply_service_corner`, `service_screw_finish` | OPERATOR | optional service/support recipe |
| `mounting_template_enabled`, `mounting_template_area_m2` | OPERATOR | mounting-template activation and quantity |
| `letter_group_finishes` | OPERATOR with ANALYZER_PROPOSED candidate | per-group finish; confirmation required |
| `metal_support_required`, `premount_bar_length_ml`, `bar_material` | DERIVED | premount activation, quantity, and material reference |

## Classification and transfer matrix
| Classification | Transfer rule |
|---|---|
| `reusable_contract` | Transfer field shape and explicit metadata. |
| `vl_specific_schema` | Transfer as template data, not hardcoded application behavior. |
| `vl_specific_ui` | Retain only as a specialized renderer/adapter; do not call it Form Builder. |
| `legacy` / `unsafe_to_transfer` | Exclude as authority. |

## Invariants
- Every field declares source, destination, validation, visibility, version, and downstream impact.
- Analyzer candidates enter PD as observed/proposed data; confirmation is required before PT when declared.
- Operator declares a grouping mode (`by_layer` or `by_color`); no auto-mixing.
- `selected_psu_watts` resolves a concrete priced variant. `MAT-LED-PSU-12V` itself has no generic price.
- A frontend form may validate presentation, but does not recalculate business quantities or EIC.

## Evidence sources
- `GET .../form-field-ownership-map`
- `GET .../analyzer-io-contract`
- `docs/qa/product-system-reference-finish-line-v1/runtime/form_field_ownership_map.json`

## Limitations
The generic Form Builder is deferred. The VL schema is complete as a reference but remains a VL-pilot contract with specialized adapters.

## Do-not-transfer
Do not transfer VL-specific UI fields as universal form components, undeclared field-name consumers, or Analyzer proposals as confirmed field values.

## Related docs
- [Product Definition contract](PRODUCT_DEFINITION_CONTRACT.md)
- [Product Truth contract](PRODUCT_TRUTH_CONTRACT.md)
- [Quantity and Formula contract](QUANTITY_AND_FORMULA_CONTRACT.md)
- [Request-to-cost flow](REQUEST_TO_COST_FLOW.md)
