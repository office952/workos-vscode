# Shared Volumetric Component Contract Decision Packet

## 1. Status

`PROPOSED_OWNER_DECISION_PACKET`

## 2. Purpose

This packet proposes a shared component contract direction for the volumetric Product System family, starting with:

- `TPL-VOLUMETRIC-LETTERS_v2`
- `TPL-VOLUMETRIC-LOGO_v1`

The goal is to avoid duplicating technical logic when Letters and Logo use the same production concept, while still preserving real template differences through profiles and template-specific configuration.

This is not an implementation document. It does not change runtime links, pricing, ProductDefinition, ProductAggregate, Work Intake, seeds, or database state.

The decision principle is:

```txt
Use one shared component contract when the technical execution is the same.
Use template_config when only labels, defaults, allowed variants, or required questions differ.
Use profile when the behavior is the same family but technically different.
Use NOT_CONFIRMED when evidence is missing.
```

## 3. Current Verified State

Verified current state:

- `TPL-VOLUMETRIC-LETTERS_v2` is an `offerable_product`.
- `TPL-VOLUMETRIC-LOGO_v1` is a `candidate_product`.
- Letters remains visible to Work Intake because it is `quote_offerable=true`.
- Logo must not be activated in Work Intake in this decision packet.
- Work Intake remains based on `quote_offerable=true`.
- Letters has operational mini-module contracts in `backend/data/mini_module_registry_volumetric_v2.py`.
- Logo has dedicated `comp_logo_*` components and `logo_*` operations seeded by `backend/seeds/seed_tpl_volumetric_logo_v1.py`.
- Logo live child template links point to dedicated Logo templates, not to Letters child templates.
- `electrica_logo` exists only as `FUTURE_RESERVED_STEP_6`; it is not active and has no ProductDefinition, aggregate, cost, quote, order, or task outputs.

Current Letters modules:

| Role | Template/module evidence | Operational status |
| --- | --- | --- |
| Face | `debitare_fata`, `comp_face_litere`, `TPL-VOLUMETRIC-FACE_v1` | ACTIVE_OPERATIONAL |
| Back | `debitare_spate`, `comp_spate_litere`, `TPL-VOLUMETRIC-BACK_v1` | ACTIVE_OPERATIONAL |
| Return / side | `modelare_cant`, `comp_lateral_litere`, `TPL-VOLUM-ALUMINIU_v1` | ACTIVE_OPERATIONAL |
| Lighting | `sistem_led`, `comp_led_litere`, `TPL-VOLUMETRIC-LED_v1` | ACTIVE_OPERATIONAL |
| Finish | `finisaje`, `comp_finisaj_litere`, `TPL-VOLUMETRIC-FINISH_v1` | ACTIVE_OPERATIONAL |
| Mounting/support | `structura_suport`, `TPL-METAL-PREMOUNT-STRUCTURE_v1` | ACTIVE_OPERATIONAL optional addon |

Current Logo modules:

| Role | Template/module evidence | Current status |
| --- | --- | --- |
| Face | `comp_logo_face`, `TPL-VOLUMETRIC-LOGO-FACE_v1`, `logo_face_*` operations | Dedicated Logo contract |
| Back | `comp_logo_back`, `TPL-VOLUMETRIC-LOGO-BACK_v1`, `logo_back_cut` | Dedicated Logo contract |
| Return / side | `comp_logo_return`, `TPL-VOLUMETRIC-LOGO-RETURN_v1`, `logo_return_*` operations | Dedicated Logo contract |
| Lighting | `comp_logo_lighting`, `TPL-VOLUMETRIC-LOGO-LIGHTING_v1`, `logo_led_install`, `logo_electrical_test` | Dedicated Logo contract |
| Finish | `comp_logo_finish`, `TPL-VOLUMETRIC-LOGO-FINISH_v1`, `logo_finish_application` | Dedicated Logo contract |
| Mounting | `comp_logo_mounting`, `TPL-VOLUMETRIC-LOGO-MOUNTING_v1`, `logo_mounting_*` operations | Dedicated Logo contract |

## 4. Core Decision

Proposed decision:

```txt
Use shared volumetric component contracts with template-specific profiles/configs.
Do not replace Logo child templates directly with Letters child templates.
Do not duplicate identical technical logic long-term.
```

This means:

- Shared component contracts become the long-term semantic source.
- Template profiles describe real technical differences between Letters and Logo.
- Template config carries labels, defaults, allowed variants, required questions, and mapping names.
- Existing Logo child templates remain in place until a future owner-approved migration proves the shared contract can preserve Product Truth.
- No Product System UI should invent missing fields, formulas, totals, status, or commercial flow.

## 5. Shared Component Model

| Shared component | Letters profile | Logo profile | Shared truth | Template-specific config | Confidence | Owner decision |
| --- | --- | --- | --- | --- | --- | --- |
| `volumetric_face` | `letters`: face panel / plexi/acrylic, `comp_face_litere`, `face_cnc_cut`, optional vinyl | `logo`: logo face, `comp_logo_face`, `logo_face_cnc_cut`, print/laminate path | component role, area basis, face material role, operation family | display label, area key, material defaults, artwork/print variants | MEDIUM | `APPROVE_AS_DIRECTION` |
| `volumetric_back` | `letters`: back panel, `comp_spate_litere`, `back_cut` | `logo`: logo back, `comp_logo_back`, `logo_back_cut` | component role, area basis, back material role, cut operation family | display label, material defaults, backing variants | MEDIUM | `APPROVE_AS_DIRECTION` |
| `volumetric_return_side` | `letters`: side wall / return profile, `modelare_cant`, letter perimeter | `logo`: logo return, `logo_return_forming`, logo perimeter | component role, perimeter basis, return depth, forming/bonding family | profile material, perimeter key, finish variants, operation aliases | MEDIUM | `APPROVE_AS_DIRECTION` |
| `volumetric_lighting` | `letters`: `sistem_led`, `comp_led_litere`, LED + PSU, `lighting_system_type` | `logo`: `comp_logo_lighting`, LED + PSU, `logo_lighting_mode` / `emblem_led_module_count` | LED material role, PSU material role, module count if confirmed/derived, selected PSU if confirmed/derived | lighting profile, field names, operation names, activation gate | PARTIAL | `NEEDS_MORE_AUDIT` |
| `volumetric_surface_finish` | `letters`: RAL/vinyl/sablon/packaging/QC via `finisaje` | `logo`: print/laminate/application via `logo_finish_application` | finish target, finish material role, area basis when applicable | print vs paint, laminate, sablon, packaging, required questions | LOW | `KEEP_SEPARATE_NOW` |
| `volumetric_mounting_interface` | `letters`: optional premount/support bars, `structura_suport`, `metal_support_required` | `logo`: mounting kit/template/install, `logo_mounting_*`, `logo_fasteners` | mounting/support requirement, mounting template requirement, support material role if present | premount vs kit/install, trigger field, default activation | LOW | `KEEP_SEPARATE_NOW` |

## 6. Component Profiles

### `volumetric_face`

`profile: letters`

- Current evidence: `debitare_fata`, `comp_face_litere`, `TPL-VOLUMETRIC-FACE_v1`.
- Technical role: face panel / front visual component.
- Geometry basis: `letter_face_area_m2` is confirmed in the Letters registry.
- Operations: `face_cnc_cut`, `vinyl_application`.
- Product Truth output should include face component role, area basis, selected material role, finish target, and source.

`profile: logo`

- Current evidence: `comp_logo_face`, `TPL-VOLUMETRIC-LOGO-FACE_v1`.
- Technical role: logo face / print surface.
- Geometry basis: `svg_area_m2` / `logo_area` is confirmed in the Logo seed.
- Operations: `logo_face_cnc_cut`, `logo_face_print`, `logo_face_laminate`.
- Product Truth output should include face component role, logo area basis, material role, artwork mode, and source.

### `volumetric_back`

`profile: letters`

- Current evidence: `debitare_spate`, `comp_spate_litere`, `TPL-VOLUMETRIC-BACK_v1`.
- Technical role: back panel / backing.
- Confirmed fields: `backing_mode`, `backing_thickness_mm`, `back_bevel_enabled`.
- Operation: `back_cut`.

`profile: logo`

- Current evidence: `comp_logo_back`, `TPL-VOLUMETRIC-LOGO-BACK_v1`.
- Technical role: logo back / closing panel.
- Confirmed mapping: `svg_area_m2`, `logo_backing_material`.
- Operation: `logo_back_cut`.

### `volumetric_return_side`

`profile: letters`

- Current evidence: `modelare_cant`, `comp_lateral_litere`, `TPL-VOLUM-ALUMINIU_v1`.
- Technical role: side wall / return profile / lateral cant.
- Confirmed fields: `return_depth_mm`, `return_finish_type`, `return_oracal_code`, `letter_perimeter_m`, `return_material_perimeter_ml`.
- Confirmed variants: depth gate 30/60/80/100 mm and finish gate RAL vs Oracal.

`profile: logo`

- Current evidence: `comp_logo_return`, `TPL-VOLUMETRIC-LOGO-RETURN_v1`.
- Technical role: logo return / side wall.
- Confirmed mappings: `svg_perimeter_ml`, `return_depth_mm`, `return_finish_type`.
- Operations: `logo_return_forming`, `logo_return_bonding`.
- Product Truth should preserve the logo perimeter basis; it must not silently reuse letter perimeter semantics.

### `volumetric_lighting`

`profile: letters`

- Current evidence: `sistem_led`, `comp_led_litere`, `TPL-VOLUMETRIC-LED_v1`.
- Confirmed fields: `lighting_system_type`, `led_module_count`, `selected_psu_watts`, `psu_configuration`.
- Confirmed materials: `MAT-LED-MODULE`, `MAT-LED-PSU-12V`.
- Confirmed operations: `led_install_letters`, `electrical_letters`.

`profile: logo`

- Current evidence: `comp_logo_lighting`, `TPL-VOLUMETRIC-LOGO-LIGHTING_v1`.
- Confirmed fields: `logo_lighting_mode`, `emblem_led_module_count`, `selected_psu_watts`.
- Confirmed materials: `MAT-LED-MODULE`, `MAT-LED-PSU-12V`.
- Confirmed operations: `logo_led_install`, `logo_electrical_test`.
- `electrica_logo` remains `FUTURE_RESERVED_STEP_6`, not active.

### `volumetric_surface_finish`

`profile: letters`

- Current evidence: `finisaje`, `comp_finisaj_litere`, `TPL-VOLUMETRIC-FINISH_v1`.
- Includes finish, mounting template, painting, packaging, and QC responsibilities.
- Confirmed fields include `mounting_template_enabled`, `mounting_template_area_m2`, `letter_group_finishes`, `paint_ral_code`.

`profile: logo`

- Current evidence: `comp_logo_finish`, `TPL-VOLUMETRIC-LOGO-FINISH_v1`.
- Focuses on print/lamination/application.
- Confirmed mappings include `logo_artwork_mode`, `svg_area_m2`.
- This profile should remain separate until owner confirms how logo print/lamination relates to Letters finish logic.

### `volumetric_mounting_interface`

`profile: letters`

- Current evidence: `structura_suport`, `TPL-METAL-PREMOUNT-STRUCTURE_v1`.
- Technical role: optional premount/support bars.
- Trigger: `metal_support_required` with known mismatch risk against `mounting_system`.

`profile: logo`

- Current evidence: `comp_logo_mounting`, `TPL-VOLUMETRIC-LOGO-MOUNTING_v1`.
- Technical role: mounting template/install kit.
- Confirmed mappings: `mounting_system`, `mounting_template_enabled`.
- Operations: `logo_mounting_template_cut`, `logo_mounting_install`.

## 7. Product Truth Outputs

Common conceptual Product Truth outputs should be defined before runtime refactor. These are contract categories, not new UI fields or pricing formulas.

| Output | Meaning | Current status |
| --- | --- | --- |
| `component_role` | The semantic role: face, back, return_side, lighting, surface_finish, mounting | CONFIRMED conceptually |
| `material_role` | Material role selected or derived for the component | CONFIRMED in current template-specific data |
| `geometry_basis` | Area, perimeter, count, or mixed basis for the component | CONFIRMED conceptually; exact key is template-specific |
| `area` | Area used for face/back/finish where applicable | CONFIRMED for logo via `svg_area_m2`; Letters has `letter_face_area_m2` |
| `perimeter` | Perimeter used for return/side | CONFIRMED with different keys for Letters and Logo |
| `count` | Count basis for LED modules or discrete items | CONFIRMED for LED module count fields; derivation policy NOT_CONFIRMED |
| `lighting_mode` | Lighting activation/profile | PARTIAL; exact front-lit/halo/combined variants NOT_CONFIRMED |
| `led_module_count` | LED module count if confirmed or derived | CONFIRMED field exists; derivation rules NOT_CONFIRMED here |
| `psu_selection` | Selected PSU if confirmed or derived | CONFIRMED field exists; selection rules NOT_CONFIRMED here |
| `finish_target` | Face, return, back, artwork, sablon, or final finish target | PARTIAL; template-specific today |
| `mounting_support_requirement` | Whether support/mounting is needed | PARTIAL; Letters and Logo use different semantics |
| `source` | `confirmed`, `suggested`, `fallback`, or `manual` provenance | REQUIRED direction; not fully confirmed in current contracts |

Rules:

- If SVG Analyzer suggests a value, Product Truth must record it as suggested, not final.
- If operator confirms a value, Product Truth can mark it confirmed.
- If a value is defaulted, Product Truth must preserve the default source.
- ProductDefinition must consume Product Truth; it must not guess missing truth.
- Pricing Registry must receive complete Product Truth plus config; it must not repair missing Product Truth.

## 8. Template-Specific Config

Definitions:

| Concept | Meaning |
| --- | --- |
| Shared component contract | Stable semantic contract for a reusable production component family. Example: `volumetric_face`. |
| Template profile | Technical behavior flavor under a shared contract. Example: `letters` vs `logo`. |
| Template config | Template-specific labels, defaults, allowed variants, required questions, and field mappings. |
| Display label | UI text only. Example: `Fata litera` vs `Fata logo`. Label differences do not require separate technical components. |
| Defaults | Initial values or fallback choices; must be marked as defaults in Product Truth if used. |
| Allowed variants | Explicit options allowed for a profile/template. Example: return depth or logo artwork mode. |
| Required questions | Operator inputs needed to produce complete Product Truth. |
| Product Truth output | Confirmed/suggested/defaulted structured output consumed downstream. |
| Pricing Registry config | Pricing-side configuration that consumes Product Truth; it must not create missing truth. |

A UI may show different labels for Letters and Logo, but it must not invent fields, commercial formulas, totals, status, or flow behavior. Display labels are presentation. Product Truth is the handoff contract.

## 9. Lighting / Electrical Decision

Starting audit conclusion:

```txt
lighting_can_be_shared = PARTIAL
```

Common evidence:

- Both Letters and Logo use `MAT-LED-MODULE`.
- Both Letters and Logo use `MAT-LED-PSU-12V`.
- Both have an LED module count concept.
- Both have selected PSU concepts.
- Both require electrical work or test operations.

Different evidence:

- Letters uses `lighting_system_type`, `led_module_count`, `psu_configuration`, `led_install_letters`, `electrical_letters`.
- Logo uses `logo_lighting_mode`, `emblem_led_module_count`, `logo_led_install`, `logo_electrical_test`.
- `electrica_logo` is future/reserved and must not activate now.

| Topic | Letters | Logo | Shared? | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| LED material role | `MAT-LED-MODULE` | `MAT-LED-MODULE` | YES | CONFIRMED | Same material role appears in both contracts. |
| PSU material role | `MAT-LED-PSU-12V` | `MAT-LED-PSU-12V` | YES | CONFIRMED | Same PSU material role appears in both contracts. |
| LED module count | `led_module_count` | `emblem_led_module_count` | PARTIAL | CONFIRMED fields, not unified | Shared truth can expose count, with profile-specific source keys. |
| Selected PSU | `selected_psu_watts`, `psu_configuration` | `selected_psu_watts` | PARTIAL | CONFIRMED fields, not unified | PSU configuration depth differs. |
| Front-lit / halo / combined | `lighting_system_type` may imply mode | `logo_lighting_mode` has `area_lit` / `excluded` in seed | PARTIAL | NOT_CONFIRMED | Exact variants need owner/product truth decision. |
| Lighting zones | Not confirmed | Not confirmed | UNKNOWN | NOT_CONFIRMED | Do not invent zone model in UI. |
| Logo irregular shape | Not confirmed by shared contract | Logo uses area/perimeter/artwork semantics | PARTIAL | NOT_CONFIRMED | Shape impact likely exists but is not fully specified. |
| Circuits | Not confirmed | Not confirmed | UNKNOWN | NOT_CONFIRMED | Must remain Product Truth/electrical profile decision. |
| Electrical test | `electrical_letters` | `logo_electrical_test` | PARTIAL | CONFIRMED separate ops | Shared category, profile-specific operation names. |
| Access/service | Not confirmed | Not confirmed | UNKNOWN | NOT_CONFIRMED | Needs owner/electrical audit. |
| Product Truth source | Must be confirmed/suggested/default/manual | Must be confirmed/suggested/default/manual | YES | REQUIRED DIRECTION | ProductDefinition consumes this, not raw UI guesses. |
| Pricing Registry dependency | Consumes complete Product Truth/config | Consumes complete Product Truth/config | YES | REQUIRED DIRECTION | Pricing must not repair missing lighting truth. |

Decision proposal:

- Approve `volumetric_lighting` as the target shared component direction.
- Keep `letters` and `logo` as separate profiles.
- Do not activate `electrica_logo` now.
- Do not replace Logo lighting template with Letters LED template now.
- Require owner confirmation for front-lit/halo/combined, zones, circuits, service access, and derivation rules.

## 10. What Must NOT Happen

- No direct swap Logo modules -> Letters modules.
- No Logo offerable activation.
- No Work Intake exposure for Logo.
- No Pricing Registry repair of missing Product Truth.
- No UI-invented fields.
- No UI-invented commercial formulas, totals, statuses, or flow steps.
- No ProductDefinition guessing.
- No ProductAggregate implementation now.
- No Task Graph now.
- No ExecutionPlan now.
- No Employee Mobile now.
- No hourly commercial pricing.
- No CostEngine changes.
- No seed or migration for this decision.

## 11. Future Implementation Slices

Single recommended direction:

1. Owner approves this decision packet.
2. Define shared component contract schema/design in docs first.
3. Align Product Truth outputs for face, back, return_side, lighting, surface_finish, and mounting_interface.
4. Add backend registry read-only exposure for shared component contracts.
5. Add Product System UI read-only display of shared components/profiles.
6. Add tests for shared contract display and no Work Intake exposure regression.
7. Only later: migrate Logo module profiles behind the shared contract, without swapping live links blindly.
8. Only after owner GO: run a separate Logo offerability audit.

No automatic push or commit is part of this packet.

## 12. Acceptance Criteria

The decision is accepted when owner agrees that:

- Letters remains `offerable_product`.
- Logo remains `candidate_product`.
- Work Intake does not expose Logo.
- Shared components are contracts/profiles first, not runtime link swaps.
- Product Truth remains the source for ProductDefinition.
- ProductDefinition consumes Product Truth and does not infer missing truth.
- Pricing is not modified by this decision.
- CostEngine is not modified by this decision.
- ProductAggregate, Task Graph, and ExecutionPlan remain out of scope.
- Employee Mobile remains final-final.

## 13. Open Questions For Owner

1. Should Logo use the same face logic family as Letters, but with `logo_area`, print, and laminate profile differences?
2. Should Logo lighting be a separate profile inside the same `volumetric_lighting` component?
3. What real Logo lighting differences exist: zones, halo, front-lit, diffusion, irregular shape handling, circuits, PSU grouping, or service access?
4. Which Logo finish behaviors must remain separate from Letters finish: print media, laminate media, artwork mode, packaging, QC, or mounting template?
5. Is Logo mounting a mounting kit/template/install flow, a premount support structure, or both under different variants?
6. Should return/side logic share depth and finish gates with Letters, or does Logo require different allowed variants?
7. Which fields must be operator-confirmed versus derived from SVG Analyzer suggestions?
8. What Product Truth provenance states are required before ProductDefinition can consume the shared contract?

## 14. Roadmap Alignment

This packet sits:

- after Product System catalog organization;
- after the Letters vs Logo similarity audit;
- before shared component runtime refactor;
- before Product Truth runtime alignment;
- before ProductDefinition changes;
- before Pricing Registry or CostEngine work;
- long before ProductAggregate / Task Graph / ExecutionPlan;
- long before Employee Mobile.

The immediate value is architectural restraint: define the shared contract before touching runtime links, pricing, ProductDefinition, or operator flows.
