# ACP Applied Component Interface

**Status:** ACTIVE_CONTRACT · OWNER_GATED_VALUES  
**Interface code:** `ACP-APPLIED-COMPONENT-INTERFACE`  
**Treatment:** `FACE-TREATMENT-APPLIED-VOLUMETRIC-COMPONENT`

## Rule

Volumetric letters/logo remain **separate product components**.  
The interface expresses the host relation to the ACP face — it does **not** absorb letters into the shell.

## Contract fields

- `interface_instance_id`
- `host_component_template_code` → live ACP shell
- `applied_component_template_code` → letters/logo template
- `source_geometry_ids` / binding geometry
- `placement_reference` → `ON_ACP_FACE` (no canvas editor)
- `mounting_method_status`, `cable_passage_status`, `electrical_interface_status` → owner-gated
- `confirmation_status`
- Segmented background context (optional; shell assembly authority):
  - `primary_panel_id`, `secondary_panel_id`
  - `crosses_joint`, `joint_id`
  - `mount_strategy` (`STANDARD` | `TWO_STAGE_JOINT_CROSSING`)
  - `panel_alignment_dependency`, `cable_passage_context`
  - `does_not_absorb_letter_ownership` → always true

See `acm_segmented_background_v1` / `MIXED_ACM_ACP_TECHNICAL_TRUTH_AND_OWNERSHIP.md` §11.

## Electrical note

Letters keep a separate electrical path when sold as illuminated volumes.  
ACP shell cavity electrical is for shell-local modules (routed/insert), composed via shell-common electrical configuration.
