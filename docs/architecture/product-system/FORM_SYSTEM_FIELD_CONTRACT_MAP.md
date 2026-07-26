# Form System Field Contract Map

## 1. Purpose

This contract maps the current Intake V6 UI surfaces into concrete Form System fields. It is the field-level bridge between:

- `INTAKE_V6_UI_SURFACE_INVENTORY_CONTRACT.md`;
- `MATERIAL_CONSUMPTION_AND_NESTING_CONTRACT.md`;
- `INTAKE_V6_PRODUCT_TRUTH_CONTRACT.md`;
- `PRODUCT_SYSTEM_FORM_SYSTEM_COMPOSITION_CONTRACT.md`.

Form System must be able to generate the Intake V6 form from explicit field contracts. The UI must not invent business fields, hide source/state, or promote suggested/hydrated/fallback values into Product Truth.

Every field in this map has a stable `field_id`, UI `surface_id`, owner, source/state vocabulary, Product Truth path, readiness behavior, validation, commercial boundary, and downstream boundary.

This contract does not implement runtime Form System generation, UI changes, backend changes, Pricing, Quote, Order, Execution, ProductAggregate, TaskGraph, ExecutionPlan, DB schema, seeds, or migrations.

Field states are promoted or blocked according to:

`docs/architecture/product-system/PRODUCT_TRUTH_CONFIRMATION_POLICY.md`

Commercial field behavior, display labels, totals, markup/discount controls and quote draft CTA boundaries are governed by:

`docs/architecture/product-system/COMMERCIAL_PREVIEW_BOUNDARY_CONTRACT.md`

## 2. Scope

In scope:

- Pas 1 / Straturi;
- Pas 2 / Review;
- Pas 3 / Confirmare;
- Vector Litere;
- Vector Atipic / Logo;
- Logo-only candidate;
- Lighting;
- Mounting;
- Materials;
- Nesting;
- Roll width;
- Split/panelization;
- Commercial preview boundary;
- Confirmare gates;
- Downstream handoff safety.

Out of scope:

- UI implementation;
- nesting engine implementation;
- split algorithm implementation;
- Pricing formulas;
- Quote/Order;
- Execution;
- ProductAggregate;
- TaskGraph;
- ExecutionPlan;
- DB migration;
- seed data.

## 3. Field Contract Schema

| Property | Meaning | Required? |
| --- | --- | --- |
| `field_id` | stable machine-readable id | yes |
| `surface_id` | linked UI surface id | yes |
| `step` | Intake V6 step | yes |
| `group` | logical form group | yes |
| `label` | operator label | yes |
| `field_type` | `string`, `number`, `select`, `multiselect`, `boolean`, `object`, `array`, `computed`, `read_only` | yes |
| `applies_to` | `gradi`, `litere1`, `litere2`, `logo`, `letters`, `logo_only`, `all` | yes |
| `owner_system` | `svg_analyzer`, `product_system`, `form_system`, `product_truth`, `material_registry`, `operator`, `backend_readiness` | yes |
| `product_truth_path` | canonical Product Truth path | yes |
| `source` | source vocabulary from this contract | yes |
| `state` | state vocabulary from this contract | yes |
| `required_for` | `preview`, `confirmare`, `quote_draft`, `order`, `execution`, `never` | yes |
| `validation` | validation rule | yes |
| `blocker_behavior` | `none`, `warning`, `block_quote`, `block_confirmare`, `block_downstream` | yes |
| `commercial_boundary` | `preview_only`, `quote_ready`, `not_offerable`, `blocked` | yes |
| `downstream_boundary` | `none`, `no_order`, `no_execution`, `gated` | yes |
| `current_status` | `systemic`, `partial`, `ui_only`, `hydrated`, `fallback`, `missing` | yes |
| `notes` | implementation notes | optional |

## 4. Field ID Naming Rules

Examples:

- `iv6.s1.upload.svg_file`
- `iv6.s1.layer_roles.confirmed_role`
- `iv6.s2.letter_group.face.material`
- `iv6.s2.letter_group.face.color`
- `iv6.s2.letter_group.cant.material`
- `iv6.s2.letter_group.cant.depth_mm`
- `iv6.s2.logo_candidate.template_code`
- `iv6.s2.material.roll.selected_width_mm`
- `iv6.s2.material.roll.usable_width_mm`
- `iv6.s2.material.roll.length_used_mm`
- `iv6.s2.material.split.required`
- `iv6.s3.gates.product_truth_ready`

Rules:

- `field_id` must be stable.
- No spaces.
- Do not use volatile UI label text as id.
- Group by step and domain.
- Do not encode Romanian labels in ids.
- Labels may be Romanian; ids remain stable English-like tokens.

## 5. Pas 1 / Straturi Field Map

| field_id | surface_id | label | field_type | applies_to | owner_system | product_truth_path | source | state | required_for | validation | blocker_behavior | current_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `iv6.s1.upload.svg_file` | IV6-S1-UPLOAD | SVG file | object | all | svg_analyzer | `svg.source.file` | svg_analyzer | suggested | preview | file must parse as SVG | block_confirmare | systemic |
| `iv6.s1.svg.file_name` | IV6-S1-UPLOAD | File name | string | all | svg_analyzer | `svg.source.file_name` | svg_analyzer | suggested | preview | non-empty filename | warning | systemic |
| `iv6.s1.svg.file_size_bytes` | IV6-S1-UPLOAD | File size | number | all | svg_analyzer | `svg.source.file_size_bytes` | svg_analyzer | suggested | preview | `>= 0` | warning | systemic |
| `iv6.s1.svg.geometry_units` | IV6-S1-GEOMETRY | Geometry units | string | all | svg_analyzer | `geometry.units` | svg_geometry | suggested | quote_draft | units/scale confidence must be acceptable | block_quote | partial |
| `iv6.s1.layer.layer_id` | IV6-S1-LAYER-ROLE-SETUP | Layer id | string | all | svg_analyzer | `svg.layer_roles[].layer_id` | svg_analyzer | suggested | preview | unique within analysis | warning | systemic |
| `iv6.s1.layer.layer_name` | IV6-S1-LAYER-ROLE-SETUP | Layer name | string | all | svg_analyzer | `svg.layer_roles[].layer_name` | svg_analyzer | suggested | preview | non-empty after analyzer normalization | warning | systemic |
| `iv6.s1.layer.auto_role` | IV6-S1-LAYER-ROLE-SETUP | Auto role | select | all | svg_analyzer | `svg.layer_roles[].auto_role` | svg_analyzer | suggested | preview | role in allowed vocabulary | warning | systemic |
| `iv6.s1.layer.suggested_role` | IV6-S1-LAYER-ROLE-SETUP | Suggested role | select | all | form_system | `svg.layer_roles[].suggested_role` | analyzer_semantic_expansion | suggested | confirmare | role must be reviewable by operator | warning | partial |
| `iv6.s1.layer.confirmed_role` | IV6-S1-LAYER-ROLE-SETUP | Confirmed role | select | all | operator | `svg.layer_roles[].confirmed_role` | operator_confirmed | confirmed | quote_draft | all relevant roles confirmed or ignored | block_confirmare | systemic |
| `iv6.s1.layer.confirmation_state` | IV6-S1-LAYER-ROLE-SETUP | Confirmation state | select | all | operator | `svg.layer_roles[].confirmation_state` | operator_confirmed | confirmed | quote_draft | `confirmed`, `ignored`, or resolved | block_confirmare | systemic |
| `iv6.s1.layer.confidence` | IV6-S1-LAYER-ROLE-SETUP | Analyzer confidence | string | all | svg_analyzer | `svg.layer_roles[].confidence` | svg_analyzer | suggested | preview | advisory only | warning | systemic |
| `iv6.s1.template.candidate_code` | IV6-S1-TEMPLATE-CANDIDATE | Template candidate | string | all | product_system | `template.candidate.code` | analyzer_semantic_expansion | candidate_read_only | preview | candidate must be allowed by template capability | warning | partial |
| `iv6.s1.template.root_offerable` | IV6-S1-TEMPLATE-CANDIDATE | Root offerable | boolean | all | product_system | `template.root_offerability` | backend_readiness | confirmed | quote_draft | false blocks commercial root behavior | block_quote | systemic |
| `iv6.s1.gate.roles_complete` | IV6-S1-LAYER-ROLE-SETUP | Roles complete gate | boolean | all | backend_readiness | `readiness.layer_roles_complete` | backend_readiness | blocked/confirmed | confirmare | `layer_role_setup.confirmation_status == complete` | block_confirmare | systemic |

## 6. Pas 2 / Vector Litere Field Map

Nearest Oracal / analyzer color mapping is `suggested` and `partial` until operator-confirmed. Hydrated cant/return values are not final Product Truth by themselves.

| field_id | surface_id | label | field_type | applies_to | owner_system | product_truth_path | source | state | required_for | validation | blocker_behavior | current_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `iv6.s2.letter_group.group_key` | IV6-S2-VECTOR-LITERE | Letter group key | string | letters | svg_analyzer | `components.letter_groups[].group_key` | svg_analyzer | confirmed | quote_draft | stable per current SVG analysis | block_quote | systemic |
| `iv6.s2.letter_group.layer_name` | IV6-S2-VECTOR-LITERE | Layer name | string | letters | svg_analyzer | `components.letter_groups[].layer_name` | svg_analyzer | confirmed | preview | non-empty | warning | systemic |
| `iv6.s2.letter_group.detected_color` | IV6-S2-LETTER-FACE-FINISH | Detected color | string | letters | svg_analyzer | `components.face_finish.letter_groups.*.detected_color` | svg_geometry | suggested | preview | must match current SVG evidence | warning | partial |
| `iv6.s2.letter_group.nearest_oracal_color` | IV6-S2-LETTER-FACE-FINISH | Nearest Oracal color | object | letters | form_system | `components.face_finish.letter_groups.*.nearest_oracal` | svg_nearest_color_mapping | suggested | quote_draft | operator confirmation required | block_quote | partial |
| `iv6.s2.letter_group.face.material` | IV6-S2-LETTER-FACE-FINISH | Face material | select | letters | form_system | `components.face_finish.letter_groups.*.material` | payload_hydrated_or_prior_state | hydrated | quote_draft | material must be explicit and allowed | block_quote | partial |
| `iv6.s2.letter_group.face.finish` | IV6-S2-LETTER-FACE-FINISH | Face finish | select | letters | form_system | `components.face_finish.letter_groups.*.face_finish` | payload_hydrated_or_prior_state | hydrated | quote_draft | finish type allowed for face material | block_quote | partial |
| `iv6.s2.letter_group.face.color_code` | IV6-S2-LETTER-FACE-FINISH | Face color code | string | letters | form_system | `components.face_finish.letter_groups.*.color_code` | svg_nearest_color_mapping | suggested | quote_draft | Oracal/RAL code required when finish requires color | block_quote | partial |
| `iv6.s2.letter_group.face.source` | IV6-S2-LETTER-FACE-FINISH | Face source | read_only | letters | backend_readiness | `components.face_finish.letter_groups.*.source` | backend_readiness | partial | preview | must be exposed | warning | partial |
| `iv6.s2.letter_group.face.state` | IV6-S2-LETTER-FACE-FINISH | Face state | read_only | letters | backend_readiness | `components.face_finish.letter_groups.*.state` | backend_readiness | partial | quote_draft | `confirmed` required for final truth | block_quote | partial |
| `iv6.s2.letter_group.cant.material` | IV6-S2-LETTER-CANT | Cant material | select | letters | form_system | `components.return_cant.letter_groups.*.material` | payload_hydrated_or_prior_state | hydrated | quote_draft | material/profile must be explicit | block_quote | partial |
| `iv6.s2.letter_group.cant.color` | IV6-S2-LETTER-CANT | Cant color | string | letters | form_system | `components.return_cant.letter_groups.*.color` | payload_hydrated_or_prior_state | hydrated | quote_draft | required when cant finish needs color | block_quote | partial |
| `iv6.s2.letter_group.cant.depth_mm` | IV6-S2-LETTER-CANT | Cant depth | number | letters | form_system | `components.return_cant.letter_groups.*.depth_mm` | payload_hydrated_or_prior_state | hydrated | quote_draft | positive allowed depth | block_quote | partial |
| `iv6.s2.letter_group.cant.source` | IV6-S2-LETTER-CANT | Cant source | read_only | letters | backend_readiness | `components.return_cant.letter_groups.*.source` | backend_readiness | partial | preview | must be exposed | warning | partial |
| `iv6.s2.letter_group.cant.state` | IV6-S2-LETTER-CANT | Cant state | read_only | letters | backend_readiness | `components.return_cant.letter_groups.*.state` | backend_readiness | partial | quote_draft | `confirmed` required for final truth | block_quote | partial |
| `iv6.s2.letter_group.readiness_status` | IV6-S2-VECTOR-LITERE | Row readiness | read_only | letters | backend_readiness | `components.letter_groups.*.readiness_status` | backend_readiness | partial | quote_draft | ready/partial/blocked must be visible | block_quote | partial |

## 7. Pas 2 / Vector Atipic and Logo Candidate Field Map

`TPL-VOLUMETRIC-LOGO_v1` is candidate/read-only. It is not root commercial offerable without owner GO.

| field_id | surface_id | label | field_type | applies_to | owner_system | product_truth_path | source | state | required_for | validation | blocker_behavior | current_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `iv6.s2.artwork.layer_name` | IV6-S2-VECTOR-ATIPIC-LOGO | Artwork layer name | string | gradi,logo | svg_analyzer | `artwork.layers[].layer_name` | svg_analyzer | confirmed | preview | non-empty current layer | warning | systemic |
| `iv6.s2.artwork.role` | IV6-S2-VECTOR-ATIPIC-LOGO | Artwork role | select | gradi,logo | operator | `artwork.layers[].role` | operator_confirmed | confirmed | quote_draft | role must be `printed_artwork` or `logo` when active | block_quote | systemic |
| `iv6.s2.artwork.finish.execution_type` | IV6-S2-VECTOR-ATIPIC-LOGO | Artwork execution type | select | gradi,logo | form_system | `artwork.layers[].finish.execution_type` | payload_persisted | partial | quote_draft | print/laminate/cut decision explicit | block_quote | partial |
| `iv6.s2.logo_candidate.template_code` | IV6-S2-LOGO-ONLY-CANDIDATE | Logo template candidate | string | logo,gradi | product_system | `template.logo_candidate.template_code` | analyzer_semantic_expansion | candidate_read_only | preview | must equal allowed candidate code | warning | systemic |
| `iv6.s2.logo_candidate.root_offerable` | IV6-S2-LOGO-ONLY-CANDIDATE | Logo root offerable | boolean | logo | product_system | `template.logo_candidate.root_offerable` | backend_readiness | not_offerable | quote_draft | false unless owner GO | block_quote | systemic |
| `iv6.s2.logo_candidate.read_only` | IV6-S2-LOGO-ONLY-CANDIDATE | Logo candidate read-only | boolean | logo | product_system | `template.logo_candidate.read_only` | backend_readiness | candidate_read_only | preview | must be true in current flow | warning | systemic |
| `iv6.s2.logo_candidate.not_offerable_reason` | IV6-S2-LOGO-ONLY-CANDIDATE | Not-offerable reason | string | logo | backend_readiness | `readiness.logo_only.reason` | backend_readiness | not_offerable | quote_draft | must be visible when logo-only | block_quote | systemic |
| `iv6.s2.linked_segment.binding_state` | IV6-S2-VECTOR-ATIPIC-LOGO | Linked segment binding state | select | gradi | product_system | `linked_templates.TPL-VOLUMETRIC-LOGO_v1.segments.*.binding_state` | payload_persisted | suggested | quote_draft | confirmed binding required for final Product Truth | block_quote | partial |
| `iv6.s2.linked_segment.readiness_status` | IV6-S2-VECTOR-ATIPIC-LOGO | Linked segment readiness | read_only | gradi | backend_readiness | `linked_templates.TPL-VOLUMETRIC-LOGO_v1.segments.*.readiness_status` | backend_readiness | partial | quote_draft | ready/partial/blocked visible | block_quote | partial |

## 8. Pas 2 / Lighting and Mounting Field Map

Hydrated/default/manual lighting and mounting values remain partial until a confirmation policy upgrades them.

| field_id | surface_id | label | field_type | applies_to | owner_system | product_truth_path | source | state | required_for | validation | blocker_behavior | current_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `iv6.s2.lighting.mode` | IV6-S2-LIGHTING | Lighting mode | select | all | form_system | `components.lighting.mode` | payload_hydrated_or_prior_state | hydrated | quote_draft | explicit mode if illuminated | block_quote | partial |
| `iv6.s2.lighting.led_strategy` | IV6-S2-LIGHTING | LED strategy | select | all | product_system | `components.lighting.strategy_profile` | payload_hydrated_or_prior_state | hydrated | quote_draft | allowed strategy/profile | warning | partial |
| `iv6.s2.lighting.psu_configuration` | IV6-S2-LIGHTING | PSU configuration | array | all | form_system | `components.lighting.psu_configuration` | payload_hydrated_or_prior_state | hydrated | order | valid PSU sizing if illuminated | block_downstream | partial |
| `iv6.s2.lighting.source` | IV6-S2-LIGHTING | Lighting source | read_only | all | backend_readiness | `components.lighting.source` | backend_readiness | partial | preview | source must be visible | warning | missing |
| `iv6.s2.lighting.state` | IV6-S2-LIGHTING | Lighting state | read_only | all | backend_readiness | `components.lighting.state` | backend_readiness | partial | quote_draft | confirmation required when lighting affects product | block_quote | missing |
| `iv6.s2.mounting.type` | IV6-S2-MOUNTING | Mounting type | select | all | form_system | `components.mounting.type` | payload_hydrated_or_prior_state | hydrated | quote_draft | allowed mounting system | block_quote | partial |
| `iv6.s2.mounting.support` | IV6-S2-MOUNTING | Support/backing branch | object | all | form_system | `components.support.*` | fallback_default | fallback | quote_draft | support requirements explicit | block_quote | partial |
| `iv6.s2.mounting.source` | IV6-S2-MOUNTING | Mounting source | read_only | all | backend_readiness | `components.mounting.source` | backend_readiness | partial | preview | source must be visible | warning | missing |
| `iv6.s2.mounting.state` | IV6-S2-MOUNTING | Mounting state | read_only | all | backend_readiness | `components.mounting.state` | backend_readiness | partial | quote_draft | confirmed/manual/fallback distinction required | block_quote | missing |

## 9. Pas 2 / Material Consumption and Nesting Field Map

This section implements the field map required by `MATERIAL_CONSUMPTION_AND_NESTING_CONTRACT.md`.

### Rigid sheet fields

| field_id | surface_id | label | field_type | applies_to | owner_system | product_truth_path | source | state | required_for | validation | blocker_behavior | current_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `iv6.s2.material.rigid.material_code` | IV6-S2-RIGID-SHEET-NESTING | Rigid material code | string | letters | material_registry | `product_truth.material_consumption.rigid_sheets[].material_code` | material_registry | suggested | quote_draft | code exists in material registry | block_quote | partial |
| `iv6.s2.material.rigid.sheet_width_mm` | IV6-S2-RIGID-SHEET-NESTING | Sheet width | number | letters | form_system | `product_truth.material_consumption.rigid_sheets[].sheet_width_mm` | sheet_format_registry | suggested | quote_draft | positive; default `3000` when selected | block_quote | partial |
| `iv6.s2.material.rigid.sheet_height_mm` | IV6-S2-RIGID-SHEET-NESTING | Sheet height | number | letters | form_system | `product_truth.material_consumption.rigid_sheets[].sheet_height_mm` | sheet_format_registry | suggested | quote_draft | positive; default `2000` when selected | block_quote | partial |
| `iv6.s2.material.rigid.sheet_count` | IV6-S2-RIGID-SHEET-NESTING | Sheet count | number | letters | product_truth | `product_truth.material_consumption.rigid_sheets[].sheet_count` | nesting_engine | computed | quote_draft | `>= 1` when material required | block_quote | missing |
| `iv6.s2.material.rigid.geometry_area_mm2` | IV6-S2-MATERIAL-CONSUMPTION-REALITY | Geometry area | number | letters | svg_analyzer | `product_truth.material_consumption.rigid_sheets[].geometry_area_mm2` | svg_geometry | estimate_area_only | preview | non-negative | warning | partial |
| `iv6.s2.material.rigid.nested_consumption_area_mm2` | IV6-S2-RIGID-SHEET-NESTING | Nested consumption area | number | letters | product_truth | `product_truth.material_consumption.rigid_sheets[].nested_consumption_area_mm2` | nesting_engine | computed | quote_draft | required before quote-ready | block_quote | missing |
| `iv6.s2.material.rigid.waste_area_mm2` | IV6-S2-MATERIAL-WASTE-EFFICIENCY | Waste area | number | letters | product_truth | `product_truth.material_consumption.rigid_sheets[].waste_area_mm2` | nesting_engine | computed | quote_draft | `>= 0` | warning | missing |
| `iv6.s2.material.rigid.efficiency_percent` | IV6-S2-MATERIAL-WASTE-EFFICIENCY | Efficiency percent | number | letters | product_truth | `product_truth.material_consumption.rigid_sheets[].efficiency_percent` | nesting_engine | computed | preview | 0-100 | warning | partial |
| `iv6.s2.material.rigid.nesting_status` | IV6-S2-NESTING-PREVIEW | Nesting status | select | letters | backend_readiness | `product_truth.material_consumption.rigid_sheets[].nesting_status` | nesting_preview | partial | quote_draft | `confirmed` required for material-ready | block_quote | partial |
| `iv6.s2.material.rigid.material_consumption_ready` | IV6-S2-MATERIAL-CONSUMPTION-REALITY | Material consumption ready | boolean | letters | backend_readiness | `product_truth.material_consumption.rigid_sheets[].material_consumption_ready` | backend_readiness | blocked | quote_draft | true only after real nesting/split decisions | block_quote | missing |

### Roll material fields

| field_id | surface_id | label | field_type | applies_to | owner_system | product_truth_path | source | state | required_for | validation | blocker_behavior | current_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `iv6.s2.material.roll.material_code` | IV6-S2-ROLL-MATERIAL-NESTING | Roll material code | string | letters,logo | material_registry | `product_truth.material_consumption.roll_materials[].material_code` | material_registry | suggested | quote_draft | code exists in material registry | block_quote | partial |
| `iv6.s2.material.roll.selected_width_mm` | IV6-S2-ROLL-WIDTH-SELECTION | Selected roll width | select | letters,logo | form_system | `product_truth.material_consumption.roll_materials[].selected_roll_width_mm` | form_system_roll_width_field | suggested | quote_draft | one of `1000`, `1260` unless owner override | block_quote | partial |
| `iv6.s2.material.roll.usable_width_mm` | IV6-S2-ROLL-WIDTH-SELECTION | Usable roll width | computed | letters,logo | form_system | `product_truth.material_consumption.roll_materials[].usable_width_mm` | form_system_roll_width_field | computed | quote_draft | selected width minus margins | block_quote | missing |
| `iv6.s2.material.roll.left_margin_mm` | IV6-S2-ROLL-WIDTH-SELECTION | Left margin | number | letters,logo | form_system | `product_truth.material_consumption.roll_materials[].left_margin_mm` | form_system_roll_width_field | computed | quote_draft | default `20` unless override | warning | missing |
| `iv6.s2.material.roll.right_margin_mm` | IV6-S2-ROLL-WIDTH-SELECTION | Right margin | number | letters,logo | form_system | `product_truth.material_consumption.roll_materials[].right_margin_mm` | form_system_roll_width_field | computed | quote_draft | default `20` unless override | warning | missing |
| `iv6.s2.material.roll.length_used_mm` | IV6-S2-ROLL-MATERIAL-NESTING | Roll length used | number | letters,logo | product_truth | `product_truth.material_consumption.roll_materials[].roll_length_used_mm` | nesting_engine | computed | quote_draft | `> 0` when roll material required | block_quote | missing |
| `iv6.s2.material.roll.width_consumption_area_mm2` | IV6-S2-ROLL-MATERIAL-NESTING | Roll width consumption area | computed | letters,logo | product_truth | `product_truth.material_consumption.roll_materials[].roll_width_consumption_area_mm2` | nesting_engine | computed | quote_draft | selected width x length used | block_quote | missing |
| `iv6.s2.material.roll.geometry_area_mm2` | IV6-S2-MATERIAL-CONSUMPTION-REALITY | Roll geometry area | number | letters,logo | svg_analyzer | `product_truth.material_consumption.roll_materials[].geometry_area_mm2` | svg_geometry | estimate_area_only | preview | non-negative; cannot be quote-ready alone | warning | partial |
| `iv6.s2.material.roll.waste_area_mm2` | IV6-S2-MATERIAL-WASTE-EFFICIENCY | Roll waste area | number | letters,logo | product_truth | `product_truth.material_consumption.roll_materials[].waste_area_mm2` | nesting_engine | computed | quote_draft | `>= 0` | warning | missing |
| `iv6.s2.material.roll.efficiency_percent` | IV6-S2-MATERIAL-WASTE-EFFICIENCY | Roll efficiency | number | letters,logo | product_truth | `product_truth.material_consumption.roll_materials[].efficiency_percent` | nesting_engine | computed | preview | 0-100 | warning | missing |
| `iv6.s2.material.roll.nesting_status` | IV6-S2-ROLL-MATERIAL-NESTING | Roll nesting status | select | letters,logo | backend_readiness | `product_truth.material_consumption.roll_materials[].nesting_status` | backend_readiness | partial | quote_draft | computed/confirmed required | block_quote | missing |
| `iv6.s2.material.roll.material_consumption_ready` | IV6-S2-MATERIAL-CONSUMPTION-REALITY | Roll consumption ready | boolean | letters,logo | backend_readiness | `product_truth.material_consumption.roll_materials[].material_consumption_ready` | backend_readiness | blocked | quote_draft | selected width + layout + split decisions ready | block_quote | missing |

Rules:

- Roll commercial consumption uses selected roll width x length used.
- Usable width is only for fit validation.
- Narrow graphics still consume selected roll width.
- No gang nesting is assumed.
- Area-only is `partial`.

## 10. Pas 2 / Split and Panelization Field Map

Split is only allowed or required when the graphic/part does not fit the selected material format.

| field_id | surface_id | label | field_type | applies_to | owner_system | product_truth_path | source | state | required_for | validation | blocker_behavior | current_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `iv6.s2.material.split.oversized_for_material_format` | IV6-S2-OVERSIZED-MATERIAL-WARNING | Oversized for material format | boolean | letters,logo | backend_readiness | `product_truth.material_consumption.split_plans[].oversized_for_material_format` | nesting_engine | computed | quote_draft | true requires split/alternate/override | block_quote | missing |
| `iv6.s2.material.split.required` | IV6-S2-MATERIAL-SPLIT-PANELIZATION | Split required | boolean | letters,logo | backend_readiness | `product_truth.material_consumption.split_plans[].split_required` | split_plan_generator | split_proposed | quote_draft | true only if full part does not fit | block_quote | missing |
| `iv6.s2.material.split.status` | IV6-S2-MATERIAL-SPLIT-PANELIZATION | Split status | select | letters,logo | operator | `product_truth.material_consumption.split_plans[].split_status` | split_plan_generator | split_proposed | quote_draft | confirmed/rejected/blocked/proposed | block_quote | missing |
| `iv6.s2.material.split.plan_id` | IV6-S2-MATERIAL-SPLIT-PANELIZATION | Split plan id | string | letters,logo | product_truth | `product_truth.material_consumption.split_plans[].split_plan_id` | split_plan_generator | split_proposed | quote_draft | stable id when split required | block_quote | missing |
| `iv6.s2.material.split.panel_count` | IV6-S2-MATERIAL-SPLIT-PANELIZATION | Panel count | number | letters,logo | product_truth | `product_truth.material_consumption.split_plans[].panel_count` | split_plan_generator | split_proposed | quote_draft | `>= 2` when split required | block_quote | missing |
| `iv6.s2.material.split.panel_dimensions` | IV6-S2-MATERIAL-SPLIT-PANELIZATION | Panel dimensions | array | letters,logo | product_truth | `product_truth.material_consumption.split_plans[].panels[]` | split_plan_generator | split_proposed | quote_draft | each panel fits selected format | block_quote | missing |
| `iv6.s2.material.split.overlap_mm` | IV6-S2-MATERIAL-SPLIT-PANELIZATION | Panel overlap | number | letters,logo | product_truth | `product_truth.material_consumption.split_plans[].panels[].overlap_mm` | split_plan_generator | split_proposed | order | `>= 0` | warning | missing |
| `iv6.s2.material.split.seam_notes` | IV6-S2-MATERIAL-SPLIT-PANELIZATION | Seam notes | string | letters,logo | operator | `product_truth.material_consumption.split_plans[].seam_notes` | operator_confirmed | partial | order | required when seam visible/customer impact | warning | missing |
| `iv6.s2.material.split.operator_confirmed` | IV6-S2-MATERIAL-SPLIT-PANELIZATION | Split operator confirmed | boolean | letters,logo | operator | `product_truth.material_consumption.split_plans[].operator_confirmed` | operator_confirmed | confirmed | quote_draft | true when split required | block_quote | missing |
| `iv6.s2.material.split.customer_approval_required` | IV6-S2-MATERIAL-SPLIT-PANELIZATION | Customer approval required | boolean | letters,logo | operator | `product_truth.material_consumption.split_plans[].customer_approval_required` | operator_confirmed | partial | order | must be explicit if seam/customer-visible | block_downstream | missing |

## 11. Pas 2 / Commercial Preview Field Map

Commercial preview can exist, but quote-ready depends on Product Truth and material consumption readiness.

| field_id | surface_id | label | field_type | applies_to | owner_system | product_truth_path | source | state | required_for | validation | blocker_behavior | current_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `iv6.s2.commercial.preview_total` | IV6-S2-LIVE-CALC | Preview total | computed | letters | backend_readiness | `commercial_preview.total` | payload_persisted | partial | preview | must be labeled preview unless quote-ready | warning | partial |
| `iv6.s2.commercial.material_estimate_state` | IV6-S2-LIVE-CALC | Material estimate state | read_only | letters,logo | backend_readiness | `commercial_preview.material_estimate_state` | backend_readiness | partial | preview | area-only/preview/computed visible | warning | missing |
| `iv6.s2.commercial.material_consumption_ready` | IV6-S2-MATERIAL-CONSUMPTION-REALITY | Material consumption ready | boolean | letters,logo | backend_readiness | `commercial_preview.material_consumption_ready` | backend_readiness | blocked | quote_draft | true required for material quote-ready | block_quote | missing |
| `iv6.s2.commercial.markup_percent` | IV6-S2-COMMERCIAL-ADJUSTMENTS | Markup percent | number | letters | operator | `commercial_inputs.markup_percent` | payload_persisted | partial | preview | numeric, bounded by policy | warning | systemic partial |
| `iv6.s2.commercial.discount_percent` | IV6-S2-COMMERCIAL-ADJUSTMENTS | Discount percent | number | letters | operator | `commercial_inputs.discount_percent` | payload_persisted | partial | preview | numeric, bounded by policy | warning | systemic partial |
| `iv6.s2.commercial.quote_ready` | IV6-S2-LIVE-CALC | Quote ready | boolean | all | backend_readiness | `readiness.commercial.quote_ready` | backend_readiness | blocked/confirmed | quote_draft | false if Product Truth/material readiness partial | block_quote | partial |
| `iv6.s2.commercial.guard_reason` | IV6-S2-LIVE-CALC | Commercial guard reason | string | all | backend_readiness | `readiness.commercial.guard_reason` | backend_readiness | blocked | quote_draft | visible if not quote-ready | warning | partial |

## 12. Pas 3 / Confirmare Field Map

Global ready must not hide row-level partial readiness or material consumption partial readiness.

| field_id | surface_id | label | field_type | applies_to | owner_system | product_truth_path | source | state | required_for | validation | blocker_behavior | current_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `iv6.s3.summary.template_code` | IV6-S3-SUMMARY | Template code | string | all | product_system | `summary.template_code` | payload_persisted | confirmed/candidate_read_only | confirmare | current root or candidate displayed | warning | systemic |
| `iv6.s3.gates.product_truth_ready` | IV6-S3-READINESS-GATES | Product Truth ready | boolean | all | backend_readiness | `readiness.product_truth_ready` | backend_readiness | partial | quote_draft | true only when field/row/section readiness ready | block_quote | missing |
| `iv6.s3.gates.material_consumption_ready` | IV6-S3-MATERIAL-CONSUMPTION-SUMMARY | Material consumption ready | boolean | all | backend_readiness | `readiness.material_consumption_ready` | backend_readiness | blocked | quote_draft | false if area-only/split unresolved/roll width missing | block_quote | missing |
| `iv6.s3.gates.commercial_ready` | IV6-S3-COMMERCIAL-SURFACE | Commercial ready | boolean | all | backend_readiness | `readiness.commercial_ready` | backend_readiness | partial | quote_draft | Product Truth + material readiness + pricing coverage | block_quote | partial |
| `iv6.s3.gates.logo_only_not_offerable` | IV6-S3-COMMERCIAL-SURFACE | Logo-only not offerable | boolean | logo | backend_readiness | `readiness.logo_only.not_offerable` | backend_readiness | not_offerable | quote_draft | true blocks commercial root | block_quote | systemic |
| `iv6.s3.handoff.quote_draft_allowed` | IV6-S3-DRAFT-HANDOFF | Quote draft allowed | boolean | all | backend_readiness | `handoff.quote_draft_allowed` | backend_readiness | blocked/confirmed | quote_draft | all gates and operator confirmations required | block_quote | systemic partial |
| `iv6.s3.boundary.no_order` | IV6-S3-NO-ORDER-NO-EXECUTION | No order from Intake V6 | boolean | all | backend_readiness | `downstream.no_order` | backend_readiness | confirmed | order | must remain true in Confirmare | block_downstream | systemic |
| `iv6.s3.boundary.no_execution` | IV6-S3-NO-ORDER-NO-EXECUTION | No execution from Intake V6 | boolean | all | backend_readiness | `downstream.no_execution` | backend_readiness | confirmed | execution | must remain true in Confirmare | block_downstream | systemic |

## 13. Multi-SVG Field Applicability Matrix

| Field group | `gradi-curat.svg` | `litere-vol-1-layer.svg` | `litere-vol-2-layere.svg` | `logo.svg` |
| --- | --- | --- | --- | --- |
| layer roles | yes: 4 face + 2 artwork | yes: 1 face | yes: 2 face | yes: 1 artwork/logo |
| Vector Litere | yes: 4 rows | yes: 1 row | yes: 2 rows | no |
| Vector Atipic / logo | yes: 2 linked logo/artwork rows | no | no | yes: logo-only artwork row |
| logo-only candidate | no | no | no | yes |
| lighting | yes | yes | yes | candidate/guarded only |
| mounting | yes | yes | yes | candidate/guarded only |
| rigid sheet nesting | yes | yes | yes | only if future Logo offerable/material truth exists |
| roll material nesting | yes when Oracal/print/laminate active | yes when Oracal/print/laminate active | yes when Oracal/print/laminate active | candidate only; commercial blocked |
| split/panelization | conditional if oversized | conditional if oversized | conditional if oversized | conditional but not offerable |
| commercial preview | normal Letters preview | normal Letters preview | normal Letters preview | guarded/blocked |
| Confirmare gates | gated | gated | gated | blocked safe |

## 14. Source/State Vocabulary

Sources:

- `svg_analyzer`
- `svg_geometry`
- `svg_nearest_color_mapping`
- `analyzer_semantic_expansion`
- `payload_persisted`
- `payload_hydrated_or_prior_state`
- `operator_confirmed`
- `fallback_default`
- `fallback_area_estimate`
- `backend_readiness`
- `form_system_backbone`
- `material_registry`
- `sheet_format_registry`
- `roll_format_registry`
- `form_system_roll_width_field`
- `nesting_preview`
- `nesting_engine`
- `split_plan_generator`
- `UI_only`

States:

- `suggested`
- `hydrated`
- `fallback`
- `partial`
- `confirmed`
- `blocked`
- `candidate_read_only`
- `not_offerable`
- `estimate_area_only`
- `nesting_preview`
- `computed`
- `split_proposed`
- `split_confirmed`
- `split_rejected`
- `override_required`
- `owner_override_confirmed`

Critical rule:

No field can become Product Truth ready without source, state, owner, Product Truth path, and readiness.

## 15. Readiness Aggregation Rules

Definitions:

- Field readiness: one field is ready only if its validation passes and state is acceptable for its `required_for` level.
- Row readiness: row is ready only if required fields in that row are ready.
- Section readiness: section is ready only if required rows/components are ready or explicitly not applicable.
- Material consumption readiness: ready only if sheet/roll/split rules from `MATERIAL_CONSUMPTION_AND_NESTING_CONTRACT.md` are satisfied.
- Commercial readiness: ready only if Product Truth readiness, material consumption readiness, and commercial/pricing coverage are ready.
- Workspace readiness: route-level summary; must not hide field/row/section partial states.

Rules:

1. Workspace readiness cannot hide row-level partial states.
2. Commercial readiness cannot be true if material consumption readiness is partial for required materials.
3. Logo-only not offerable overrides commercial readiness.
4. Area-only material estimate cannot become quote-ready.
5. Split required but unconfirmed blocks quote readiness.
6. Roll width missing blocks roll material quote readiness.
7. Operator override must be explicit, audited, and downstream-visible.

## 16. Current Status and Gaps

Already systemic:

- SVG upload/analyzer result;
- layer role confirmation;
- workspace readiness status;
- logo-only not-offerable guard;
- Form System Backbone diagnostic;
- letter group finish readiness endpoint;
- linked logo segment readiness endpoint;
- no-order/no-execution guard.

Partial:

- Vector Litere source/state not fully surfaced in the main UI;
- linked logo binding remains suggested;
- material/nesting fields are contract-only, not runtime enforced;
- lighting/mounting/support source/state fields are not fully explicit;
- commercial preview for Letters still needs stronger Product Truth/material readiness boundary;
- Confirmare gates need alignment with row/material readiness.

UI-only / hydrated / fallback:

- Review tab structure;
- many hydrated defaults in finish/lighting/mounting;
- material preview and `Nesting activ`-style surfaces;
- commercial inputs and preview totals before final Product Truth.

Missing:

- runtime material consumption readiness;
- formal split/panelization UI and Product Truth;
- selected roll width as Product Truth field;
- material consumption summary in Confirmare;
- field-level Product Truth snapshot.

## 17. Required Next Slice

Recommended next slice:

```text
PRODUCT_TRUTH_CONFIRMATION_POLICY_V1
```

Reason:

After the field map, the next blocker is policy: how `suggested`, `hydrated`, `fallback`, `partial`, area-only, nesting-preview, and split-proposed fields become confirmed Product Truth.

Do not start direct Pricing implementation yet.