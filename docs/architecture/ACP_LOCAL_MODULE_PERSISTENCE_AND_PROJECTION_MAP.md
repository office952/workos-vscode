# ACP Local Modules — Persistence & Projection Map

## Path

```text
Product System contracts (acp_local_face_modules_v1)
  → FinishSetup.svg_component_bindings[].local_module_configuration
  → FinishSetup.acp_electrical_configuration
  → ProductDefinition.canonical_values
       · acp_local_face_module_instances
       · acp_electrical_configuration
       · acp_local_face_modules_aggregate_projection
  → ProductAggregate (guarded projection only)
```

No parallel storage. No schema/migration. JSON fields on finish_setup.

## Stable identity

| Identity | Source |
|----------|--------|
| `binding_id` | FinishSetup binding |
| `local_zone_id` | Stable hash of role+geometry |
| `module_instance_id` | Stable hash of module_code+binding_id |

## Inactive isolation

`status=INACTIVE` → zero warnings, materials, process quantities, Aggregate module rows, CPP/task effects.

## Capabilities on live ACM shell

`boxed_acp_shell`, `local_face_treatments`, `routed_backlit_cutout_module`, `acrylic_insert_module`, `applied_component_host`, `illumination_host`
