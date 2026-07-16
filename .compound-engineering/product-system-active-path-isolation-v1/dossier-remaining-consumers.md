# Dossier Remaining Consumers Audit

## Controlled (authority redirected)

| Consumer | Surface | Classification | Change |
|----------|---------|----------------|--------|
| `product_aggregate_service.build` | aggregate | was behavior-bearing | canonical parent components + form keys |
| `intake_v4_template_option_contract_service` | intake V4 | was behavior-bearing | `_resolve_template_variants` canonical |
| `intake_v6_template_option_contract_service` | intake V6 | was behavior-bearing | canonical variants |
| `intake_v5_service.get_template_config` | intake V5 | was behavior-bearing | canonical variants + form keys |
| `output_blocks_renderer_service` | output blocks | was behavior-bearing (v2) | canonical blocks for v2 |
| `product_readiness_service.evaluate` | readiness | was behavior-bearing (v2) | template BOM + canonical blocks |
| `product_system_template_readiness_service._derive_execution` | readiness | was behavior-bearing | template operations, not dossier task_rules |

## Still gated legacy (non-v2)

| Consumer | Classification |
|----------|----------------|
| `output_blocks_renderer_service` (non-v2) | legacy_bridge — approved dossier only |
| `quote_output_composition_service` | delegates to renderer |

## Metadata / audit only

| Consumer | Classification |
|----------|----------------|
| `output_blocks_coverage_service` | audit-only |
| Dossier CRUD routers | inspection / admin |

## Post-freeze forbidden

Snapshot-time dossier reads remain unchanged (out of scope).
