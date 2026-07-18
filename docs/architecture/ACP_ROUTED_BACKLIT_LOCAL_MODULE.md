# ACP Routed Backlit Cutout — Local Module

**Status:** ACTIVE_CONTRACT · OWNER_GATED_VALUES  
**Module code:** `ACP-LOCAL-MODULE-ROUTED-BACKLIT`  
**Host:** `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1`  
**Treatment:** `FACE-TREATMENT-ROUTED-BACKLIT-CUTOUT`  
**Geometry roles:** `CUTOUT_TEXT`, `CUTOUT_LOGO`

## Ownership

Component-owned on the ACP shell. Product Template composes; shell holds local truth.  
Not absorbed into Product Template. Not legacy `TPL-ACP-LIGHT-ROUTED` authority.

## Persisted shape (FinishSetup → binding.local_module_configuration)

- `module_instance_id`, `face_treatment_code`, `geometry_role`, `binding_id`
- `backing_material` — material_code / thickness_mm / optical_type → **OWNER_GATE_REQUIRED**
- `backing_mounting` — method / overlap → **OWNER_GATE_REQUIRED** / **MANUAL_CONFIRMATION_REQUIRED**
- `illumination_intent` — enabled + lighting_mode; LED/PSU/wiring statuses gated
- `service.access_status` — gated
- `readiness` — material/geometry/mounting/illumination/electrical/overall

## Authority findings

| Concern | Classification |
|---------|----------------|
| Plexiglas thickness / optical type | OWNER_GATE_REQUIRED (no optical RO catalog) |
| Overlap / adhesion method | OWNER_GATE_REQUIRED |
| LED density / PSU / wiring | OWNER_GATE_REQUIRED (shell electrical module) |
| Legacy LIGHT-ROUTED diffuser fields | LEGACY_REFERENCE only |

## Aggregate

Projects identity, illumination intent, readiness, guarded process intents.  
**No quantities. No BOM. No CPP.**
