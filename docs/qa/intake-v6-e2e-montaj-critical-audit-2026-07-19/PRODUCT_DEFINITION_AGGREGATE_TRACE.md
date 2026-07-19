# ProductDefinition / Aggregate Trace — Montaj

Endpoints (live):

- `GET /api/v1/product-system/product-definition/TPL-VOLUMETRIC-LETTERS_v2?workspace_id=…`
- `GET /api/v1/product-system/aggregate/TPL-VOLUMETRIC-LETTERS_v2?workspace_id=…`

Artifacts: `runtime/acm_product_definition.json`, `runtime/acm_product_aggregate.json`.

## Field inclusion matrix

| Montaj field | PD | Aggregate | Mark |
|--------------|----|-----------|------|
| mounting_scope | `commercial_mounting_scope` | via composition graph | included |
| mounting_solution ACM | `frozen_mounting_solution` + config | conflicts if scope inactive | included + **stale activation** |
| svg_support_selection | included when confirmed | support type alucobond_cased | included |
| ACM dims/folds/frame | in frozen config / internal_frame | projections | included |
| segmented PROPOSED | `segmented_background_proposal` zero-effects | segmented effects absent | context-only / excluded intentionally from effects |
| segmented CONFIRMED | canonical segmented_background | aggregate projection | (not proven on this WS) |
| electrical nested | with confirmed segmented | with confirmed | excluded when unconfirmed |
| mounting_template_* | weak/task signal | Forex signals | context |
| mains_cable | not in PD keys this WS | process bridge when present | missing here |
| service_corner | may project from selection | **REQUIRED** conflict when absent | missing → Aggregate error |
| mounting_fixing_system | when set | fixing projection | absent this WS |
| Accesorii 5% | notes say PD has no pricing | cost/logical list elsewhere | excluded from PD (intentional) |
| legacy mounting_system | fallback possible | TRIGGER_FIELD_MISMATCH warning for metal trigger | duplicated/legacy |

## Critical PD finding

```
composition.solution_status = blocked
composition.blockers = ["MOUNTING_SCOPE_INACTIVE"]
provenance: prep_active=False scope=none
frozen_mounting_solution.template_code = TPL-ACM-BOXED-MOUNTING-SUPPORT_v1
```

Product ACM truth is **frozen** while composition graph marks solution **blocked** because commercial scope is inactive. Parallel truths.

## Critical Aggregate finding

Conflicts:

1. `COMPOSITION_GRAPH_BLOCKED` (MOUNTING_SCOPE_INACTIVE)
2. `PROCESS_RESOLVER_SERVICE_CORNER_REQUIRED` — Alucobond cased panel requires `power_supply_service_corner`

Warning: `TRIGGER_FIELD_MISMATCH` metal_support_required vs Intake `mounting_system`.
