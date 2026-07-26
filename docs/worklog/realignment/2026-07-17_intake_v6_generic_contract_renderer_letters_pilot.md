# Worklog — Intake V6 Generic Contract Renderer (Letters pilot)

**Date:** 2026-07-17  
**Build:** `INTAKE_V6_GENERIC_CONTRACT_RENDERER_LETTERS_PILOT`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Baseline HEAD:** `6a2252a`

---

## Owner decision

```text
APPROVED = INTAKE_V6_GENERIC_CONTRACT_RENDERER_LETTERS_PILOT
Letters = first proven product contract
Intake = generic renderer (not Letters-only system)
No Pricing Registry 7I
```

---

## Authority matrix (editable Letters Review — pilot scope)

| Section | Field | Current React owner | PS binding | Workspace path | Type | Options | Required | Visibility | Save path | Proposed mode |
|---|---|---|---|---|---|---|---|---|---|---|
| Finisaje | face_finish_type | LetterGroupsSection | yes | finish_setup.face_finish_type (+ letter groups) | select | local/API | yes | sold scope | syncFormFromLayerFinishes | EXISTING_SPECIALIZED_COMPONENT_ADAPTED |
| Finisaje | return_finish_type | ReturnCantFields | yes | finish_setup.return_finish_type | select | local | yes | always | sync | EXISTING_SPECIALIZED_COMPONENT_ADAPTED |
| Finisaje | return_depth_mm | ReturnCantFields | yes | finish_setup.return_depth_mm | number | API depths | yes | always | sync | EXISTING_SPECIALIZED_COMPONENT_ADAPTED |
| Finisaje | backing_mode | BackingFinishRow | yes | finish_setup.backing_mode | select | local | yes | always | sync | EXISTING_SPECIALIZED_COMPONENT_ADAPTED |
| Finisaje | back_bevel_enabled | encoded in backing | yes | finish_setup.back_bevel_enabled | boolean | — | no | backing rule | derived | DERIVED_READ_ONLY |
| Finisaje | letter_group_finishes | LetterGroups layout | yes | finish_setup.letter_group_finishes | complex | — | — | — | sync | KEEP_FRONTEND_TEMPORARILY (layout) |
| Iluminare | lighting_system_type | LightingSection | yes | finish_setup.lighting_system_type | select | API | no | illuminated | updateForm | GENERIC_RENDERER_NOW |
| Iluminare | selected_psu_watts | LightingSection | yes | finish_setup.selected_psu_watts | select | API | no | LED | updateForm | GENERIC_RENDERER_NOW |
| Iluminare | led_module_count | display | yes | finish_setup.led_module_count | number | derived | no | — | syncLighting | ANALYZER_OWNED / DERIVED_READ_ONLY |
| Iluminare | illuminated, light_color, power | LightingSection | no/partial | finish_setup.* | mixed | local/API | — | — | updateForm | KEEP_FRONTEND_TEMPORARILY |
| Montaj | mounting_template_enabled | ReviewStep inline | yes | finish_setup.mounting_template_enabled | boolean | — | no | prep | updateForm | GENERIC_RENDERER_NOW |
| Montaj | mounting_template_area_m2 | ReviewStep inline | yes | finish_setup.mounting_template_area_m2 | number | — | no | template on | updateForm | GENERIC_RENDERER_NOW |
| Montaj | mounting_system | legacy read-only | yes | finish_setup.mounting_system | select | API | yes | — | derived from solution | DERIVED_READ_ONLY |
| Montaj | mounting_scope / solution | ReviewStep inline | no | finish_setup.* | select | local | — | — | updateForm | KEEP_FRONTEND_TEMPORARILY |
| Geometry | width/height/perimeter/count | Analyzer / metrics | yes | client/quote_geometry | — | — | — | — | analyzer | ANALYZER_OWNED |

### Pilot selection

**GENERIC_RENDERER_NOW:** `lighting_system_type`, `selected_psu_watts`, `mounting_template_enabled`, `mounting_template_area_m2`  
**EXISTING_SPECIALIZED_COMPONENT_ADAPTED:** face/return/backing controls consume generic field primitives + contract options/labels/required  
**KEEP_FRONTEND_TEMPORARILY:** letter-group layout shell, lighting derived UI, mounting_scope/solution  
**ANALYZER_OWNED:** geometry / LED counts

---

## Implementation notes

### Generic architecture

- Backend: `render_sections`, `writable_workspace_paths`, structured `options` / `visibility`
- Frontend: `IntakeContractSectionRenderer` + `IntakeContractFieldRenderer` (no Letters field keys in generic code)
- Gate: `isContractRendererEnabled(templateCode)` only
- Workspace writes: allowlisted `setByWorkspacePath` → existing `updateForm`

### Pilot activation

| Section | Mode |
|---------|------|
| iluminare | GENERIC — lighting_system_type, selected_psu_watts |
| montaj_template | GENERIC — mounting_template_enabled, area |
| finisaje_fields | GENERIC when no letter groups; letter-group layout KEEP_FRONTEND + contract labels |

### Authority scope

`runtime_authority=false`  
`runtime_authority_scope=selected_sections:finisaje_fields,iluminare,montaj_template`

### Remaining frontend-owned

- Letter group card layout
- Lighting derived UI (illuminated toggle, density, emblem)
- Mounting scope / solution / material
- SVG Analyzer geometry

### Master status

```text
INTAKE_V6_GENERIC_CONTRACT_RENDERER = PILOT PROVEN
LETTERS CONTRACT-DRIVEN SECTIONS = COMPLETE FOR APPROVED PILOT
LETTERS FULL FORM = PARTIAL
OTHER PRODUCT TEMPLATES = PARTIAL / NOT PROVEN
```
